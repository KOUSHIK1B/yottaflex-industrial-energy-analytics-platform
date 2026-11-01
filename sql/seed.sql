-- ============================================================================
-- YottaFlex Industrial Energy Analytics Platform - Master & Reference Seed Data
-- ============================================================================

-- 1. PLANT
INSERT OR IGNORE INTO plants (
    plant_id, name, industry_type, country, state, city, timezone,
    grid_connection_voltage_kv, contracted_peak_capacity_kw, created_at
) VALUES (
    'PLT-001', 'YottaFlex Precision Metals & Robotics Plant #1',
    'Precision Metals & Robotics Manufacturing', 'USA', 'TX', 'Austin',
    'America/Chicago', 13.80, 2500.00, '2026-01-01 00:00:00'
);

-- 2. METERS
INSERT OR IGNORE INTO meters (meter_id, plant_id, parent_meter_id, name, meter_type, measurement_unit, voltage_rating_v, current_rating_a, installation_date, status) VALUES
('MTR-PLT-001-001', 'PLT-001', NULL, 'Utility 13.8kV Main Incomer Meter', 'MAIN_INCOMER', 'kWh', 13800.0, 1500.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-002', 'PLT-001', 'MTR-PLT-001-001', 'Feeder A: CNC & Milling Center Substation', 'SUB_FEEDER', 'kWh', 480.0, 1200.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-003', 'PLT-001', 'MTR-PLT-001-001', 'Feeder B: Heavy Molding & Press Substation', 'SUB_FEEDER', 'kWh', 480.0, 1000.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-004', 'PLT-001', 'MTR-PLT-001-001', 'Feeder C: Thermal, Chiller & Utilities Busbar', 'SUB_FEEDER', 'kWh', 480.0, 1000.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-005', 'PLT-001', 'MTR-PLT-001-002', 'Meter - 5-Axis CNC Milling Center #1', 'MACHINE_POINT', 'kWh', 480.0, 150.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-006', 'PLT-001', 'MTR-PLT-001-002', 'Meter - 5-Axis CNC Milling Center #2', 'MACHINE_POINT', 'kWh', 480.0, 150.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-007', 'PLT-001', 'MTR-PLT-001-002', 'Meter - High-Speed CNC Lathe #1', 'MACHINE_POINT', 'kWh', 480.0, 100.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-008', 'PLT-001', 'MTR-PLT-001-002', 'Meter - High-Speed CNC Lathe #2', 'MACHINE_POINT', 'kWh', 480.0, 100.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-009', 'PLT-001', 'MTR-PLT-001-003', 'Meter - Hydraulic Injection Molder 350T', 'MACHINE_POINT', 'kWh', 480.0, 250.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-010', 'PLT-001', 'MTR-PLT-001-003', 'Meter - Electric Injection Molder 180T', 'MACHINE_POINT', 'kWh', 480.0, 180.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-011', 'PLT-001', 'MTR-PLT-001-003', 'Meter - Precision Injection Molder 120T', 'MACHINE_POINT', 'kWh', 480.0, 140.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-012', 'PLT-001', 'MTR-PLT-001-003', 'Meter - Heavy Stamping Press 500T', 'MACHINE_POINT', 'kWh', 480.0, 300.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-013', 'PLT-001', 'MTR-PLT-001-004', 'Meter - Continuous Thermal Curing Oven #1', 'MACHINE_POINT', 'kWh', 480.0, 350.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-014', 'PLT-001', 'MTR-PLT-001-004', 'Meter - Batch Heat Treatment Oven #2', 'MACHINE_POINT', 'kWh', 480.0, 250.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-015', 'PLT-001', 'MTR-PLT-001-004', 'Meter - Central Rotary Screw Compressor #1', 'MACHINE_POINT', 'kWh', 480.0, 200.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-016', 'PLT-001', 'MTR-PLT-001-004', 'Meter - Central Rotary Screw Compressor #2', 'MACHINE_POINT', 'kWh', 480.0, 200.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-017', 'PLT-001', 'MTR-PLT-001-004', 'Meter - Water-Cooled Central Chiller #1', 'MACHINE_POINT', 'kWh', 480.0, 300.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-018', 'PLT-001', 'MTR-PLT-001-004', 'Meter - Water-Cooled Central Chiller #2', 'MACHINE_POINT', 'kWh', 480.0, 300.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-019', 'PLT-001', 'MTR-PLT-001-002', 'Meter - Automated 6-Axis Assembly Cell', 'MACHINE_POINT', 'kWh', 480.0, 80.0, '2025-06-01', 'ACTIVE'),
('MTR-PLT-001-020', 'PLT-001', 'MTR-PLT-001-003', 'Meter - Main Facility Overhead Conveyor Loop', 'MACHINE_POINT', 'kWh', 480.0, 80.0, '2025-06-01', 'ACTIVE');

-- 3. MACHINES
INSERT OR IGNORE INTO machines (machine_id, plant_id, name, category, rated_power_kw, standby_power_kw, operating_power_kw, commissioning_date, lifecycle_state) VALUES
('MCH-PLT-001-001', 'PLT-001', '5-Axis CNC Milling Center Alpha', 'CNC_MILLING', 75.0, 4.5, 48.0, '2025-06-10', 'OPERATIONAL'),
('MCH-PLT-001-002', 'PLT-001', '5-Axis CNC Milling Center Beta', 'CNC_MILLING', 75.0, 4.5, 46.5, '2025-06-10', 'OPERATIONAL'),
('MCH-PLT-001-003', 'PLT-001', 'High-Speed CNC Lathe Gamma', 'CNC_MILLING', 45.0, 3.2, 32.0, '2025-06-15', 'OPERATIONAL'),
('MCH-PLT-001-004', 'PLT-001', 'High-Speed CNC Lathe Delta', 'CNC_MILLING', 45.0, 3.2, 31.5, '2025-06-15', 'OPERATIONAL'),
('MCH-PLT-001-005', 'PLT-001', 'Hydraulic Injection Molder 350T', 'INJECTION_MOLDING', 120.0, 8.5, 88.0, '2025-07-01', 'OPERATIONAL'),
('MCH-PLT-001-006', 'PLT-001', 'Electric Injection Molder 180T', 'INJECTION_MOLDING', 85.0, 4.0, 58.0, '2025-07-01', 'OPERATIONAL'),
('MCH-PLT-001-007', 'PLT-001', 'Precision Injection Molder 120T', 'INJECTION_MOLDING', 65.0, 3.5, 42.0, '2025-07-05', 'OPERATIONAL'),
('MCH-PLT-001-008', 'PLT-001', 'Heavy Stamping Press 500T', 'STAMPING_PRESS', 150.0, 7.0, 95.0, '2025-07-10', 'OPERATIONAL'),
('MCH-PLT-001-009', 'PLT-001', 'Continuous Thermal Curing Oven', 'INDUSTRIAL_OVEN', 160.0, 18.0, 125.0, '2025-07-15', 'OPERATIONAL'),
('MCH-PLT-001-010', 'PLT-001', 'Batch Heat Treatment Oven', 'INDUSTRIAL_OVEN', 110.0, 12.0, 78.0, '2025-07-15', 'OPERATIONAL'),
('MCH-PLT-001-011', 'PLT-001', 'Central Rotary Screw Compressor #1', 'ROTARY_SCREW_COMPRESSOR', 90.0, 18.5, 72.0, '2025-06-20', 'OPERATIONAL'),
('MCH-PLT-001-012', 'PLT-001', 'Central Rotary Screw Compressor #2', 'ROTARY_SCREW_COMPRESSOR', 90.0, 18.5, 70.0, '2025-06-20', 'OPERATIONAL'),
('MCH-PLT-001-013', 'PLT-001', 'Water-Cooled Central Chiller #1', 'CHILLER_PLANT', 140.0, 22.0, 98.0, '2025-06-25', 'OPERATIONAL'),
('MCH-PLT-001-014', 'PLT-001', 'Water-Cooled Central Chiller #2', 'CHILLER_PLANT', 140.0, 22.0, 94.0, '2025-06-25', 'OPERATIONAL'),
('MCH-PLT-001-015', 'PLT-001', 'Automated 6-Axis Assembly Cell', 'AUTOMATED_ASSEMBLY_ROBOT', 35.0, 2.5, 21.0, '2025-08-01', 'OPERATIONAL'),
('MCH-PLT-001-016', 'PLT-001', 'Main Overhead Conveyor Loop', 'CONVEYOR_SYSTEM', 30.0, 2.0, 18.0, '2025-08-01', 'OPERATIONAL');

-- 4. MACHINE METER ASSIGNMENTS
INSERT OR IGNORE INTO machine_meter_assignments (assignment_id, machine_id, meter_id, effective_from, effective_to, allocation_percentage, is_primary_meter) VALUES
('ASN-MCH-PLT-001-001-MTR-PLT-001-005', 'MCH-PLT-001-001', 'MTR-PLT-001-005', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-002-MTR-PLT-001-006', 'MCH-PLT-001-002', 'MTR-PLT-001-006', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-003-MTR-PLT-001-007', 'MCH-PLT-001-003', 'MTR-PLT-001-007', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-004-MTR-PLT-001-008', 'MCH-PLT-001-004', 'MTR-PLT-001-008', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-005-MTR-PLT-001-009', 'MCH-PLT-001-005', 'MTR-PLT-001-009', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-006-MTR-PLT-001-010', 'MCH-PLT-001-006', 'MTR-PLT-001-010', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-007-MTR-PLT-001-011', 'MCH-PLT-001-007', 'MTR-PLT-001-011', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-008-MTR-PLT-001-012', 'MCH-PLT-001-008', 'MTR-PLT-001-012', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-009-MTR-PLT-001-013', 'MCH-PLT-001-009', 'MTR-PLT-001-013', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-010-MTR-PLT-001-014', 'MCH-PLT-001-010', 'MTR-PLT-001-014', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-011-MTR-PLT-001-015', 'MCH-PLT-001-011', 'MTR-PLT-001-015', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-012-MTR-PLT-001-016', 'MCH-PLT-001-012', 'MTR-PLT-001-016', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-013-MTR-PLT-001-017', 'MCH-PLT-001-013', 'MTR-PLT-001-017', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-014-MTR-PLT-001-018', 'MCH-PLT-001-014', 'MTR-PLT-001-018', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-015-MTR-PLT-001-019', 'MCH-PLT-001-015', 'MTR-PLT-001-019', '2026-01-01 00:00:00', NULL, 100.0, 1),
('ASN-MCH-PLT-001-016-MTR-PLT-001-020', 'MCH-PLT-001-016', 'MTR-PLT-001-020', '2026-01-01 00:00:00', NULL, 100.0, 1);

-- 5. SHIFTS
INSERT OR IGNORE INTO shifts (shift_id, plant_id, name, start_time_local, end_time_local, duration_hours, standard_manning_level, shift_multiplier) VALUES
('SHF-001', 'PLT-001', 'Morning Production Shift', '06:00:00', '14:00:00', 8.0, 42, 1.05),
('SHF-002', 'PLT-001', 'Afternoon Peak Shift', '14:00:00', '22:00:00', 8.0, 38, 1.00),
('SHF-003', 'PLT-001', 'Night Low-Energy Shift', '22:00:00', '06:00:00', 8.0, 18, 0.85);

-- 6. TARIFFS
INSERT OR IGNORE INTO tariffs (tariff_id, plant_id, tariff_code, name, period_type, rate_per_kwh_usd, demand_charge_per_kw_usd, start_hour, end_hour, is_weekend_applicable, effective_from, effective_to) VALUES
('TAR-2026-001', 'PLT-001', 'TOU-OFFPEAK-LV', 'Off-Peak Base Power Tariff', 'OFF_PEAK', 0.0650, 5.0000, 22, 7, 1, '2026-01-01', '2026-12-31'),
('TAR-2026-002', 'PLT-001', 'TOU-SHOULDER-LV', 'Shoulder Commercial Tariff', 'SHOULDER', 0.1280, 10.0000, 7, 13, 0, '2026-01-01', '2026-12-31'),
('TAR-2026-003', 'PLT-001', 'TOU-ONPEAK-LV', 'On-Peak High Demand Tariff', 'ON_PEAK', 0.2250, 18.5000, 13, 19, 0, '2026-01-01', '2026-12-31'),
('TAR-2026-004', 'PLT-001', 'TOU-CRITPEAK-LV', 'Critical Peak Summer Event Tariff', 'CRITICAL_PEAK', 0.4500, 25.0000, 14, 18, 0, '2026-06-01', '2026-09-30');
