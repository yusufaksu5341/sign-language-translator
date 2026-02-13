const API_URLS = [
  "http://127.0.0.1:8000/predict",
  "http://localhost:8000/predict",
];

async function fetchWithTimeout(url, payload, timeoutMs = 5000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    return await res.json();
  } finally {
    clearTimeout(timeout);
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "predict") {
    return;
  }

  (async () => {
    let lastError = null;
    for (const url of API_URLS) {
      try {
        const data = await fetchWithTimeout(url, message.payload, 5000);
        sendResponse({ ok: true, data });
        return;
      } catch (error) {
        lastError = error;
      }
    }
    sendResponse({ ok: false, error: String(lastError || "unreachable") });
  })();

  return true;
});
