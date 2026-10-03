const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("testtrace_token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("testtrace_token", token);
  } else {
    localStorage.removeItem("testtrace_token");
  }
}

export function getUser() {
  const raw = localStorage.getItem("testtrace_user");
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setUser(user) {
  if (user) {
    localStorage.setItem("testtrace_user", JSON.stringify(user));
  } else {
    localStorage.removeItem("testtrace_user");
  }
}

export async function apiRequest(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    ...options.headers,
  };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errMessage = "Request failed";
    try {
      const errData = await response.json();
      errMessage = errData.detail || errData.message || errMessage;
    } catch {
      errMessage = `HTTP error ${response.status}`;
    }
    throw new Error(errMessage);
  }

  return response.json();
}
