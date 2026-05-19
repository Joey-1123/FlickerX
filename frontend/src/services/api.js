// Changed: read backend base URL from Vite env or fall back to localhost for dev
const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

export const sendMessageToBackend = async (message, token, fileUrl) => {
    // Send the message and file URL to the backend API
    const res = await fetch(`${BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            // Only include Authorization header when token is provided
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message, fileUrl }),
    });

    if (!res.ok) {
        const err = await res.text();
        console.error("Backend error:", err);
        throw new Error("Request failed" + (err ? `: ${err}` : ""));
    }

    return res.json();
};

export const uploadFile = async (file) => {
    // Upload the file to the backend and get the URL
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/api/upload`, {
        method: "POST",
        body: formData,
    });

    const data = await res.json();
    return data.url;
};

