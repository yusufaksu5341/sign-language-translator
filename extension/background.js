const ROBOFLOW_API_URL = "https://serverless.roboflow.com";
const ROBOFLOW_MODEL_ID = "turk-isaret-dili/2";
const DEFAULT_ROBOFLOW_API_KEY = "p6t4i9gco8ZGaA3Y1i26";
const LOCAL_API_URLS = [
  "http://127.0.0.1:8000/predict",
  "http://localhost:8000/predict",
];
const ALLOW_DIRECT_ROBOFLOW_FALLBACK = false;

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(["roboflow_api_key"], (items) => {
    if (!items.roboflow_api_key && DEFAULT_ROBOFLOW_API_KEY) {
      chrome.storage.local.set({ roboflow_api_key: DEFAULT_ROBOFLOW_API_KEY });
    }
  });
});

async function getApiKey() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["roboflow_api_key"], (items) => {
      resolve(items.roboflow_api_key || DEFAULT_ROBOFLOW_API_KEY || "");
    });
  });
}

async function inferRoboflow(imageBase64, timeoutMs = 12000) {
  const apiKey = await getApiKey();
  if (!apiKey) {
    throw new Error("roboflow_api_key not set in extension storage");
  }

  const blob = await (await fetch(imageBase64)).blob();
  const form = new FormData();
  form.append("file", blob, "frame.jpg");

  const url = `${ROBOFLOW_API_URL}/${ROBOFLOW_MODEL_ID}?api_key=${encodeURIComponent(apiKey)}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      method: "POST",
      body: form,
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status}: ${text}`);
    }

    const result = await res.json();
    const predictions = result.predictions || [];
    if (!predictions.length) {
      return { text: "", confidence: 0, ready: true, source: "roboflow" };
    }

    const best = predictions.reduce((acc, cur) => {
      const curConf = Number(cur.confidence || 0);
      const accConf = Number(acc.confidence || 0);
      return curConf > accConf ? cur : acc;
    }, predictions[0]);

    return {
      text: String(best.class || "").trim(),
      confidence: Number(best.confidence || 0),
      ready: true,
      source: "roboflow",
    };
  } finally {
    clearTimeout(timeout);
  }
}

async function inferLocalApi(payload, timeoutMs = 7000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    let lastError = null;
    for (const url of LOCAL_API_URLS) {
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
      } catch (error) {
        lastError = error;
      }
    }

    throw new Error(String(lastError || "local api unreachable"));
  } finally {
    clearTimeout(timeout);
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "predict") {
    return;
  }

  (async () => {
    try {
      let data = await inferLocalApi(message.payload, 7000);
      if (!data && ALLOW_DIRECT_ROBOFLOW_FALLBACK) {
        data = await inferRoboflow(message.payload.image_base64, 12000);
      }
      sendResponse({ ok: true, data });
    } catch (error) {
      if (ALLOW_DIRECT_ROBOFLOW_FALLBACK) {
        try {
          const data = await inferRoboflow(message.payload.image_base64, 12000);
          sendResponse({ ok: true, data });
          return;
        } catch (fallbackError) {
          sendResponse({ ok: false, error: String(fallbackError || "inference unreachable") });
          return;
        }
      }
      sendResponse({ ok: false, error: String(error || "local merged api unreachable") });
    }
  })();

  return true;
});
