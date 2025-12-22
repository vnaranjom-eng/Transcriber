const $ = (id) => document.getElementById(id);

const btnConnect = $("btnConnect");
const btnStart = $("btnStart");
const btnStop = $("btnStop");
const statusEl = $("status");
const dot = $("dot");
const sttFinalEl = $("sttFinal");
const llmTextEl = $("llmText");
const eventsEl = $("events");
const wsUrlEl = $("wsUrl");
const langEl = $("lang");
const dgModelEl = $("dgModel");
const openaiModelEl = $("openaiModel");
const systemPromptEl = $("systemPrompt");
const audioInfoEl = $("audioInfo");

const TARGET_SAMPLE_RATE = 16000;
const TARGET_CHANNELS = 1;

let ws = null;
let audioCtx = null;
let mediaStream = null;
let processor = null;
let source = null;

let isStreaming = false;
let totalBytesSent = 0;
let lastStatsAt = 0;

function logEvent(obj) {
  const line = typeof obj === "string" ? obj : JSON.stringify(obj);
  eventsEl.textContent = `${line}\n${eventsEl.textContent}`.slice(0, 7000);
}

function setStatus(text, kind) {
  statusEl.textContent = text;
  dot.classList.remove("good", "bad");
  if (kind === "good") dot.classList.add("good");
  if (kind === "bad") dot.classList.add("bad");
}

function defaultWsUrl() {
  const isHttps = window.location.protocol === "https:";
  const proto = isHttps ? "wss" : "ws";
  return `${proto}://${window.location.host}/ws`;
}

function clamp16(v) {
  const s = Math.max(-1, Math.min(1, v));
  return s < 0 ? s * 0x8000 : s * 0x7fff;
}

function downsampleTo16k(float32, inputSampleRate) {
  if (inputSampleRate === TARGET_SAMPLE_RATE) return float32;
  const ratio = inputSampleRate / TARGET_SAMPLE_RATE;
  const newLen = Math.floor(float32.length / ratio);
  const out = new Float32Array(newLen);
  let offset = 0;
  for (let i = 0; i < newLen; i++) {
    const nextOffset = Math.floor((i + 1) * ratio);
    let sum = 0;
    let count = 0;
    for (let j = offset; j < nextOffset && j < float32.length; j++) {
      sum += float32[j];
      count++;
    }
    out[i] = count > 0 ? sum / count : 0;
    offset = nextOffset;
  }
  return out;
}

function floatToPCM16LEBytes(float32) {
  const buf = new ArrayBuffer(float32.length * 2);
  const view = new DataView(buf);
  for (let i = 0; i < float32.length; i++) {
    view.setInt16(i * 2, clamp16(float32[i]), true);
  }
  return buf;
}

async function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  const url = wsUrlEl.value.trim() || defaultWsUrl();
  wsUrlEl.value = url;

  setStatus("conectando...", "");
  ws = new WebSocket(url);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    setStatus("conectado", "good");
    btnConnect.disabled = true;
    btnStart.disabled = false;
    btnStop.disabled = false;
    logEvent({ type: "ws_open", url });

    // Send start config (also ensures backend pipeline starts)
    ws.send(
      JSON.stringify({
        type: "start",
        sample_rate: TARGET_SAMPLE_RATE,
        channels: TARGET_CHANNELS,
        deepgram_language: langEl.value,
        deepgram_model: dgModelEl.value.trim() || "nova-3-general",
        openai_model: openaiModelEl.value.trim() || "gpt-4.1",
        system_prompt: systemPromptEl.value,
      })
    );
  };

  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === "ready" || msg.type === "started") {
        logEvent(msg);
        return;
      }
      if (msg.type === "stt_final") {
        sttFinalEl.textContent = `${msg.text}\n${sttFinalEl.textContent}`;
        logEvent(msg);
        return;
      }
      if (msg.type === "stt_interim") {
        // no spam: show last interim as a single line at top
        const lines = sttFinalEl.textContent.split("\n");
        const prefix = `[interim] ${msg.text}`;
        if (lines.length === 0) sttFinalEl.textContent = prefix;
        else sttFinalEl.textContent = `${prefix}\n${lines.slice(1).join("\n")}`;
        return;
      }
      if (msg.type === "llm_start") {
        llmTextEl.textContent = "";
        logEvent(msg);
        return;
      }
      if (msg.type === "llm_delta") {
        llmTextEl.textContent += msg.text || "";
        return;
      }
      if (msg.type === "llm_end") {
        logEvent(msg);
        return;
      }
      if (msg.type === "error") {
        setStatus("error", "bad");
        logEvent(msg);
        return;
      }
      logEvent(msg);
    } catch {
      logEvent({ type: "ws_msg_raw", data: String(ev.data).slice(0, 200) });
    }
  };

  ws.onclose = () => {
    setStatus("desconectado", "");
    btnConnect.disabled = false;
    btnStart.disabled = true;
    btnStop.disabled = true;
    stopStreaming().catch(() => {});
    logEvent({ type: "ws_close" });
    ws = null;
  };

  ws.onerror = () => {
    setStatus("error", "bad");
    logEvent({ type: "ws_error" });
  };
}

