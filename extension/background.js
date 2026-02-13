const ROBOFLOW_API_URL = "https://serverless.roboflow.com";
const ROBOFLOW_MODEL_ID = "turk-isaret-dili/2";

async function getApiKey() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["roboflow_api_key"], (items) => {
      resolve(items.roboflow_api_key || "");
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

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || message.type !== "predict") {
    return;
  }

  (async () => {
    try {
      const data = await inferRoboflow(message.payload.image_base64, 12000);
      sendResponse({ ok: true, data });
    } catch (error) {
      sendResponse({ ok: false, error: String(error || "roboflow unreachable") });
    }
  })();

  return true;
});
