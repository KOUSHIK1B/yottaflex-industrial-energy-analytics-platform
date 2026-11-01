# Business Logic & Analytical Calculation Rules
## YottaFlex Industrial Energy Analytics Platform

### 1. Energy Consumption Calculation
- **Rule**: Instantaneous electrical power demand ($P$ in kW) recorded over a discrete time interval ($\Delta t = 15\text{ minutes} = 0.25\text{ hours}$) yields electrical energy ($E$ in kWh).
- **Formula**:
  $$E_{\text{interval}} (\text{kWh}) = P_{\text{avg}} (\text{kW}) \times \frac{\Delta t (\text{minutes})}{60} = P_{\text{avg}} \times 0.25$$
- **Enforcement**: Energy reading must never be independent of power. Any deviation between $P \times 0.25$ and $E$ is flagged as an energy calculation error (Category 2 anomaly).

### 2. Peak Electricity Demand
- **Rule**: Facility peak demand is the maximum active power draw ($kW$) recorded by the main incomer over 15-minute settlement intervals. Do not sum parent and child meters, because hierarchical readings represent overlapping energy.
- **Formula**:
  $$P_{\text{facility}}^{\text{coincident}}(t) = P_{\text{main incomer}}(t)$$
  $$\text{Peak Demand} = \max_{t \in T} P_{\text{facility}}^{\text{coincident}}(t)$$
- **Utility Impact**: Demand charges are billed at monthly maximum coincident peak ($14.50/kW on Peak, $8.00/kW Off-Peak).

### 3. Time-of-Use (TOU) Energy Costing
- **Rule**: Every energy reading interval timestamp is mapped to the active tariff rule based on local facility timezone (`America/Chicago`), day-of-week (weekday vs weekend), and hour of day.
- **Tariff Windows**:
  - `ON_PEAK`: Weekdays 13:00 to 19:00 ($0.2250 / kWh)
  - `SHOULDER`: Weekdays 07:00 to 13:00 and 19:00 to 22:00 ($0.1280 / kWh)
  - `OFF_PEAK`: Weekdays 22:00 to 07:00, plus all Weekend hours ($0.0650 / kWh)
  - `CRITICAL_PEAK`: Extreme ambient temperature windows (>38°C) between 14:00-18:00 ($0.4500 / kWh)
- **Formula**:
  $$\text{Cost} (\$) = E_{\text{interval}} (\text{kWh}) \times \text{Rate}_{\text{tariff}} (\$ / \text{kWh})$$

### 4. Energy Intensity (Specific Energy Consumption - SEC)
- **Rule**: Energy intensity measures the kilowatt-hours required to produce one unit of verified good production output for each machine and batch.
- **Formula**:
  $$\text{SEC}_{\text{batch}} (\text{kWh/unit}) = \frac{\sum_{t \in [t_{\text{start}}, t_{\text{end}}]} E_{\text{machine}}(t)}{\text{Actual Good Units Produced}}$$
- **Overlapping batches**: Assign a matched machine reading to only one batch: the overlapping batch with the latest start timestamp, with `batch_id` as a deterministic tie-breaker. Shift batch counts and good-unit totals are calculated from production records independently of telemetry joins.
- **Baseline Benchmarking**:
  - CNC Milling: 1.80 - 2.80 kWh / unit
  - Injection Molding: 3.20 - 4.50 kWh / unit
  - Industrial Oven: 5.50 - 8.20 kWh / unit
  - Stamping Press: 1.10 - 1.90 kWh / unit

### 5. Idle Energy Consumption & Wastage
- **Rule**: When a production machine is energized without active parts output (status starved, blocked downstream, operator break, or off-shift standby), the energy consumed is categorized as non-productive idle energy.
- **Formula**:
  $$E_{\text{idle}} (\text{kWh}) = P_{\text{standby}} (\text{kW}) \times \frac{\text{Duration (min)}}{60}$$
  $$\text{Wasted Cost} (\$) = E_{\text{idle}} \times \text{Rate}_{\text{effective}}$$

### 6. Weather Correlation & Cooling Degree Load
- **Rule**: Central chillers and facility HVAC power demands correlate with outdoor dry-bulb temperature and humidity.
- **Formula**:
  $$\text{Cooling Degree Factor} = \max(0, T_{\text{ambient}} - 18.33^\circ\text{C})$$
  $$P_{\text{chiller}}(t) = P_{\text{base}} + (\beta_T \times \text{Factor}) + \epsilon$$

### 7. Recommendations Engine & Payback
- **Rule**: Automated algorithmic generation of quantifiable interventions with baseline, annual kWh savings, USD financial savings, implementation CAPEX, and payback period in months.
- **Formula**:
  $$\text{Annual Cost Savings} (\$) = \Delta \text{kWh}_{\text{annual}} \times \bar{\text{Rate}}_{\text{blended}}$$
  $$\text{Payback (months)} = \left(\frac{\text{CAPEX}}{\text{Annual Cost Savings}}\right) \times 12$$
