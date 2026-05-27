const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

// Changed: accepts `model` and `userApiKey` parameters
export const sendMessageToBackend = async (messages, token, fileUrl, model, userApiKey) => {
    const body = { messages, ...(fileUrl ? { fileUrl } : {}), ...(model ? { model } : {}), ...(userApiKey ? { userApiKey } : {}) };
    const res = await fetch(`${BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const err = await res.text();
        console.error("Backend error:", { status: res.status, body: err });
        throw new Error("Request failed" + (err ? `: ${err}` : ""));
    }

    return res.json();
};

// Changed: streaming chat — reads SSE events and calls onChunk(content)
export const streamChat = async (messages, token, fileUrl, model, onChunk, userApiKey) => {
    const body = { messages, ...(fileUrl ? { fileUrl } : {}), ...(model ? { model } : {}), ...(userApiKey ? { userApiKey } : {}) };
    const res = await fetch(`${BASE_URL}/api/chat/stream`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
    });

    if (!res.ok) {
        const err = await res.text();
        throw new Error("Stream request failed" + (err ? `: ${err}` : ""));
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data: ")) continue;
            const data = trimmed.slice(6);
            try {
                const parsed = JSON.parse(data);
                if (parsed.done) return parsed.fullContent;
                if (parsed.content) onChunk(parsed.content);
                if (parsed.error) throw new Error(parsed.error);
            } catch (e) {
                if (e instanceof SyntaxError) continue;
                throw e;
            }
        }
    }
};

export const uploadFile = async (file, token) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/api/upload`, {
        method: "POST",
        headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
    });

    const payload = await res.json();
    if (!res.ok) {
        throw new Error(payload?.error || "Upload failed");
    }
    return payload.url;
};
