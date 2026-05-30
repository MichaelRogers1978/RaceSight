const backendUrl = "http://localhost:8000";

const state = {
    mode: "chat",
};

const API_KEY_STORAGE_KEY = "racesightApiKey";

function $(id) {
    return document.getElementById(id);
}

function setStatus(text) {
    $("status").textContent = text;
}

function setLiveStatus(text) {
    $("liveStatus").textContent = text;
}

function setOutput(value) {
    $("output").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

function appendOutput(value) {
    const next = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    $("output").textContent += next;
    $("output").scrollTop = $("output").scrollHeight;
}

function getApiKey() {
    return window.localStorage.getItem(API_KEY_STORAGE_KEY) || "";
}

function saveApiKey() {
    const apiKey = $("apiKeyInput").value.trim();
    if (apiKey) {
        window.localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
        setStatus("API key saved locally");
    } else {
        window.localStorage.removeItem(API_KEY_STORAGE_KEY);
        setStatus("API key cleared");
    }
}

function buildHeaders(baseHeaders = {}) {
    const apiKey = getApiKey();
    const headers = { ...baseHeaders };
    if (apiKey) {
        headers.Authorization = `Bearer ${apiKey}`;
    }
    return headers;
}

async function postJson(path, body) {
    const response = await fetch(`${backendUrl}${path}`, {
        method: "POST",
        headers: buildHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || `HTTP ${response.status}`);
    }

    return response.json();
}

async function fetchStatus() {
    try {
        const response = await fetch(`${backendUrl}/racesight/status`, {
            headers: buildHeaders(),
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        const parts = [
            data.status || "online",
            data.summary,
            data.alert_level ? `alert ${data.alert_level}` : null,
        ].filter(Boolean);
        setLiveStatus(`Live status: ${parts.join(" · ")}`);
    } catch (error) {
        setLiveStatus("Live status: offline");
    }
}

function currentModeLabel() {
    return state.mode.charAt(0).toUpperCase() + state.mode.slice(1);
}

function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll("[data-mode-panel]").forEach((panel) => {
        panel.hidden = panel.dataset.modePanel !== mode;
    });
    document.querySelectorAll("[data-mode-tab]").forEach((tab) => {
        tab.classList.toggle("active", tab.dataset.modeTab === mode);
    });
    setStatus(`${currentModeLabel()} mode ready`);
}

async function sendMessage() {
    const message = $("chatInput").value.trim();
    if (!message) {
        return;
    }
    appendOutput(`\nYou: ${message}\n`);
    setStatus("Sending chat to RaceSight...");
    const data = await postJson("/chat", { message });
    appendOutput(`RaceSight: ${data.response}\n`);
    setStatus("Chat response received");
}

async function generateBrief() {
    const focus = $("briefFocus").value.trim() || "balanced";
    setStatus("Generating race engineer brief...");
    const data = await postJson("/racesight/brief", { focus });
    setOutput(data);
    setStatus("Race engineer brief ready");
}

async function loadReplay() {
    const maxFrames = Number.parseInt($("replayFrames").value, 10) || 4;
    const includeBrief = $("replayBrief").checked;
    setStatus("Loading replay timeline...");
    const data = await postJson("/racesight/replay", { max_frames: maxFrames, include_brief: includeBrief });
    setOutput(data);
    setStatus("Replay loaded");
}

async function runCoachLoop() {
    const maxSteps = Number.parseInt($("coachSteps").value, 10) || 4;
    setStatus("Running driver coaching loop...");
    const data = await postJson("/racesight/coach-loop", { max_steps: maxSteps });
    setOutput(data);
    setStatus("Coaching loop ready");
}

async function streamChat() {
    const message = $("chatInput").value.trim();
    if (!message) {
        return;
    }

    $("output").textContent = `You: ${message}\n\nRaceSight: `;
    setStatus("Streaming response...");

    const response = await fetch(`${backendUrl}/racesight/stream`, {
        method: "POST",
        headers: buildHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({ message }),
    });

    if (!response.ok || !response.body) {
        throw new Error(`Streaming failed: HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        appendOutput(decoder.decode(value, { stream: true }));
    }

    appendOutput("\n");
    setStatus("Streaming complete");
}

async function generateGraniteText() {
    const prompt = $("granitePrompt").value.trim();
    if (!prompt) {
        return;
    }
    setStatus("Calling Granite text generator...");
    const data = await postJson("/racesight/granite", {
        prompt,
        system_prompt: $("graniteSystemPrompt").value.trim() || undefined,
    });
    setOutput(data);
    setStatus("Granite text generated");
}

window.sendMessage = sendMessage;
window.generateBrief = generateBrief;
window.loadReplay = loadReplay;
window.runCoachLoop = runCoachLoop;
window.streamChat = streamChat;
window.generateGraniteText = generateGraniteText;
window.setMode = setMode;
window.saveApiKey = saveApiKey;

window.addEventListener("DOMContentLoaded", () => {
    $("apiKeyInput").value = getApiKey();
    setMode("chat");
    fetchStatus();
    window.setInterval(fetchStatus, 15000);
});
