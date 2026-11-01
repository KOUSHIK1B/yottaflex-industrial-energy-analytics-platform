 import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import fs from 'fs';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { fileURLToPath } from 'url';

const execFilePromise = promisify(execFile);
const app = express();
const portSetting = process.env.PORT;
const PORT = portSetting ? Number(portSetting) : 3000;
if (!Number.isInteger(PORT) || PORT < 1 || PORT > 65535) {
  throw new RangeError(`PORT must be an integer between 1 and 65535; received '${portSetting}'.`);
}
const isProd = process.env.NODE_ENV === 'production';
const ROOT_DIR = path.dirname(fileURLToPath(import.meta.url));
const PYTHON_EXECUTABLE = process.env.PYTHON_EXECUTABLE ?? path.join(
  ROOT_DIR,
  '.venv',
  process.platform === 'win32' ? 'Scripts' : 'bin',
  process.platform === 'win32' ? 'python.exe' : 'python',
);
const DATABASE_PATH = path.join(ROOT_DIR, 'database', 'energy_analytics.db');

app.use(express.json());

// Helper to parse CSV to array of objects
type CsvValue = string | number;

function parseCsv(filePath: string): Record<string, CsvValue>[] {
  if (!fs.existsSync(filePath)) return [];
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.replace(/^\uFEFF/, '').split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) return [];

  const parseRow = (line: string): string[] => {
    const values: string[] = [];
    let value = '';
    let insideQuote = false;

    for (let index = 0; index < line.length; index += 1) {
      const character = line[index];
      if (character === '"') {
        if (insideQuote && line[index + 1] === '"') {
          value += '"';
          index += 1;
        } else {
          insideQuote = !insideQuote;
        }
      } else if (character === ',' && !insideQuote) {
        values.push(value);
        value = '';
      } else {
        value += character;
      }
    }

    values.push(value);
    return values;
  };

  const headers = parseRow(lines[0]).map(header => header.trim());
  return lines.slice(1).map(line => {
    const values = parseRow(line);
    const row: Record<string, CsvValue> = {};
    headers.forEach((h, idx) => {
      const value = values[idx] ?? '';
      const numericValue = Number(value);
      row[h] = value.trim() !== '' && Number.isFinite(numericValue) ? numericValue : value;
    });
    return row;
  });
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function getNumericField(row: Record<string, CsvValue>, field: string): number {
  const value = row[field];
  return typeof value === 'number' ? value : 0;
}

function getPythonUnavailableMessage(): string | null {
  return fs.existsSync(PYTHON_EXECUTABLE)
    ? null
    : `Configured Python executable was not found: ${PYTHON_EXECUTABLE}`;
}

function getProcessErrorOutput(error: unknown): string {
  if (error && typeof error === 'object' && 'stdout' in error) {
    const output = error.stdout;
    if (typeof output === 'string' || Buffer.isBuffer(output)) {
      return output.toString();
    }
  }
  return getErrorMessage(error);
}

// API Routes
app.get('/api/status', (req, res) => {
  const valPath = path.join(ROOT_DIR, 'data', 'outputs', 'validation_report.json');
  
  const dbExists = fs.existsSync(DATABASE_PATH);
  const dbSizeMb = dbExists ? (fs.statSync(DATABASE_PATH).size / (1024 * 1024)).toFixed(2) : '0';
  let validation = fs.existsSync(valPath) ? JSON.parse(fs.readFileSync(valPath, 'utf-8')) : null;

  res.json({
    status: 'ONLINE',
    plantId: 'PLT-001',
    plantName: 'YottaFlex Precision Metals & Robotics Plant #1',
    seed: 20261022,
    windowDays: 90,
    intervalMinutes: 15,
    dbExists,
    dbSizeMb: `${dbSizeMb} MB`,
    validationSummary: validation ? validation.summary : null,
  });
});

