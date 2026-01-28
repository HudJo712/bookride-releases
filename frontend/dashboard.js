const state = {
  baseUrl: localStorage.getItem("br.baseUrl") || "/api",
  bearerToken: sessionStorage.getItem("br.bearerToken") || "",
  apiKey: localStorage.getItem("br.apiKey") || "dev-key-123",
  metricsSocket: null,
};

document.body.classList.add("hidden");

if (!state.bearerToken) {
  window.location.href = "index.html";
}

async function ensureDeveloperAccess() {
  if (!state.bearerToken) {
    return;
  }
  try {
    const response = await fetch(`${normalizeBaseUrl(state.baseUrl)}/access`, {
      headers: { Authorization: `Bearer ${state.bearerToken}` },
    });
    const payload = await response.json();
    if (!response.ok || payload?.role !== "developer") {
      localStorage.setItem("br.authMessage", "Control room access is restricted to developer accounts.");
      window.location.href = "index.html";
      return;
    }
    document.body.classList.remove("hidden");
  } catch (err) {
    localStorage.setItem("br.authMessage", "Unable to verify developer access.");
    window.location.href = "index.html";
  }
}

const outputMeta = document.getElementById("output-meta");
const outputBody = document.getElementById("output-body");
const activeRentals = document.getElementById("active-rentals");
const toggleMetrics = document.getElementById("toggle-metrics");
const logoutButton = document.getElementById("logout");

const baseUrlInput = document.getElementById("base-url");
const bearerInput = document.getElementById("bearer-token");
const apiKeyInput = document.getElementById("api-key");
const generatedApiKeyInput = document.getElementById("generated-api-key");
const apiKeyMeta = document.getElementById("api-key-meta");
const rememberApiKeyToggle = document.getElementById("remember-api-key");
const applyApiKeyButton = document.getElementById("apply-api-key");

baseUrlInput.value = state.baseUrl;
bearerInput.value = state.bearerToken;
apiKeyInput.value = state.apiKey;
if (generatedApiKeyInput && state.apiKey) {
  generatedApiKeyInput.value = state.apiKey;
  if (apiKeyMeta) {
    apiKeyMeta.textContent = "Using saved API key from this device.";
  }
}

function normalizeBaseUrl(url) {
  return url.replace(/\/$/, "");
}

function setOutput(meta, body) {
  outputMeta.textContent = meta;
  outputBody.textContent = body;
}

function formatHeaders(headers) {
  const entries = [];
  headers.forEach((value, key) => {
    entries.push(`${key}: ${value}`);
  });
  return entries.join("\n");
}

function stringifyJson(data) {
  return JSON.stringify(data, null, 2);
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/x-protobuf")) {
    const buffer = await response.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    let binary = "";
    bytes.forEach((b) => {
      binary += String.fromCharCode(b);
    });
    const base64 = btoa(binary);
    return `protobuf bytes (base64):\n${base64}`;
  }
  const text = await response.text();
  if (contentType.includes("application/json")) {
    try {
      return stringifyJson(JSON.parse(text));
    } catch (err) {
      return text;
    }
  }
  return text || "(empty body)";
}

async function request(path, options = {}) {
  const started = performance.now();
  const url = `${normalizeBaseUrl(state.baseUrl)}${path}`;
  try {
    const response = await fetch(url, options);
    const body = await parseResponse(response);
    const duration = Math.round(performance.now() - started);
    const meta = `Status: ${response.status} ${response.statusText} | ${duration}ms | ${url}\n${formatHeaders(response.headers)}`;
    setOutput(meta, body);
    return { response, body };
  } catch (error) {
    setOutput(`Request failed | ${url}`, error.message || String(error));
    throw error;
  }
}

function bearerHeaders() {
  if (!state.bearerToken) {
    return {};
  }
  return { Authorization: `Bearer ${state.bearerToken}` };
}

function apiKeyHeaders() {
  if (!state.apiKey) {
    return {};
  }
  return { "X-API-Key": state.apiKey };
}

function clearBearerToken() {
  state.bearerToken = "";
  bearerInput.value = "";
  sessionStorage.removeItem("br.bearerToken");
}

