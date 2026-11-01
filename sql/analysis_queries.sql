-- ============================================================================
-- YottaFlex Industrial Energy Analytics Platform - Analytical SQL Queries
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Query 1: Which machines consume the most energy?
-- Aggregates total kWh, total cost, average operating power, and % of facility total
-- ----------------------------------------------------------------------------
-- QUERY_1_START
WITH facility_total AS (
    SELECT SUM(r.energy_consumed_kwh) AS plant_total_kwh
    FROM energy_readings r
    JOIN meters m ON r.meter_id = m.meter_id
    WHERE m.meter_type = 'MAIN_INCOMER' AND r.is_anomaly = 0
)
SELECT 
    m.machine_id,
    m.name AS machine_name,
    m.category,
    m.rated_power_kw,
    ROUND(SUM(r.energy_consumed_kwh), 2) AS total_energy_kwh,
    ROUND(SUM(r.cost_usd), 2) AS total_cost_usd,
    ROUND(AVG(r.power_demand_kw), 2) AS avg_power_kw,
    ROUND(MAX(r.power_demand_kw), 2) AS peak_power_kw,
    ROUND(100.0 * SUM(r.energy_consumed_kwh) / f.plant_total_kwh, 2) AS pct_of_total_consumption
FROM machines m
JOIN energy_readings r ON m.machine_id = r.machine_id
CROSS JOIN facility_total f
WHERE r.is_anomaly = 0
GROUP BY m.machine_id, m.name, m.category, m.rated_power_kw, f.plant_total_kwh
ORDER BY total_energy_kwh DESC;
-- QUERY_1_END


-- ----------------------------------------------------------------------------
-- Query 2: Which machines have the highest idle consumption?
-- Aggregates confirmed idle duration, wasted kWh, wasted cost, and idle waste ratio
-- ----------------------------------------------------------------------------
-- QUERY_2_START
WITH machine_total_energy AS (
    SELECT machine_id, SUM(energy_consumed_kwh) AS total_kwh
    FROM energy_readings
    WHERE machine_id IS NOT NULL AND is_anomaly = 0
    GROUP BY machine_id
)
SELECT 
    m.machine_id,
    m.name AS machine_name,
    m.category,
    COUNT(i.idle_id) AS idle_event_count,
    ROUND(SUM(i.duration_minutes) / 60.0, 1) AS total_idle_hours,
    ROUND(SUM(i.energy_wasted_kwh), 2) AS total_idle_wasted_kwh,
    ROUND(SUM(i.cost_wasted_usd), 2) AS total_idle_cost_usd,
    ROUND(100.0 * SUM(i.energy_wasted_kwh) / NULLIF(mte.total_kwh, 0), 2) AS idle_energy_pct
FROM machines m
LEFT JOIN machine_idle_periods i ON m.machine_id = i.machine_id
LEFT JOIN machine_total_energy mte ON m.machine_id = mte.machine_id
GROUP BY m.machine_id, m.name, m.category, mte.total_kwh
ORDER BY total_idle_wasted_kwh DESC;
-- QUERY_2_END


-- ----------------------------------------------------------------------------
-- Query 3: What are the daily energy consumption trends?
-- Daily total kWh, peak kW, cost, weekday vs weekend classification at Main Incomer
-- ----------------------------------------------------------------------------
-- QUERY_3_START
SELECT 
    DATE(r.timestamp) AS reading_date,
    CASE strftime('%w', r.timestamp)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        ELSE 'Saturday'
    END AS day_of_week,
    ROUND(SUM(r.energy_consumed_kwh), 2) AS daily_total_kwh,
    ROUND(MAX(r.power_demand_kw), 2) AS daily_peak_demand_kw,
    ROUND(AVG(r.power_demand_kw), 2) AS daily_avg_power_kw,
    ROUND(SUM(r.cost_usd), 2) AS daily_total_cost_usd,
    ROUND(SUM(r.cost_usd) / NULLIF(SUM(r.energy_consumed_kwh), 0), 4) AS avg_cost_per_kwh
FROM energy_readings r
JOIN meters m ON r.meter_id = m.meter_id
WHERE r.is_anomaly = 0 AND m.meter_type = 'MAIN_INCOMER'
GROUP BY DATE(r.timestamp), strftime('%w', r.timestamp)
ORDER BY reading_date ASC;
-- QUERY_3_END