async function startStreaming() {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    await connect();
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
  }
  if (isStreaming) return;

  isStreaming = true;
  totalBytesSent = 0;
  lastStatsAt = performance.now();

  mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: TARGET_CHANNELS,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
    video: false,
  });

  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  source = audioCtx.createMediaStreamSource(mediaStream);

  // ScriptProcessorNode is deprecated but broadly compatible and simplest for a zero-build demo.
  const bufferSize = 4096;
  processor = audioCtx.createScriptProcessor(bufferSize, TARGET_CHANNELS, TARGET_CHANNELS);

  processor.onaudioprocess = (e) => {
    if (!isStreaming || !ws || ws.readyState !== WebSocket.OPEN) return;

    const input = e.inputBuffer.getChannelData(0);
    const down = downsampleTo16k(input, audioCtx.sampleRate);
    const pcmBuf = floatToPCM16LEBytes(down);

    try {
      ws.send(pcmBuf);
      totalBytesSent += pcmBuf.byteLength;
    } catch {
      // ignore if socket closed mid-frame
    }

    const now = performance.now();
    if (now - lastStatsAt > 800) {
      const kb = (totalBytesSent / 1024).toFixed(1);
      audioInfoEl.textContent = `AudioContext: ${audioCtx.sampleRate}Hz → ${TARGET_SAMPLE_RATE}Hz | enviados: ${kb} KB`;
      lastStatsAt = now;
    }
  };

  source.connect(processor);
  processor.connect(audioCtx.destination);

  btnStart.disabled = true;
  btnStop.disabled = false;
  logEvent({ type: "mic_started", input_sample_rate: audioCtx.sampleRate });
}

async function stopStreaming() {
  isStreaming = false;

  if (processor) {
    try {
      processor.disconnect();
    } catch {}
    processor.onaudioprocess = null;
    processor = null;
  }

  if (source) {
    try {
      source.disconnect();
    } catch {}
    source = null;
  }

  if (mediaStream) {
    for (const track of mediaStream.getTracks()) track.stop();
    mediaStream = null;
  }

  if (audioCtx) {
    try {
      await audioCtx.close();
    } catch {}
    audioCtx = null;
  }

  btnStart.disabled = !ws || ws.readyState !== WebSocket.OPEN;
  btnStop.disabled = true;

  if (ws && ws.readyState === WebSocket.OPEN) {
    try {
      ws.send(JSON.stringify({ type: "end" }));
    } catch {}
  }

  logEvent({ type: "mic_stopped" });
}

btnConnect.addEventListener("click", () => connect());
btnStart.addEventListener("click", () => startStreaming());
btnStop.addEventListener("click", () => stopStreaming());

// Initialize WS URL default
wsUrlEl.value = defaultWsUrl();

