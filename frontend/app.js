const state = {
  baseUrl: localStorage.getItem("br.baseUrl") || "/api",
  bearerToken: localStorage.getItem("br.bearerToken") || "",
  apiKey: localStorage.getItem("br.apiKey") || "dev-key-123",
  metricsSocket: null,
};

const outputMeta = document.getElementById("output-meta");
const outputBody = document.getElementById("output-body");
const activeRentals = document.getElementById("active-rentals");
const toggleMetrics = document.getElementById("toggle-metrics");

const baseUrlInput = document.getElementById("base-url");
const bearerInput = document.getElementById("bearer-token");
const apiKeyInput = document.getElementById("api-key");

baseUrlInput.value = state.baseUrl;
bearerInput.value = state.bearerToken;
apiKeyInput.value = state.apiKey;

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

function saveConnection(event) {
  event.preventDefault();
  state.baseUrl = baseUrlInput.value.trim();
  state.bearerToken = bearerInput.value.trim();
  state.apiKey = apiKeyInput.value.trim();
  localStorage.setItem("br.baseUrl", state.baseUrl);
  localStorage.setItem("br.bearerToken", state.bearerToken);
  localStorage.setItem("br.apiKey", state.apiKey);
  setOutput("Saved connection settings.", "{}");
}

document.getElementById("connection-form").addEventListener("submit", saveConnection);

document.getElementById("register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    email: form.email.value.trim(),
    password: form.password.value,
  };
  const { body } = await request("/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  try {
    const parsed = JSON.parse(body);
    if (parsed.access_token) {
      state.bearerToken = parsed.access_token;
      bearerInput.value = parsed.access_token;
      localStorage.setItem("br.bearerToken", parsed.access_token);
    }
  } catch (err) {
    // Response already displayed.
  }
});

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    email: form.email.value.trim(),
    password: form.password.value,
  };
  const { body } = await request("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  try {
    const parsed = JSON.parse(body);
    if (parsed.access_token) {
      state.bearerToken = parsed.access_token;
      bearerInput.value = parsed.access_token;
      localStorage.setItem("br.bearerToken", parsed.access_token);
    }
  } catch (err) {
    // Response already displayed.
  }
});

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
