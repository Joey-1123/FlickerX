const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

const parseJsonResponse = async (res) => {
    const payload = await res.json();
    if (!res.ok) {
        throw new Error(payload?.error || "Request failed");
    }
    return payload;
};

export const register = async (email, password, name) => {
    const res = await fetch(`${BASE_URL}/api/auth/register`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password, name }),
    });

    return parseJsonResponse(res);
};

export const login = async (email, password) => {
    const res = await fetch(`${BASE_URL}/api/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
    });

    return parseJsonResponse(res);
};

export const refreshAuth = async () => {
    const res = await fetch(`${BASE_URL}/api/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
    });

    return parseJsonResponse(res);
};

export const logout = async () => {
    const res = await fetch(`${BASE_URL}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
    });

    if (!res.ok) {
        const payload = await res.json();
        throw new Error(payload?.error || "Logout failed");
    }
};

export const getProfile = async (token) => {
    const res = await fetch(`${BASE_URL}/api/auth/me`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    });

    return parseJsonResponse(res);
};
