"""
YottaFlex Industrial Energy Analytics Platform - SQL Analysis Runner
===================================================================
Executes the 10 production analytical queries defined in sql/analysis_queries.sql
directly against the SQLite database (database/energy_analytics.db) and formats
results in human-readable tabular previews.
"""

import csv
import json
from pathlib import Path
from typing import Optional
import config
from src.database.db_manager import DatabaseManager

QUERY_TITLES = [
    "1. Top 10 Energy-Consuming Machines & Specific Energy Consumption (SEC)",
    "2. Machine Idle Period Energy Waste & Financial Standby Loss",
    "3. Daily Total Energy Consumption, Peak Demand, and Effective Tariff Rate",
    "4. Top 20 Facility Peak Demand Intervals at Main Incomer (Coincidental Demand)",
    "5. Production Batch Energy Intensity (SEC) by Machine",
    "6. Time-of-Use (TOU) Tariff Cost Distribution & Expense Breakdown",
    "7. Shift-by-Shift Energy Productivity & Cost-Per-Unit Comparison",
    "8. Abnormal Machine Consumption & Nominal Operating Power Deviation",
    "9. Actionable Energy-Saving Interventions by Expected ROI & Payback",
    "10. Facility-Wide Cost Reduction Potential & Category Portfolio Summary"
]

QUERY_SLUGS = [
    "top_consuming_machines",
    "machine_idle_waste",
    "daily_energy_consumption",
    "peak_demand_intervals",
    "batch_energy_intensity",
    "tou_tariff_distribution",
    "shift_energy_productivity",
    "abnormal_machine_consumption",
    "energy_saving_interventions",
    "portfolio_summary"
]

def run_sql_analysis(db_path: Optional[Path] = None, export_files: bool = True):
    target_db = db_path or config.DB_PATH
    if not target_db.exists():
        raise FileNotFoundError(
            f"Database file '{target_db}' does not exist. "
            "Run main.py --generate to initialize and populate it."
        )

    print("=" * 80)
    print("YOTTAFLEX INDUSTRIAL ENERGY ANALYTICS - PRODUCTION SQL QUERY SUITE")
    print(f"Database: {target_db.name} | Size: {target_db.stat().st_size / (1024*1024):.2f} MB")
    print("=" * 80)

    db = DatabaseManager(target_db)
    query_file = config.SQL_DIR / "analysis_queries.sql"
    with open(query_file, "r", encoding="utf-8") as f:
        content = f.read()

    query_blocks = []
    for i in range(1, 11):
        start_tag = f"-- QUERY_{i}_START"
        end_tag = f"-- QUERY_{i}_END"
        if start_tag in content and end_tag in content:
            sql_text = content.split(start_tag)[1].split(end_tag)[0].strip()
            query_blocks.append((i, sql_text))

    if len(query_blocks) != 10:
        raise ValueError(f"Expected 10 analytical queries, found {len(query_blocks)}.")

    summary_records = []
    analytics_dirs = [config.ROOT_OUTPUTS_DIR / "analytics_results", config.OUTPUTS_DIR / "analytics_results"]
    if export_files:
        for out_dir in analytics_dirs:
            out_dir.mkdir(parents=True, exist_ok=True)

    for q_num, sql in query_blocks:
        title = QUERY_TITLES[q_num - 1] if q_num <= len(QUERY_TITLES) else f"Query #{q_num}"
        slug = QUERY_SLUGS[q_num - 1] if q_num <= len(QUERY_SLUGS) else f"query_{q_num}"
        print(f"\n[QUERY {q_num}/10] {title}")
        print("-" * 80)
        results = db.execute_query(sql)
        print(f"Total Rows Returned: {len(results)}")
        if results:
            headers = list(results[0].keys())
            header_line = " | ".join(f"{h:<22}" for h in headers[:6])
            print(header_line)
            print("-" * len(header_line))
            for row in results[:5]:
                row_vals = [str(row[h]) if row[h] is not None else "NULL" for h in headers[:6]]
                print(" | ".join(f"{v:<22}" for v in row_vals))
            if len(results) > 5:
                print(f"  ... [{len(results) - 5} additional rows]")

            if export_files:
                csv_filename = f"query_{q_num}_{slug}.csv"
                for out_dir in analytics_dirs:
                    csv_path = out_dir / csv_filename
                    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=headers)
                        writer.writeheader()
                        writer.writerows(results)
        else:
            raise RuntimeError(f"Query #{q_num} returned no rows.")

        summary_records.append({
            "query_number": q_num,
            "title": title,
            "slug": slug,
            "row_count": len(results),
            "columns": list(results[0].keys()),
            "status": "SUCCESS"
        })

    if export_files:
        summary_payload = {
            "total_queries": len(query_blocks),
            "successful_queries": len(summary_records),
            "queries": summary_records
        }
        for out_dir in analytics_dirs:
            with open(out_dir / "sql_analytics_summary.json", "w", encoding="utf-8") as f:
                json.dump(summary_payload, f, indent=2)

    print("\n" + "=" * 80)
    print("ALL 10 ANALYTICAL QUERIES EXECUTED SUCCESSFULLY & EXPORTED")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    run_sql_analysis()