app.get('/api/kpi', (req, res) => {
  const daily = parseCsv(path.join(ROOT_DIR, 'data', 'outputs', 'energy_analytics.csv'));
  const machines = parseCsv(path.join(ROOT_DIR, 'data', 'outputs', 'machine_performance.csv'));
  const valPath = path.join(ROOT_DIR, 'data', 'outputs', 'validation_report.json');
  const validation = fs.existsSync(valPath) ? JSON.parse(fs.readFileSync(valPath, 'utf-8')) : null;

  const totalKwh = daily.reduce((acc, row) => acc + getNumericField(row, 'daily_total_kwh'), 0);
  const totalCostUsd = daily.reduce((acc, row) => acc + getNumericField(row, 'daily_cost_usd'), 0);
  const maxDemandKw = daily.reduce(
    (max, row) => Math.max(max, getNumericField(row, 'daily_peak_demand_kw')),
    0,
  );
  const totalGoodUnits = machines.reduce((acc, row) => acc + getNumericField(row, 'total_good_units'), 0);
  const totalIdleCost = machines.reduce((acc, row) => acc + getNumericField(row, 'idle_wasted_cost_usd'), 0);
  const totalIdleKwh = machines.reduce((acc, row) => acc + getNumericField(row, 'idle_wasted_kwh'), 0);

  res.json({
    totalEnergyKwh: Math.round(totalKwh),
    totalCostUsd: Math.round(totalCostUsd),
    facilityPeakDemandKw: Math.round(maxDemandKw * 100) / 100,
    totalGoodUnitsProduced: totalGoodUnits,
    averageFacilitySec: totalGoodUnits > 0 ? (totalKwh / totalGoodUnits).toFixed(4) : '0.0000',
    totalIdleWastedKwh: Math.round(totalIdleKwh),
    totalIdleCostUsd: Math.round(totalIdleCost),
    anomaliesCount: validation?.summary?.injected_ground_truth_count ?? 0,
    validationPassedRatio: validation
      ? `${validation.summary.passed_checks}/${validation.summary.total_checks}`
      : 'Unavailable',
  });
});

app.get('/api/daily', (req, res) => {
  const data = parseCsv(path.join(ROOT_DIR, 'data', 'outputs', 'energy_analytics.csv'));
  res.json(data);
});

app.get('/api/machines', (req, res) => {
  const data = parseCsv(path.join(ROOT_DIR, 'data', 'outputs', 'machine_performance.csv'));
  res.json(data);
});

app.get('/api/anomalies', (req, res) => {
  const gtPath = path.join(ROOT_DIR, 'data', 'ground_truth', 'ground_truth.json');
  if (fs.existsSync(gtPath)) {
    res.json(JSON.parse(fs.readFileSync(gtPath, 'utf-8')));
  } else {
    res.json(parseCsv(path.join(ROOT_DIR, 'data', 'ground_truth', 'ground_truth.csv')));
  }
});

app.get('/api/validation', (req, res) => {
  const valPath = path.join(ROOT_DIR, 'data', 'outputs', 'validation_report.json');
  if (fs.existsSync(valPath)) {
    res.json(JSON.parse(fs.readFileSync(valPath, 'utf-8')));
  } else {
    res.status(404).json({ error: 'Validation report not generated yet' });
  }
});

app.get('/api/recommendations', (req, res) => {
  const data = parseCsv(path.join(ROOT_DIR, 'data', 'outputs', 'recommendations.csv'));
  res.json(data);
});

app.get('/api/queries', (req, res) => {
  const queryFile = path.join(ROOT_DIR, 'sql', 'analysis_queries.sql');
  if (!fs.existsSync(queryFile)) return res.json([]);
  const content = fs.readFileSync(queryFile, 'utf-8');

  const titles = [
    '1. Machine Energy Consumption Ranking',
    '2. Highest Idle Consumption & Standby Waste',
    '3. 90-Day Daily Consumption & Peak Trends',
    '4. Top 20 Facility Peak Demand Intervals',
    '5. Energy Intensity (SEC) per Good Unit Produced',
    '6. TOU Tariff Cost Breakdown & Spend Analysis',
    '7. Shift Energy Consumption Comparison',
    '8. Abnormal Machine Consumption & Nominal Deviation',
    '9. Top Actionable Energy-Saving Interventions',
    '10. Facility-Wide Cost Reduction Potential & Payback'
  ];

  const queries: { id: number; title: string; sql: string }[] = [];
  for (let i = 1; i <= 10; i++) {
    const startTag = `-- QUERY_${i}_START`;
    const endTag = `-- QUERY_${i}_END`;
    if (content.includes(startTag) && content.includes(endTag)) {
      const sql = content.split(startTag)[1].split(endTag)[0].trim();
      queries.push({
        id: i,
        title: titles[i - 1] || `Query #${i}`,
        sql,
      });
    }
  }
  res.json(queries);
});

