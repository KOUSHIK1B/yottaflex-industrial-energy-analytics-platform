# YottaFlex Industrial Energy Analytics Platform

A full-stack industrial energy analytics platform for monitoring electricity consumption, analyzing machine performance, detecting data-quality anomalies, and identifying energy-saving opportunities. Built with Python, SQLite, SQL, TypeScript, React, and Vite.

## Features

**Industrial Energy Monitoring**
- Monitor electricity consumption across 20 industrial meters.
- Analyze 90 days of energy readings at 15-minute intervals.
- Track facility-level energy consumption and peak demand.
- Monitor machine-wise electricity usage and performance.

**Machine Performance Analytics**
- Analyze energy consumption by individual machine.
- Calculate machine energy intensity (kWh/unit).
- Identify idle energy consumption and wastage.
- Compare machine demand and production performance.

**Anomaly Detection and Data Quality**
- Detect five categories of intentionally injected data anomalies:
  - kW/kWh measurement confusion
  - Tariff timezone mismatch
  - Meter total mismatch
  - Duplicate energy readings
  - Meter hierarchy and foreign-key violations
- Maintain anomaly ground truth for verification.
- Validate database integrity and data consistency.
- Generate validation and anomaly reports.

**SQL-Based Business Analytics**
- Execute 10 analytical SQL queries.
- Identify top energy-consuming machines.
- Analyze machine idle energy wastage.
- Monitor daily energy consumption.
- Identify facility peak-demand intervals.
- Analyze production batch energy intensity.
- Compare time-of-use tariff distribution.
- Evaluate shift-wise energy consumption and productivity.
- Identify abnormal machine consumption.
- Estimate energy-saving intervention opportunities.

**Actionable Engineering Recommendations**
- Generate machine-level energy-saving recommendations.
- Identify high, medium, and low-priority interventions.
- Estimate annual financial savings.
- Estimate potential energy savings.
- Calculate investment payback periods.

**Interactive Dashboard**
- Executive Overview
- Machine Performance & Intensity
- Validation Engine
- Anomaly Ground Truth
- Live SQL Query Studio
- Actionable Interventions & ROI
- Architecture

## Tech Stack

- **Backend / Data Processing:** Python
- **Database:** SQLite
- **Analytics:** SQL, Pandas, NumPy
- **Frontend:** React, TypeScript
- **Build Tool:** Vite
- **Server:** Node.js, TypeScript
- **Testing:** Pytest
- **Data Storage:** CSV, JSON, SQLite

## Project Dataset

The platform uses a reproducible synthetic industrial energy dataset.

| Dataset component | Details |
|---|---|
| Industrial meters | 20 |
| Monitoring period | 90 days |
| Reading interval | 15 minutes |
| Baseline energy readings | 172,800 |
| Production batches | 2,000 |
| Intentional anomalies | 125 |
| Anomaly categories | 5 |
| Analytical SQL queries | 10 |

**Meter Hierarchy**

The industrial facility contains:
- 1 main incomer meter
- 3 subfeeder meters
- 16 machine-level meters

The main incomer is used for facility-level demand analysis to avoid double-counting downstream meter consumption.

## Prerequisites

- Python 3.13 recommended
- Node.js and npm
- Git
- Visual Studio Code (recommended)
- Windows, Linux, or macOS

## Setup Instructions

### 1. Clone or Download the Project

```bash
git clone https://github.com/YOUR_USERNAME/yottaflex-industrial-energy-analytics-platform.git
cd yottaflex-industrial-energy-analytics-platform
```

### 2. Create a Python Virtual Environment

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Install Frontend and Backend Dependencies

```bash
npm install
```

### 5. Configure Environment Variables

The project includes an `.env.example` template.

Review the template and configure any required environment variables according to the application configuration.

Do not commit API keys, passwords, or other secrets to GitHub.

The core Python and SQLite analytics pipeline uses the local project database.

### 6. Generate the Industrial Energy Dataset

Run the complete pipeline:

```bash
python main.py --all
```

The pipeline performs the following operations:

- Generates industrial master and reference data.
- Generates energy readings and production batches.
- Injects the five intentional anomaly categories.
- Stores the generated data in the SQLite database.
- Executes data validation.
- Performs analytical calculations.
- Generates reports and analytical outputs.

The pipeline uses a deterministic random seed for reproducibility.

### 7. Run the SQL Analytics

Execute:

```bash
python run_sql_analysis.py
```

This runs the analytical SQL queries and generates corresponding result files.

### 8. Run the Python Test Suite

Execute:

```bash
python -m pytest -v
```

The test suite verifies:
- Database structure and integrity.
- Data generation and reproducibility.
- Anomaly injection and detection.
- Analytical calculations.
- SQL query execution.
- Business logic and recommendations.

### 9. Run the Application

Start the full-stack application:

```bash
npm run dev
```

The development server starts on:

```text
http://localhost:3000
```

Open the URL in your browser to access the YottaFlex dashboard.

## Database Schema and Data Organization

The project uses SQLite for relational data storage.

**Database Location**

```text
database/energy_analytics.db
```

**Data Organization**

| Directory | Purpose |
|---|---|
| data/master/ | Plant, meter and machine master data |
| data/reference/ | Tariff, shift and weather reference data |
| data/transactions/ | Energy readings and production batches |
| data/events/ | Maintenance events |
| data/ground_truth/ | Known injected anomaly records |
| database/ | SQLite database |
| outputs/ | Generated analytical results and reports |
| sql/ | Database schema, seed data and analytical queries |
| docs/ | Architecture and project documentation |
| tests/ | Automated test cases |