-- ----------------------------------------------------------------------------
-- Query 4: What are the peak demand periods?
-- Top 20 15-minute intervals with the highest instantaneous demand across the facility
-- ----------------------------------------------------------------------------
-- QUERY_4_START
WITH interval_meter_aggregates AS (
    SELECT 
        r.timestamp,
        r.tariff_id,
        MAX(CASE WHEN m.meter_type = 'MAIN_INCOMER' THEN r.power_demand_kw ELSE 0 END) AS plant_total_demand_kw,
        MAX(CASE WHEN m.meter_type = 'MAIN_INCOMER' THEN r.energy_consumed_kwh ELSE 0 END) AS plant_interval_kwh,
        MAX(CASE WHEN m.meter_type = 'MAIN_INCOMER' THEN r.cost_usd ELSE 0 END) AS interval_cost_usd,
        COUNT(DISTINCT CASE WHEN r.power_demand_kw > 0 THEN r.meter_id END) AS active_meter_count,
        SUM(CASE WHEN m.meter_type = 'SUB_FEEDER' THEN r.power_demand_kw ELSE 0 END) AS feeder_aggregate_demand_kw,
        SUM(CASE WHEN m.meter_type = 'MACHINE_POINT' THEN r.power_demand_kw ELSE 0 END) AS machine_submeters_demand_kw
    FROM energy_readings r
    JOIN meters m ON r.meter_id = m.meter_id
    WHERE r.is_anomaly = 0
    GROUP BY r.timestamp, r.tariff_id
)
SELECT 
    ima.timestamp,
    t.period_type AS tariff_tier,
    t.rate_per_kwh_usd,
    ROUND(ima.plant_total_demand_kw, 2) AS plant_total_demand_kw,
    ROUND(ima.plant_interval_kwh, 2) AS plant_interval_kwh,
    ROUND(ima.interval_cost_usd, 2) AS interval_cost_usd,
    ima.active_meter_count,
    ROUND(ima.feeder_aggregate_demand_kw, 2) AS feeder_aggregate_demand_kw,
    ROUND(ima.machine_submeters_demand_kw, 2) AS machine_submeters_demand_kw
FROM interval_meter_aggregates ima
JOIN tariffs t ON ima.tariff_id = t.tariff_id
ORDER BY ima.plant_total_demand_kw DESC
LIMIT 20;
-- QUERY_4_END


-- ----------------------------------------------------------------------------
-- Query 5: Which machines have the highest energy intensity?
-- Calculates kWh per unit of actual good production output
-- ----------------------------------------------------------------------------
-- QUERY_5_START
-- Overlapping batch windows: each reading belongs to the latest-starting batch, then the lowest batch ID.
WITH batch_energy AS (
    SELECT
        batch_id,
        machine_id,
        product_sku,
        actual_good_units,
        actual_scrap_units,
        SUM(energy_consumed_kwh) AS batch_kwh,
        SUM(cost_usd) AS batch_cost_usd
    FROM (
        SELECT
            b.batch_id,
            b.machine_id,
            b.product_sku,
            b.actual_good_units,
            b.actual_scrap_units,
            r.energy_consumed_kwh,
            r.cost_usd,
            ROW_NUMBER() OVER (
                PARTITION BY r.reading_id
                ORDER BY b.start_timestamp DESC, b.batch_id
            ) AS batch_rank
        FROM production_batches b
        JOIN energy_readings r ON b.machine_id = r.machine_id
            AND r.timestamp >= b.start_timestamp
            AND r.timestamp <= b.end_timestamp
        WHERE r.is_anomaly = 0
    ) assigned_readings
    WHERE batch_rank = 1
    GROUP BY batch_id, machine_id, product_sku, actual_good_units, actual_scrap_units
)
SELECT 
    m.machine_id,
    m.name AS machine_name,
    m.category,
    COUNT(DISTINCT b.batch_id) AS total_batches_run,
    SUM(b.actual_good_units) AS total_good_units_produced,
    ROUND(SUM(COALESCE(be.batch_kwh, 0)), 2) AS total_production_kwh,
    ROUND(SUM(COALESCE(be.batch_kwh, 0)) / NULLIF(SUM(b.actual_good_units), 0), 4) AS energy_intensity_kwh_per_unit,
    ROUND(SUM(COALESCE(be.batch_cost_usd, 0)) / NULLIF(SUM(b.actual_good_units), 0), 4) AS cost_per_unit_usd
FROM machines m
JOIN production_batches b ON m.machine_id = b.machine_id
LEFT JOIN batch_energy be ON b.batch_id = be.batch_id
GROUP BY m.machine_id, m.name, m.category
HAVING total_good_units_produced > 0
ORDER BY energy_intensity_kwh_per_unit DESC;
-- QUERY_5_END


