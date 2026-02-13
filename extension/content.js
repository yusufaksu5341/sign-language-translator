const SESSION_ID = "meet-session-1";
const FRAME_INTERVAL_MS = 500;

let canvas = document.createElement("canvas");
let ctx = canvas.getContext("2d");
let overlay = null;

function ensureOverlay() {
  if (overlay) return;
  overlay = document.createElement("div");
  overlay.style.position = "fixed";
  overlay.style.right = "20px";
  overlay.style.bottom = "20px";
  overlay.style.zIndex = "999999";
  overlay.style.background = "rgba(0,0,0,0.8)";
  overlay.style.color = "#fff";
  overlay.style.padding = "10px 14px";
  overlay.style.borderRadius = "8px";
  overlay.style.fontSize = "14px";
  overlay.style.fontFamily = "Arial, sans-serif";
  overlay.textContent = "Sign: waiting...";
  document.body.appendChild(overlay);
}

function findActiveVideo() {
  const videos = Array.from(document.querySelectorAll("video"));
  return videos.find((v) => v.videoWidth > 0 && v.videoHeight > 0) || null;
}

async function sendFrame(video) {
  canvas.width = 320;
  canvas.height = 240;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const imageBase64 = canvas.toDataURL("image/jpeg", 0.75);

  const response = await chrome.runtime.sendMessage({
    type: "predict",
    payload: { session_id: SESSION_ID, image_base64: imageBase64 },
  });

  if (!response || !response.ok) {
    const reason = response?.error || "no response from background";
    throw new Error(reason);
  }

  const data = response.data;
  if (data.error) {
    overlay.textContent = `Sign: error (${data.error})`;
    return;
  }

  if (!data.ready) {
    overlay.textContent = "Sign: collecting sequence...";
    return;
  }

  overlay.textContent = `Sign: ${data.text} (${(data.confidence || 0).toFixed(2)})`;
}

async function loop() {
  ensureOverlay();
  const video = findActiveVideo();
  if (!video) {
    overlay.textContent = "Sign: no video found";
    setTimeout(loop, FRAME_INTERVAL_MS);
    return;
  }

  try {
    await sendFrame(video);
  } catch (err) {
    overlay.textContent = `Sign: API not reachable (${String(err).slice(0, 80)})`;
  }

  setTimeout(loop, FRAME_INTERVAL_MS);
}

loop();