## Anomaly Categories

The platform introduces five intentional data-quality problems to demonstrate industrial telemetry validation.

| Anomaly | Count | Description |
|---|---:|---|
| kW/kWh confusion | 35 | Incorrect interpretation of power and energy measurements |
| Tariff timezone mismatch | 30 | Incorrect tariff time alignment |
| Meter total mismatch | 25 | Difference between meter totals and expected reconciliation |
| Duplicate readings | 20 | Repeated energy telemetry records |
| Meter hierarchy violation | 15 | Invalid meter hierarchy or foreign-key relationship |
| **Total** | **125** | **Intentional anomalies** |

The validation engine checks the data against known ground truth to evaluate anomaly detection performance.

## Analytical SQL Queries

The project includes 10 analytical SQL queries.

| Query | Analysis |
|---|---|
| Q1 | Top Consuming Machines |
| Q2 | Machine Idle Energy Wastage |
| Q3 | Daily Energy Consumption |
| Q4 | Facility Peak Demand Intervals |
| Q5 | Production Batch Energy Intensity |
| Q6 | Time-of-Use Tariff Distribution |
| Q7 | Shift Energy and Productivity |
| Q8 | Abnormal Machine Consumption |
| Q9 | Energy-Saving Interventions |
| Q10 | Cost Reduction Portfolio Summary |

The SQL Query Studio allows users to select and execute analytical queries and inspect their results.

## Dashboard Modules

**1. Executive Overview**

Displays facility-level energy consumption, electricity expenditure, peak demand, idle energy wastage, production batches and anomaly statistics.

**2. Machine Performance & Intensity**

Displays machine-wise electricity consumption, production output, energy intensity, peak demand and idle energy wastage.

**3. Validation Engine**

Runs data-quality checks covering primary keys, foreign keys, mandatory fields, measurement units, duplicates, timestamps, tariff alignment, meter hierarchy and energy calculations.

**4. Anomaly Ground Truth**

Displays injected anomaly categories, ground-truth values, corrupted values, severity and detection information.

**5. Live SQL Query Studio**

Provides access to the 10 analytical SQL queries and their execution results.

**6. Actionable Interventions & ROI**

Displays engineering recommendations, estimated annual savings, potential energy savings, implementation priorities and payback periods.

**7. Architecture**

Provides an overview of the platform architecture and its components.

## Validation and Testing Results

The project was tested using automated Python tests and the complete data-generation pipeline.

**Verified results:**

- Python automated tests: 29/29 passed.
- Full data-generation pipeline: completed successfully.
- Baseline energy readings: 172,800.
- Final energy readings after anomaly injection: 172,820.
- Production batches: 2,000.
- Intentional anomalies injected: 125.
- Ground-truth detection: 100% (125/125).
- Analytical SQL queries: 10/10 executed successfully.
- Database integrity: Valid.
- TypeScript compilation: no errors reported.
- Vite production build: successful.

## Business Impact and Cost Reduction

The platform generates engineering recommendations based on machine energy consumption and operational analysis.

The analytical results estimate the following annual savings opportunities:

| Priority | Estimated Annual Savings |
|---|---:|
| High | $170,850 |
| Medium | $49,050 |
| Low | $8,948.32 |
| **Total** | **$228,848.32** |

These are model-generated estimates based on the synthetic dataset and should not be interpreted as verified real-world savings.

## Reproducibility

The data-generation pipeline uses a fixed random seed to ensure consistent dataset generation.

The project includes reproducibility verification scripts and generated reports.

Run:

```bash
python verify_reproducibility.py
```

## Troubleshooting

**Python Dependency Issues**

Verify that the virtual environment is activated and install the required dependencies again:

```bash
python -m pip install -r requirements.txt
```

**Database Connection or File Issues**

Verify that the following file exists:

```text
database/energy_analytics.db
```

If the database needs to be regenerated, run:

```bash
python main.py --all
```

**Frontend Dependency Issues**

Install dependencies:

```bash
npm install
```

Then start the application:

```bash
npm run dev
```

**Port 3000 Already in Use**

Stop the existing server process before restarting the application.

**SQL Query Execution Issues**

Verify that the SQLite database exists and that the required schema and analytical SQL files are available in the `sql/` directory.

**Test Execution Issues**

Run the tests from the project root with the virtual environment activated:

```bash
python -m pytest -v
```

## Development

Run the frontend and backend development server:

```bash
npm run dev
```

Run Python tests:

```bash
python -m pytest -v
```

Check TypeScript compilation:

```bash
npm run lint
```

Build the production frontend:

```bash
npm run build
```

## Production Build

Generate the production frontend build:

```bash
npm run build
```

The generated production assets are stored in the `dist/` directory.

The application should be deployed with the required Python, Node.js and SQLite runtime configuration.

## License

This project is developed for educational and technical assessment purposes.

## Support and Documentation

For additional information, refer to:

- Python Documentation: https://docs.python.org/3/
- SQLite Documentation: https://www.sqlite.org/docs.html
- React Documentation: https://react.dev/
- TypeScript Documentation: https://www.typescriptlang.org/docs/
- Vite Documentation: https://vite.dev/guide/
- Pandas Documentation: https://pandas.pydata.org/docs/