-- ----------------------------------------------------------------------------
-- Query 6: What are the most expensive tariff periods?
-- Total spend, energy, and average cost breakdown by tariff period type
-- ----------------------------------------------------------------------------
-- QUERY_6_START
SELECT 
    t.period_type,
    t.rate_per_kwh_usd,
    COUNT(r.reading_id) AS total_reading_intervals,
    ROUND(SUM(r.energy_consumed_kwh), 2) AS total_energy_kwh,
    ROUND(SUM(r.cost_usd), 2) AS total_spend_usd,
    ROUND(100.0 * SUM(r.cost_usd) / (
        SELECT SUM(r2.cost_usd) 
        FROM energy_readings r2 
        JOIN meters m2 ON r2.meter_id = m2.meter_id 
        WHERE r2.is_anomaly = 0 AND m2.meter_type = 'MAIN_INCOMER'
    ), 2) AS pct_of_total_cost,
    ROUND(100.0 * SUM(r.energy_consumed_kwh) / (
        SELECT SUM(r3.energy_consumed_kwh) 
        FROM energy_readings r3 
        JOIN meters m3 ON r3.meter_id = m3.meter_id 
        WHERE r3.is_anomaly = 0 AND m3.meter_type = 'MAIN_INCOMER'
    ), 2) AS pct_of_total_kwh
FROM energy_readings r
JOIN meters m ON r.meter_id = m.meter_id
JOIN tariffs t ON r.tariff_id = t.tariff_id
WHERE r.is_anomaly = 0 AND m.meter_type = 'MAIN_INCOMER'
GROUP BY t.period_type, t.rate_per_kwh_usd
ORDER BY total_spend_usd DESC;
-- QUERY_6_END


-- ----------------------------------------------------------------------------
-- Query 7: Which production shifts consume the most energy?
-- Correlation of shift schedules to total energy and cost
-- ----------------------------------------------------------------------------
-- QUERY_7_START
-- Batch energy uses the same one-reading/one-batch attribution as Query 5.
WITH distinct_batch_energy AS (
    SELECT 
        batch_id,
        shift_id,
        actual_good_units,
        actual_scrap_units,
        SUM(energy_consumed_kwh) AS batch_kwh,
        SUM(cost_usd) AS batch_cost_usd
    FROM (
        SELECT
            b.batch_id,
            b.shift_id,
            b.actual_good_units,
            b.actual_scrap_units,
            b.start_timestamp,
            r.reading_id,
            r.energy_consumed_kwh,
            r.cost_usd,
            ROW_NUMBER() OVER (
                PARTITION BY r.reading_id
                ORDER BY b.start_timestamp DESC, b.batch_id
            ) AS batch_rank
        FROM production_batches b
        JOIN energy_readings r ON b.machine_id = r.machine_id
            AND r.timestamp >= b.start_timestamp
            AND r.timestamp <= b.end_timestamp
        WHERE r.is_anomaly = 0
    ) assigned_readings
    WHERE batch_rank = 1
    GROUP BY batch_id, shift_id, actual_good_units, actual_scrap_units
),
shift_batch_summary AS (
    SELECT 
        shift_id,
        COUNT(batch_id) AS batches_processed,
        SUM(actual_good_units) AS total_units_produced
    FROM production_batches
    GROUP BY shift_id
),
shift_machine_energy AS (
    SELECT
        shift_id,
        SUM(batch_kwh) AS machine_production_kwh,
        SUM(batch_cost_usd) AS machine_production_cost_usd
    FROM distinct_batch_energy
    GROUP BY shift_id
),
facility_shift_energy AS (
    SELECT 
        s.shift_id,
        ROUND(SUM(r.energy_consumed_kwh), 2) AS facility_shift_kwh,
        ROUND(SUM(r.cost_usd), 2) AS facility_shift_cost_usd
    FROM shifts s
    JOIN energy_readings r ON (
        CASE 
            WHEN s.start_time_local < s.end_time_local 
            THEN TIME(r.timestamp) >= s.start_time_local AND TIME(r.timestamp) < s.end_time_local
            ELSE TIME(r.timestamp) >= s.start_time_local OR TIME(r.timestamp) < s.end_time_local
        END
    )
    JOIN meters m ON r.meter_id = m.meter_id
    WHERE r.is_anomaly = 0 AND m.meter_type = 'MAIN_INCOMER'
    GROUP BY s.shift_id
)
SELECT 
    s.shift_id,
    s.name AS shift_name,
    s.start_time_local,
    s.end_time_local,
    COALESCE(sbs.batches_processed, 0) AS batches_processed,
    COALESCE(sbs.total_units_produced, 0) AS total_units_produced,
    ROUND(COALESCE(sme.machine_production_kwh, 0), 2) AS machine_production_kwh,
    ROUND(COALESCE(sme.machine_production_cost_usd, 0), 2) AS machine_production_cost_usd,
    COALESCE(fse.facility_shift_kwh, 0) AS facility_shift_kwh,
    COALESCE(fse.facility_shift_cost_usd, 0) AS facility_shift_cost_usd,
    ROUND(COALESCE(fse.facility_shift_kwh, 0), 2) AS total_shift_kwh,
    ROUND(COALESCE(fse.facility_shift_cost_usd, 0), 2) AS total_shift_cost_usd,
    ROUND(COALESCE(fse.facility_shift_kwh, 0) / NULLIF(sbs.total_units_produced, 0), 4) AS shift_energy_intensity