function setApiKey(key, persist) {
  if (!key) {
    return;
  }
  state.apiKey = key;
  apiKeyInput.value = key;
  if (persist) {
    localStorage.setItem("br.apiKey", key);
  } else {
    localStorage.removeItem("br.apiKey");
  }
}

function updateApiKeyMeta({ key, expiresAt, ttlSeconds }) {
  if (!apiKeyMeta) {
    return;
  }
  const currentKey = key || (generatedApiKeyInput ? generatedApiKeyInput.value.trim() : "");
  if (!currentKey) {
    apiKeyMeta.textContent = "No API key generated yet.";
    return;
  }
  let meta = "API key ready for this session.";
  if (expiresAt && ttlSeconds) {
    meta = `Expires ${expiresAt} (TTL ${ttlSeconds}s).`;
  } else if (expiresAt) {
    meta = `Expires ${expiresAt}.`;
  } else if (ttlSeconds) {
    meta = `TTL ${ttlSeconds}s.`;
  }
  apiKeyMeta.textContent = meta;
}

function saveConnection(event) {
  event.preventDefault();
  state.baseUrl = baseUrlInput.value.trim();
  state.bearerToken = bearerInput.value.trim();
  state.apiKey = apiKeyInput.value.trim();
  localStorage.setItem("br.baseUrl", state.baseUrl);
  sessionStorage.setItem("br.bearerToken", state.bearerToken);
  localStorage.setItem("br.apiKey", state.apiKey);
  if (generatedApiKeyInput && state.apiKey) {
    generatedApiKeyInput.value = state.apiKey;
    updateApiKeyMeta({ key: state.apiKey, expiresAt: "", ttlSeconds: "" });
  }
  setOutput("Saved connection settings.", "{}");
}

document.getElementById("connection-form").addEventListener("submit", saveConnection);

if (applyApiKeyButton) {
  applyApiKeyButton.addEventListener("click", () => {
    const key = generatedApiKeyInput ? generatedApiKeyInput.value.trim() : "";
    if (!key) {
      setOutput("No API key to apply yet.", "{}");
      return;
    }
    const persist = rememberApiKeyToggle ? rememberApiKeyToggle.checked : true;
    setApiKey(key, persist);
    updateApiKeyMeta({ key, expiresAt: "", ttlSeconds: "" });
    setOutput("Applied API key for rentals.", "{}");
  });
}

if (logoutButton) {
  logoutButton.addEventListener("click", () => {
    clearBearerToken();
    window.location.href = "index.html";
  });
}

document.getElementById("list-books").addEventListener("click", () => {
  request("/books", {
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("get-book-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const bookId = event.currentTarget.bookId.value;
  request(`/books/${bookId}`, {
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("create-book-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    id: Number(form.id.value),
    title: form.title.value.trim(),
    author: form.author.value.trim(),
    price: Number(form.price.value),
    in_stock: form.inStock.checked,
  };
  request("/books", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...bearerHeaders() },
    body: JSON.stringify(payload),
  });
});

document.getElementById("start-book-loan-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const confirmed = window.confirm("This will add €5 to your balance. Continue lending?");
  if (!confirmed) {
    setOutput("Book lending cancelled.", "{}");
    return;
  }
  const payload = {
    book_id: Number(event.currentTarget.bookId.value),
  };
  request("/book-loans/start", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...bearerHeaders() },
    body: JSON.stringify(payload),
  });
});

document.getElementById("stop-book-loan-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    loan_id: Number(event.currentTarget.loanId.value),
  };
  request("/book-loans/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...bearerHeaders() },
    body: JSON.stringify(payload),
  });
});

document.getElementById("list-book-loans").addEventListener("click", () => {
  request("/book-loans/active", {
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("create-bike-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    id: form.id.value.trim(),
    model: form.model.value.trim(),
    color: form.color.value.trim(),
    year: Number(form.year.value),
    rate_per_minute: Number(form.rate.value),
    price_cap_eur: Number(form.cap.value),
    is_active: form.isActive.checked,
  };
  request("/bikes", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...bearerHeaders() },
    body: JSON.stringify(payload),
  });
});

