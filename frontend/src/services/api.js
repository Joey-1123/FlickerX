const BASE_URL = "http://localhost:5000";

export const sendMessageToBackend = async (message, token, fileUrl) => {
    // Send the message and file URL to the backend API
    const res = await fetch(`${BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
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

    const res = await fetch("http://localhost:5000/api/upload", {
        method: "POST",
        body: formData,
    });

    const data = await res.json();
    return data.url;
};