FROM shifts s
LEFT JOIN shift_batch_summary sbs ON s.shift_id = sbs.shift_id
LEFT JOIN shift_machine_energy sme ON s.shift_id = sme.shift_id
LEFT JOIN facility_shift_energy fse ON s.shift_id = fse.shift_id
ORDER BY facility_shift_cost_usd DESC;
-- QUERY_7_END


-- ----------------------------------------------------------------------------
-- Query 8: Which machines have abnormal consumption?
-- Ranks machines by peak and average deviation from nominal operating power
-- ----------------------------------------------------------------------------
-- QUERY_8_START
SELECT 
    m.machine_id,
    m.name AS machine_name,
    m.category,
    m.rated_power_kw,
    COUNT(r.reading_id) AS total_readings,
    ROUND(MAX(r.power_demand_kw), 2) AS max_recorded_kw,
    ROUND(AVG(r.power_demand_kw), 2) AS avg_recorded_kw,
    ROUND(m.operating_power_kw, 2) AS nominal_operating_kw,
    ROUND(100.0 * (MAX(r.power_demand_kw) - m.operating_power_kw) / m.operating_power_kw, 2) AS peak_pct_over_nominal,
    ROUND(100.0 * (AVG(r.power_demand_kw) - m.operating_power_kw) / m.operating_power_kw, 2) AS avg_pct_deviation_from_nominal
FROM machines m
JOIN energy_readings r ON m.machine_id = r.machine_id
WHERE r.is_anomaly = 0
GROUP BY m.machine_id, m.name, m.category, m.rated_power_kw, m.operating_power_kw
ORDER BY peak_pct_over_nominal DESC;
-- QUERY_8_END


-- ----------------------------------------------------------------------------
-- Query 9: What are the top energy-saving opportunities?
-- Ranked actionable recommendations with expected savings and payback period
-- ----------------------------------------------------------------------------
-- QUERY_9_START
SELECT 
    rec.recommendation_id,
    m.name AS machine_name,
    rec.category,
    rec.title,
    rec.priority,
    ROUND(rec.expected_savings_kwh, 0) AS expected_savings_kwh,
    ROUND(rec.estimated_annual_cost_savings_usd, 2) AS estimated_savings_usd,
    ROUND(rec.implementation_cost_usd, 2) AS capex_usd,
    ROUND(rec.payback_months, 1) AS payback_months,
    rec.status
FROM recommendations rec
JOIN machines m ON rec.machine_id = m.machine_id
ORDER BY estimated_annual_cost_savings_usd DESC;
-- QUERY_9_END


-- ----------------------------------------------------------------------------
-- Query 10: How much estimated cost could be saved?
-- Facility-wide savings summary grouped by priority and recommendation category
-- ----------------------------------------------------------------------------
-- QUERY_10_START
SELECT 
    priority,
    COUNT(recommendation_id) AS total_recommendations,
    ROUND(SUM(expected_savings_kwh), 0) AS total_potential_kwh_saved,
    ROUND(SUM(estimated_annual_cost_savings_usd), 2) AS total_potential_annual_savings_usd,
    ROUND(SUM(implementation_cost_usd), 2) AS total_implementation_cost_usd,
    ROUND(
        CASE WHEN SUM(estimated_annual_cost_savings_usd) > 0 
        THEN (CAST(SUM(implementation_cost_usd) AS REAL) / CAST(SUM(estimated_annual_cost_savings_usd) AS REAL)) * 12.0 
        ELSE 0.0 END, 1
    ) AS weighted_payback_months
FROM recommendations
GROUP BY priority
ORDER BY 
    CASE priority 
        WHEN 'HIGH' THEN 1 
        WHEN 'MEDIUM' THEN 2 
        ELSE 3 
    END;
-- QUERY_10_END