document.getElementById("list-bikes").addEventListener("click", () => {
  request("/bikes/all", {
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("list-available-bikes").addEventListener("click", () => {
  request("/bikes", {
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("delete-bike-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const bikeId = event.currentTarget.id.value.trim();
  if (!bikeId) {
    setOutput("Bike ID required for delete.", "{}");
    return;
  }
  request(`/bikes/${encodeURIComponent(bikeId)}`, {
    method: "DELETE",
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("start-rental-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    bike_id: event.currentTarget.bikeId.value.trim(),
  };
  request("/rentals/start", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...apiKeyHeaders() },
    body: JSON.stringify(payload),
  });
});

document.getElementById("stop-rental-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    rental_id: Number(event.currentTarget.rentalId.value),
  };
  request("/rentals/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...apiKeyHeaders() },
    body: JSON.stringify(payload),
  });
});

document.getElementById("start-rental-auth-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    bike_id: event.currentTarget.bikeId.value.trim(),
  };
  request("/rentals/start-auth", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...bearerHeaders() },
    body: JSON.stringify(payload),
  });
});

document.getElementById("stop-rental-auth-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const payload = {
    rental_id: Number(event.currentTarget.rentalId.value),
  };
  request("/rentals/stop-auth", {
    method: "POST",
    headers: { "Content-Type": "application/json", ...bearerHeaders() },
    body: JSON.stringify(payload),
  });
});

document.getElementById("list-rentals").addEventListener("click", () => {
  request("/rentals/active", {
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("create-partner-rental-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    id: Number(form.id.value),
    user_id: Number(form.userId.value),
    bike_id: form.bikeId.value.trim(),
    start_time: form.startTime.value.trim(),
    price_eur: Number(form.price.value),
  };
  const endTime = form.endTime.value.trim();
  if (endTime) {
    payload.end_time = endTime;
  }
  request("/rentals", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
});

document.getElementById("get-partner-rental-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const rentalId = event.currentTarget.rentalId.value;
  request(`/rentals/${rentalId}`);
});

document.getElementById("convert-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const target = form.target.value;
  let payload = {};
  try {
    payload = JSON.parse(form.payload.value);
  } catch (err) {
    setOutput("Payload must be valid JSON.", err.message || String(err));
    return;
  }
  request(`/convert?to=${encodeURIComponent(target)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
});

document.getElementById("ping-health").addEventListener("click", () => {
  request("/health");
});

document.getElementById("load-info").addEventListener("click", () => {
  request("/info");
});

document.getElementById("get-balance").addEventListener("click", () => {
  request("/balance", {
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("pay-balance").addEventListener("click", () => {
  request("/balance/pay", {
    method: "POST",
    headers: { ...bearerHeaders() },
  });
});

document.getElementById("get-access").addEventListener("click", () => {
  request("/access", {
    headers: { ...bearerHeaders() },
  });
});

function toWebSocketUrl(baseUrl) {
  if (baseUrl.startsWith("https://")) {
    return baseUrl.replace("https://", "wss://");
  }
  if (baseUrl.startsWith("http://")) {
    return baseUrl.replace("http://", "ws://");
  }
  return `ws://${baseUrl}`;
}

function connectMetrics() {
  const wsUrl = `${toWebSocketUrl(normalizeBaseUrl(state.baseUrl))}/ws/metrics`;
  state.metricsSocket = new WebSocket(wsUrl);
  state.metricsSocket.addEventListener("message", (event) => {
    try {
      const data = JSON.parse(event.data);
      activeRentals.textContent = String(data.active_rentals ?? "--");
    } catch (err) {
      activeRentals.textContent = "--";
    }
  });
  state.metricsSocket.addEventListener("close", () => {
    activeRentals.textContent = "--";
    toggleMetrics.textContent = "Connect metrics";
    state.metricsSocket = null;
  });
  toggleMetrics.textContent = "Disconnect metrics";
}

function toggleMetricsConnection() {
  if (state.metricsSocket) {
    state.metricsSocket.close();
    return;
  }
  connectMetrics();
}

toggleMetrics.addEventListener("click", toggleMetricsConnection);

ensureDeveloperAccess();
