import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const API_KEY = import.meta.env.VITE_API_KEY || "";
export const AUTH_ENABLED = import.meta.env.VITE_ENABLE_AUTH === "true";
export const TOKEN_STORAGE_KEY = "fraud_risk_access_token";

export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function storeToken(token) {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  } else if (API_KEY) {
    config.headers["X-API-Key"] = API_KEY;
  }

  config.headers["Content-Type"] = "application/json";
  return config;
});

export function getApiError(error, fallbackMessage) {
  if (!API_KEY && error?.response?.status === 401) {
    return "Frontend API key is not configured. Set VITE_API_KEY for the React app.";
  }

  return (
    error?.response?.data?.detail ||
    error?.message ||
    fallbackMessage
  );
}

export async function checkHealth() {
  const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 5000 });
  return response.data;
}

export async function predictTransaction(transaction) {
  const response = await apiClient.post("/predict", transaction);
  return response.data;
}

export async function login(email, password) {
  const response = await axios.post(`${API_BASE_URL}/auth/login`, { email, password });
  storeToken(response.data.access_token);
  return response.data;
}

export async function fetchCurrentUser() {
  const response = await apiClient.get("/auth/me");
  return response.data;
}

export async function predictBatch(transactions) {
  const response = await apiClient.post("/predict_batch", { transactions });
  return response.data;
}

export async function fetchPredictionLogs(limit = 20) {
  const response = await apiClient.get(`/prediction_logs?limit=${limit}`);
  return response.data;
}

export async function fetchMonitoringMetrics() {
  const response = await apiClient.get("/monitoring/metrics");
  return response.data;
}

export async function fetchStreamingStatus() {
  const response = await apiClient.get("/streaming/status");
  return response.data;
}

export async function fetchRecentScored(limit = 20) {
  const response = await apiClient.get(`/streaming/recent-scored?limit=${limit}`);
  return response.data;
}

export async function fetchDataLakeSummary() {
  const response = await apiClient.get("/datalake/summary");
  return response.data;
}
