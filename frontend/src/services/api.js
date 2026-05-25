const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

export const sendMessageToBackend = async (message, token, fileUrl) => {
    const res = await fetch(`${BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message, fileUrl }),
    });

    if (!res.ok) {
        const err = await res.text();
        console.error("Backend error:", {
            status: res.status,
            statusText: res.statusText,
            body: err,
        });
        throw new Error("Request failed" + (err ? `: ${err}` : ""));
    }

    return res.json();
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