// Run live SQL query against database
app.post('/api/query', async (req, res) => {
  const body: unknown = req.body;
  if (!body || typeof body !== 'object' || !('query' in body) || typeof body.query !== 'string' || !body.query.trim()) {
    return res.status(400).json({ error: 'SQL query string is required' });
  }
  const query = body.query;

  if (!fs.existsSync(DATABASE_PATH)) {
    return res.status(503).json({ error: 'Analytics database has not been generated yet.' });
  }
  const pythonError = getPythonUnavailableMessage();
  if (pythonError) return res.status(503).json({ error: pythonError });

  const startTime = Date.now();
  try {
    const script = `
import json
import sqlite3
import sys

query, database_path = sys.argv[1:]
conn = sqlite3.connect(database_path)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA query_only = ON")

allowed_actions = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
}

def authorize(action, arg1, arg2, database_name, trigger_name):
    return sqlite3.SQLITE_OK if action in allowed_actions else sqlite3.SQLITE_DENY

conn.set_authorizer(authorize)
try:
    cursor = conn.execute(query)
    rows = cursor.fetchmany(501)
    print(json.dumps({
        "success": True,
        "rows": [dict(row) for row in rows[:500]],
        "count": min(len(rows), 500),
        "truncated": len(rows) > 500,
    }))
except sqlite3.Error as error:
    print(json.dumps({"success": False, "error": str(error)}))
finally:
    conn.close()
`;
    const { stdout } = await execFilePromise(
      PYTHON_EXECUTABLE,
      ['-c', script, query, DATABASE_PATH],
      { cwd: ROOT_DIR, maxBuffer: 20 * 1024 * 1024 },
    );
    const durationMs = Date.now() - startTime;
    const result = JSON.parse(String(stdout).trim());
    
    if (result.success) {
      res.json({
        success: true,
        rows: result.rows,
        rowCount: result.count,
        truncated: result.truncated,
        durationMs,
      });
    } else {
      res.status(400).json({
        success: false,
        error: result.error,
        durationMs,
      });
    }
  } catch (err: unknown) {
    res.status(500).json({
      success: false,
      error: getErrorMessage(err),
      durationMs: Date.now() - startTime,
    });
  }
});

// Run pipeline CLI command
app.post('/api/run-pipeline', async (req, res) => {
  const pythonError = getPythonUnavailableMessage();
  if (pythonError) return res.status(503).json({ success: false, error: pythonError });

  try {
    const { stdout } = await execFilePromise(
      PYTHON_EXECUTABLE,
      ['main.py', '--all'],
      { cwd: ROOT_DIR, maxBuffer: 20 * 1024 * 1024 },
    );
    res.json({ success: true, output: String(stdout) });
  } catch (err: unknown) {
    res.status(500).json({ success: false, error: getProcessErrorOutput(err) });
  }
});

// Run pytest suite
app.post('/api/run-tests', async (req, res) => {
  const pythonError = getPythonUnavailableMessage();
  if (pythonError) return res.status(503).json({ success: false, error: pythonError });

  try {
    const { stdout } = await execFilePromise(
      PYTHON_EXECUTABLE,
      ['-m', 'pytest', '-v'],
      { cwd: ROOT_DIR, maxBuffer: 20 * 1024 * 1024 },
    );
    res.json({ success: true, output: String(stdout) });
  } catch (err: unknown) {
    res.status(500).json({ success: false, error: getProcessErrorOutput(err) });
  }
});

async function startServer() {
  if (!isProd) {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.join(ROOT_DIR, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.join(ROOT_DIR, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server listening on port ${PORT}`);
  });
}

startServer();
