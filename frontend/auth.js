const state = {
  baseUrl: localStorage.getItem("br.baseUrl") || "/api",
};

const authMessage = document.getElementById("auth-message");
const baseUrlInput = document.getElementById("auth-base-url");

if (baseUrlInput) {
  baseUrlInput.value = state.baseUrl;
}

function normalizeBaseUrl(url) {
  return url.replace(/\/$/, "");
}

function setAuthMessage(message) {
  if (authMessage) {
    authMessage.textContent = message;
  }
}

function isSignedIn() {
  return Boolean(sessionStorage.getItem("br.bearerToken"));
}

function parseJsonMaybe(text) {
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (err) {
    return null;
  }
}

async function request(path, payload) {
  const url = `${normalizeBaseUrl(state.baseUrl)}${path}`;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const text = await response.text();
    const parsed = parseJsonMaybe(text);
    return { response, parsed, text, url };
  } catch (error) {
    setAuthMessage(`Request failed: ${error.message || String(error)}`);
    throw error;
  }
}

function saveBaseUrl() {
  if (!baseUrlInput) {
    return;
  }
  state.baseUrl = baseUrlInput.value.trim();
  localStorage.setItem("br.baseUrl", state.baseUrl);
}

async function handleAuthSubmit(event, path, successMessage) {
  event.preventDefault();
  saveBaseUrl();
  const form = event.currentTarget;
  const payload = {
    email: form.email.value.trim(),
    password: form.password.value,
  };
  const { response, parsed, text } = await request(path, payload);
  if (!response.ok) {
    const detail = parsed?.detail || text || `Request failed (${response.status})`;
    setAuthMessage(detail);
    return;
  }
  const token = parsed?.access_token || parsed?.accessToken || "";
  const role = parsed?.role;
  if (token) {
    sessionStorage.setItem("br.bearerToken", token);
  }
  setAuthMessage(successMessage);
  if (role === "developer") {
    window.location.href = "dashboard.html";
    return;
  }
  if (role === "guest") {
    window.location.href = "guest-dashboard.html";
    return;
  }
  if (token) {
    try {
      const access = await fetch(`${normalizeBaseUrl(state.baseUrl)}/access`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!access.ok) {
        setAuthMessage("Unable to verify access. Please try again.");
        return;
      }
      const accessPayload = await access.json();
      if (accessPayload?.role === "developer") {
        window.location.href = "dashboard.html";
        return;
      }
    } catch (err) {
      setAuthMessage("Unable to verify access. Please try again.");
      return;
    }
  }
  window.location.href = "guest-dashboard.html";
}

document.getElementById("login-form").addEventListener("submit", (event) => {
  handleAuthSubmit(event, "/login", "Login successful. Redirecting...");
});

document.getElementById("register-form").addEventListener("submit", (event) => {
  handleAuthSubmit(event, "/register", "Account created. Redirecting...");
});

async function redirectIfSignedIn() {
  if (!isSignedIn()) {
    return;
  }
  setAuthMessage("Signed in. Redirecting you to the right dashboard...");
  try {
    const token = sessionStorage.getItem("br.bearerToken") || "";
    const access = await fetch(`${normalizeBaseUrl(state.baseUrl)}/access`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!access.ok) {
      setAuthMessage("Signed in, but unable to verify access. Please log in again.");
      sessionStorage.removeItem("br.bearerToken");
      return;
    }
    const accessPayload = await access.json();
    if (accessPayload?.role === "developer") {
      window.location.href = "dashboard.html";
      return;
    }
  } catch (err) {
    setAuthMessage("Signed in, but unable to verify access. Please log in again.");
    sessionStorage.removeItem("br.bearerToken");
    return;
  }
  window.location.href = "guest-dashboard.html";
}

redirectIfSignedIn();

const storedMessage = localStorage.getItem("br.authMessage");
if (storedMessage) {
  setAuthMessage(storedMessage);
  localStorage.removeItem("br.authMessage");
}
