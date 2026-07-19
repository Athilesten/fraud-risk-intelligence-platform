import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  DataTable,
  ErrorBanner,
  LoadingState,
  MetricCard,
  Navbar,
  SectionHeader,
  StatusCard,
} from "./components/ui.jsx";
import {
  API_BASE_URL,
  AUTH_ENABLED,
  checkHealth,
  clearToken,
  fetchDataLakeSummary,
  fetchCurrentUser,
  fetchMonitoringMetrics,
  fetchPredictionLogs,
  fetchRecentScored,
  fetchStreamingStatus,
  getApiError,
  getStoredToken,
  login,
  predictBatch,
  predictTransaction,
} from "./services/api.js";
import "./App.css";

const requiredColumns = [
  "step",
  "type",
  "amount",
  "oldbalanceOrg",
  "newbalanceOrig",
  "oldbalanceDest",
  "newbalanceDest",
  "isFlaggedFraud",
];

const defaultTransaction = {
  step: 1,
  type: "TRANSFER",
  amount: 250000,
  oldbalanceOrg: 250000,
  newbalanceOrig: 0,
  oldbalanceDest: 0,
  newbalanceDest: 250000,
  isFlaggedFraud: 1,
};

function toPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(2)}%`;
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean);

  if (lines.length < 2) {
    throw new Error("CSV must include a header row and at least one transaction.");
  }

  const headers = lines[0].split(",").map((header) => header.trim());
  const missingColumns = requiredColumns.filter((column) => !headers.includes(column));

  if (missingColumns.length) {
    throw new Error(`Missing required columns: ${missingColumns.join(", ")}`);
  }

  return lines.slice(1).map((line) => {
    const values = line.split(",").map((value) => value.trim());
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index]]));

    return {
      step: Number(row.step),
      type: String(row.type).toUpperCase(),
      amount: Number(row.amount),
      oldbalanceOrg: Number(row.oldbalanceOrg),
      newbalanceOrig: Number(row.newbalanceOrig),
      oldbalanceDest: Number(row.oldbalanceDest),
      newbalanceDest: Number(row.newbalanceDest),
      isFlaggedFraud: Number(row.isFlaggedFraud),
    };
  });
}

function riskTone(riskLevel) {
  if (riskLevel === "HIGH") return "danger";
  if (riskLevel === "MEDIUM") return "warning";
  return "success";
}

function App() {
  const [health, setHealth] = useState("checking");
  const [transaction, setTransaction] = useState(defaultTransaction);
  const [prediction, setPrediction] = useState(null);
  const [batchResults, setBatchResults] = useState([]);
  const [logs, setLogs] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [streamingStatus, setStreamingStatus] = useState(null);
  const [recentScored, setRecentScored] = useState([]);
  const [dataLakeSummary, setDataLakeSummary] = useState(null);
  const [user, setUser] = useState(null);
  const [loginForm, setLoginForm] = useState({
    email: "admin@fraud.local",
    password: "admin123",
  });
  const [loading, setLoading] = useState({
    prediction: false,
    batch: false,
    logs: false,
    metrics: false,
    bigData: false,
    login: false,
  });
  const [error, setError] = useState("");

  useEffect(() => {
    refreshHealth();
    refreshCurrentUser();
  }, []);

  async function refreshCurrentUser() {
    if (!AUTH_ENABLED || !getStoredToken()) return;

    try {
      const response = await fetchCurrentUser();
      setUser(response);
    } catch {
      clearToken();
      setUser(null);
    }
  }

  async function runLogin(event) {
    event.preventDefault();
    setError("");
    setLoading((current) => ({ ...current, login: true }));

    try {
      const response = await login(loginForm.email, loginForm.password);
      setUser(response.user);
    } catch (err) {
      setError(getApiError(err, "Login failed."));
    } finally {
      setLoading((current) => ({ ...current, login: false }));
    }
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  const logSummary = useMemo(() => {
    const high = logs.filter((log) => log.risk_level === "HIGH").length;
    const medium = logs.filter((log) => log.risk_level === "MEDIUM").length;
    const low = logs.filter((log) => log.risk_level === "LOW").length;

    return { high, medium, low, total: logs.length };
  }, [logs]);

  const riskDistribution = useMemo(() => {
    const counts = logs.reduce((accumulator, log) => {
      const risk = log.risk_level || "UNKNOWN";
      accumulator[risk] = (accumulator[risk] || 0) + 1;
      return accumulator;
    }, {});

    return Object.entries(counts).map(([risk, count]) => ({ risk, count }));
  }, [logs]);

  const batchSummary = useMemo(() => {
    const high = batchResults.filter((row) => row.risk_level === "HIGH").length;
    const medium = batchResults.filter((row) => row.risk_level === "MEDIUM").length;
    const low = batchResults.filter((row) => row.risk_level === "LOW").length;

    return { high, medium, low, total: batchResults.length };
  }, [batchResults]);

  async function refreshHealth() {
    setHealth("checking");

    try {
      await checkHealth();
      setHealth("healthy");
    } catch {
      setHealth("down");
    }
  }

  function updateTransaction(field, value) {
    setTransaction((current) => ({
      ...current,
      [field]: field === "type" ? value : Number(value),
    }));
  }

  async function runPrediction() {
    setError("");
    setLoading((current) => ({ ...current, prediction: true }));

    try {
      const response = await predictTransaction(transaction);
      setPrediction(response);
    } catch (err) {
      setPrediction(null);
      setError(getApiError(err, "Prediction failed."));
    } finally {
      setLoading((current) => ({ ...current, prediction: false }));
    }
  }

  async function uploadBatch(event) {
    setError("");
    setBatchResults([]);
    setLoading((current) => ({ ...current, batch: true }));

    const file = event.target.files?.[0];

    if (!file) {
      setLoading((current) => ({ ...current, batch: false }));
      return;
    }

    try {
      const text = await file.text();
      const transactions = parseCsv(text).slice(0, 100);
      const response = await predictBatch(transactions);
      setBatchResults(response.results || []);
    } catch (err) {
      setError(getApiError(err, "Batch scoring failed."));
    } finally {
      setLoading((current) => ({ ...current, batch: false }));
      event.target.value = "";
    }
  }

  async function loadLogs() {
    setError("");
    setLoading((current) => ({ ...current, logs: true }));

    try {
      const response = await fetchPredictionLogs(20);
      setLogs(response.logs || []);
    } catch (err) {
      setError(getApiError(err, "Could not load prediction logs."));
    } finally {
      setLoading((current) => ({ ...current, logs: false }));
    }
  }

  async function loadMetrics() {
    setError("");
    setLoading((current) => ({ ...current, metrics: true }));

    try {
      const response = await fetchMonitoringMetrics();
      setMetrics(response);
    } catch (err) {
      setError(getApiError(err, "Could not load monitoring metrics."));
    } finally {
      setLoading((current) => ({ ...current, metrics: false }));
    }
  }

  async function loadBigDataStatus() {
    setError("");
    setLoading((current) => ({ ...current, bigData: true }));

    try {
      const [statusResponse, scoredResponse, lakeResponse] = await Promise.all([
        fetchStreamingStatus(),
        fetchRecentScored(20),
        fetchDataLakeSummary(),
      ]);
      setStreamingStatus(statusResponse);
      setRecentScored(scoredResponse.records || []);
      setDataLakeSummary(lakeResponse);
    } catch (err) {
      setError(getApiError(err, "Could not load streaming or data lake status."));
    } finally {
      setLoading((current) => ({ ...current, bigData: false }));
    }
  }

  const batchColumns = [
    { key: "type", label: "Type" },
    { key: "amount", label: "Amount" },
    { key: "fraud_probability", label: "Probability", render: (row) => toPercent(row.fraud_probability) },
    { key: "risk_level", label: "Risk" },
    { key: "rule_risk_score", label: "Rule Score" },
    { key: "final_decision", label: "Decision" },
  ];

  const logColumns = [
    { key: "id", label: "ID" },
    { key: "transaction_type", label: "Type" },
    { key: "amount", label: "Amount" },
    { key: "fraud_probability", label: "Probability", render: (row) => toPercent(row.fraud_probability) },
    { key: "risk_level", label: "Risk" },
    { key: "rule_risk_score", label: "Rule Score" },
    { key: "final_decision", label: "Decision" },
  ];

  const endpointColumns = [
    { key: "endpoint", label: "Endpoint" },
    { key: "requests", label: "Requests" },
    { key: "errors", label: "Errors" },
    { key: "avg_latency_ms", label: "Avg Latency", render: (row) => `${row.avg_latency_ms} ms` },
    { key: "max_latency_ms", label: "Max Latency", render: (row) => `${row.max_latency_ms} ms` },
  ];

  const scoredColumns = [
    { key: "event_id", label: "Event ID" },
    { key: "type", label: "Type" },
    { key: "amount", label: "Amount" },
    { key: "fraud_probability", label: "Probability", render: (row) => toPercent(row.fraud_probability) },
    { key: "risk_level", label: "Risk" },
    { key: "rule_risk_score", label: "Rule Score" },
    { key: "final_decision", label: "Decision" },
  ];

  const typeDistributionColumns = [
    { key: "type", label: "Transaction Type" },
    { key: "count", label: "Count" },
  ];

  return (
    <div className="app-shell">
      <Navbar />
      <ErrorBanner message={error} />

      <main>
        {AUTH_ENABLED && !user && (
          <section className="section-card access-panel" id="access">
            <SectionHeader
              eyebrow="Secure Access"
              title="Platform Login"
              description="Use local demo credentials to access protected scoring, logs, monitoring, and streaming endpoints."
            />
            <form className="login-form" onSubmit={runLogin}>
              <label>Email<input type="email" value={loginForm.email} onChange={(event) => setLoginForm((current) => ({ ...current, email: event.target.value }))} /></label>
              <label>Password<input type="password" value={loginForm.password} onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))} /></label>
              <button className="button primary" type="submit" disabled={loading.login}>
                {loading.login ? "Signing in..." : "Sign In"}
              </button>
            </form>
          </section>
        )}

        {AUTH_ENABLED && user && (
          <div className="access-strip">
            <span>Signed in as {user.email || user.subject}</span>
            <button className="button ghost small" onClick={logout}>Sign Out</button>
          </div>
        )}

        {(!AUTH_ENABLED || user) && (
          <>
        <section className="overview-grid" id="overview">
          <div className="hero-panel">
            <p className="eyebrow">Real-Time Fraud Detection</p>
            <h1>Fraud Risk Intelligence Platform</h1>
            <p>
              A production-style fintech risk platform for transaction scoring,
              rule-based decisioning, audit logging, and operational monitoring.
            </p>
            <div className="hero-actions">
              <a className="button primary" href="#predict">Score Transaction</a>
              <a className="button secondary" href={`${API_BASE_URL}/docs`} target="_blank" rel="noreferrer">
                API Docs
              </a>
            </div>
          </div>
          <StatusCard health={health} onRefresh={refreshHealth} />
        </section>

        <section className="module-grid" aria-label="Key modules">
          <MetricCard label="ML Scoring" value="FastAPI" />
          <MetricCard label="Rule Engine" value="Explainable" />
          <MetricCard label="Audit Logs" value="PostgreSQL" />
          <MetricCard label="Monitoring" value="Prometheus" />
        </section>

        <section className="section-card" id="predict">
          <SectionHeader
            eyebrow="Transaction Scoring"
            title="Fraud Prediction"
            description="Score a single transaction through the FastAPI ML model and rule engine."
          />

          <div className="prediction-layout">
            <div className="form-grid">
              <label>Step<input type="number" value={transaction.step} onChange={(event) => updateTransaction("step", event.target.value)} /></label>
              <label>Type<select value={transaction.type} onChange={(event) => updateTransaction("type", event.target.value)}>
                <option>CASH_IN</option>
                <option>CASH_OUT</option>
                <option>DEBIT</option>
                <option>PAYMENT</option>
                <option>TRANSFER</option>
              </select></label>
              <label>Amount<input type="number" value={transaction.amount} onChange={(event) => updateTransaction("amount", event.target.value)} /></label>
              <label>Sender Old Balance<input type="number" value={transaction.oldbalanceOrg} onChange={(event) => updateTransaction("oldbalanceOrg", event.target.value)} /></label>
              <label>Sender New Balance<input type="number" value={transaction.newbalanceOrig} onChange={(event) => updateTransaction("newbalanceOrig", event.target.value)} /></label>
              <label>Receiver Old Balance<input type="number" value={transaction.oldbalanceDest} onChange={(event) => updateTransaction("oldbalanceDest", event.target.value)} /></label>
              <label>Receiver New Balance<input type="number" value={transaction.newbalanceDest} onChange={(event) => updateTransaction("newbalanceDest", event.target.value)} /></label>
              <label>System Flagged Fraud<select value={transaction.isFlaggedFraud} onChange={(event) => updateTransaction("isFlaggedFraud", event.target.value)}>
                <option value={0}>0</option>
                <option value={1}>1</option>
              </select></label>
              <button className="button primary wide" onClick={runPrediction} disabled={loading.prediction}>
                {loading.prediction ? "Scoring..." : "Predict Fraud Risk"}
              </button>
            </div>

            <div className="result-panel">
              {loading.prediction && <LoadingState label="Scoring transaction" />}
              {!loading.prediction && !prediction && <p className="empty-state">Run a prediction to see risk, rules, and model explanation.</p>}
              {!loading.prediction && prediction && (
                <>
                  <div className="metric-grid">
                    <MetricCard label="Fraud Probability" value={toPercent(prediction.prediction.fraud_probability)} tone={riskTone(prediction.prediction.risk_level)} />
                    <MetricCard label="Risk Level" value={prediction.prediction.risk_level} tone={riskTone(prediction.prediction.risk_level)} />
                    <MetricCard label="Rule Risk Score" value={`${prediction.prediction.rule_risk_score}/100`} />
                    <MetricCard label="Final Decision" value={prediction.prediction.final_decision} />
                  </div>

                  <div className="detail-block">
                    <h3>Triggered Fraud Rules</h3>
                    {prediction.prediction.triggered_rules?.length ? (
                      <ul>
                        {prediction.prediction.triggered_rules.map((rule) => <li key={rule}>{rule}</li>)}
                      </ul>
                    ) : (
                      <p>No fraud rule triggered.</p>
                    )}
                  </div>

                  <div className="detail-block">
                    <h3>Model Explanation</h3>
                    {prediction.explanation?.top_features?.length ? (
                      <DataTable
                        columns={[
                          { key: "feature", label: "Feature" },
                          { key: "feature_value", label: "Value" },
                          { key: "impact_score", label: "Impact", render: (row) => Number(row.impact_score).toFixed(4) },
                        ]}
                        rows={prediction.explanation.top_features}
                      />
                    ) : (
                      <p>No explanation returned by the model service.</p>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        </section>

        <section className="section-card" id="batch">
          <SectionHeader
            eyebrow="CSV Scoring"
            title="Batch Prediction"
            description="Upload a PaySim-style CSV. The frontend validates required columns and scores up to 100 rows."
          />
          <input className="file-input" type="file" accept=".csv" onChange={uploadBatch} />
          {loading.batch && <LoadingState label="Scoring batch" />}
          {batchResults.length > 0 && (
            <>
              <div className="module-grid compact">
                <MetricCard label="Rows Scored" value={batchSummary.total} />
                <MetricCard label="High Risk" value={batchSummary.high} tone="danger" />
                <MetricCard label="Medium Risk" value={batchSummary.medium} tone="warning" />
                <MetricCard label="Low Risk" value={batchSummary.low} tone="success" />
              </div>
              <DataTable columns={batchColumns} rows={batchResults.slice(0, 20)} />
            </>
          )}
        </section>

        <section className="section-card" id="logs">
          <SectionHeader
            eyebrow="Audit Trail"
            title="Prediction Logs"
            description="Load real recent prediction records from PostgreSQL through FastAPI."
          />
          <button className="button secondary" onClick={loadLogs} disabled={loading.logs}>
            {loading.logs ? "Loading..." : "Load Recent Logs"}
          </button>

          {logs.length > 0 && (
            <>
              <div className="module-grid compact">
                <MetricCard label="Recent Records" value={logSummary.total} />
                <MetricCard label="High Risk" value={logSummary.high} tone="danger" />
                <MetricCard label="Medium Risk" value={logSummary.medium} tone="warning" />
                <MetricCard label="Low Risk" value={logSummary.low} tone="success" />
              </div>
              <div className="chart-card">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={riskDistribution}>
                    <XAxis dataKey="risk" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <DataTable columns={logColumns} rows={logs} />
            </>
          )}
        </section>

        <section className="section-card" id="monitoring">
          <SectionHeader
            eyebrow="Operations"
            title="Monitoring"
            description="Fetch real API request metrics and endpoint-level latency from the FastAPI monitoring store."
          />
          <div className="toolbar">
            <button className="button secondary" onClick={loadMetrics} disabled={loading.metrics}>
              {loading.metrics ? "Loading..." : "Load API Metrics"}
            </button>
            <a className="button ghost" href="http://localhost:3000" target="_blank" rel="noreferrer">
              Open Grafana
            </a>
          </div>

          {metrics && (
            <>
              <div className="module-grid compact">
                <MetricCard label="Total Requests" value={metrics.total_requests} />
                <MetricCard label="Total Errors" value={metrics.total_errors} tone={metrics.total_errors ? "danger" : "success"} />
                <MetricCard label="Average Latency" value={`${metrics.avg_latency_ms} ms`} />
                <MetricCard label="Max Latency" value={`${metrics.max_latency_ms} ms`} />
              </div>
              <DataTable columns={endpointColumns} rows={metrics.by_endpoint || []} />
            </>
          )}
        </section>

        <section className="section-card" id="big-data">
          <SectionHeader
            eyebrow="Streaming Intelligence"
            title="Big Data Pipeline"
            description="Inspect Kafka scoring artifacts and Delta Lake table status produced by the local streaming pipeline."
          />
          <button className="button secondary" onClick={loadBigDataStatus} disabled={loading.bigData}>
            {loading.bigData ? "Refreshing..." : "Refresh Big Data Status"}
          </button>

          {streamingStatus && (
            <>
              <div className="module-grid compact">
                <MetricCard label="Kafka Raw Topic" value={streamingStatus.kafka?.raw_topic || "transactions.raw"} />
                <MetricCard label="Kafka Scored Topic" value={streamingStatus.kafka?.scored_topic || "transactions.scored"} />
                <MetricCard label="FastAPI Scoring" value={streamingStatus.fastapi_scoring?.status || "available"} tone="success" />
                <MetricCard
                  label="Data Lake"
                  value={streamingStatus.data_lake?.available ? "Available" : "Not Started"}
                  tone={streamingStatus.data_lake?.available ? "success" : "warning"}
                />
              </div>

              <div className="detail-block">
                <h3>Pipeline Status</h3>
                <div className="status-list two-column">
                  <span>Bootstrap: {streamingStatus.kafka?.bootstrap_servers}</span>
                  <span>Last refresh: {streamingStatus.last_refresh_time}</span>
                  <span>Latest event: {dataLakeSummary?.latest_event_timestamp || "not available"}</span>
                  <span>Latest ingestion: {dataLakeSummary?.latest_ingestion_timestamp || "not available"}</span>
                  <span>Scored log: {streamingStatus.kafka?.recent_scored_log?.exists ? "available" : "not created yet"}</span>
                  <span>Dead letters: {streamingStatus.kafka?.dead_letter_log?.exists ? "available" : "none found"}</span>
                </div>
              </div>

              <div className="module-grid compact">
                <MetricCard label="Bronze Rows" value={dataLakeSummary?.bronze_count || 0} />
                <MetricCard label="Silver Rows" value={dataLakeSummary?.silver_count || 0} />
                <MetricCard label="Gold Rows" value={dataLakeSummary?.gold_count || 0} />
                <MetricCard label="Scored Decisions" value={dataLakeSummary?.scored_gold_count || 0} />
              </div>

              {!dataLakeSummary?.available && (
                <div className="command-box">
                  <strong>Delta Lake empty state</strong>
                  <span>Run: python streaming\spark_streaming_delta_pipeline.py</span>
                </div>
              )}

              {dataLakeSummary?.transaction_type_distribution?.length > 0 && (
                <DataTable
                  columns={typeDistributionColumns}
                  rows={dataLakeSummary.transaction_type_distribution}
                />
              )}

              <SectionHeader
                eyebrow="Live Scored Events"
                title="Recent Kafka-Scored Transactions"
                description="These rows come from the streaming scorer consumer when it calls FastAPI and publishes enriched decisions."
              />
              <DataTable
                columns={scoredColumns}
                rows={recentScored}
                emptyMessage="No Kafka-scored transactions yet. Start Kafka, create topics, run the producer, then run the scoring consumer."
              />
            </>
          )}
        </section>

        <section className="section-card" id="architecture">
          <SectionHeader
            eyebrow="System Design"
            title="Architecture"
            description="Online scoring and streaming analytics are separated so the core product remains stable while the big-data pipeline scales independently."
          />
          <div className="architecture-flow">
            <span>React Frontend</span>
            <strong>-&gt;</strong>
            <span>FastAPI Scoring Service</span>
            <strong>-&gt;</strong>
            <span>ML Model + Rule Engine</span>
            <strong>-&gt;</strong>
            <span>PostgreSQL Audit Logs</span>
            <strong>-&gt;</strong>
            <span>Prometheus / Grafana</span>
          </div>
          <div className="architecture-flow">
            <span>Kafka Raw Topic</span>
            <strong>-&gt;</strong>
            <span>Kafka Scoring Consumer</span>
            <strong>-&gt;</strong>
            <span>Kafka Scored Topic</span>
            <strong>-&gt;</strong>
            <span>PySpark Structured Streaming</span>
            <strong>-&gt;</strong>
            <span>Delta Lake Bronze / Silver / Gold</span>
          </div>
          <p className="architecture-note">
            Streamlit remains available as an internal analyst dashboard at port 8501; the React website is the main product interface.
          </p>
        </section>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
