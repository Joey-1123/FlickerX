const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

const parseJsonResponse = async (res) => {
    const payload = await res.json();
    if (!res.ok) {
        throw new Error(payload?.error || "Request failed");
    }
    return payload;
};

export const register = async (email, password, name, agreements = {}) => {
    const res = await fetch(`${BASE_URL}/api/auth/register`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password, name, ...agreements }),
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

export const acceptPolicies = async (token, agreements) => {
    const res = await fetch(`${BASE_URL}/api/auth/accept-policies`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(agreements),
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

// Changed: update profile fields (name, systemPrompt)
export const updateProfile = async (token, updates) => {
    const res = await fetch(`${BASE_URL}/api/auth/me`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
    });

    return parseJsonResponse(res);
};

export const deleteAccount = async (token) => {
    const res = await fetch(`${BASE_URL}/api/auth/me`, {
        method: "DELETE",
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    if (!res.ok) {
        const payload = await res.json();
        throw new Error(payload?.error || "Failed to delete account.");
    }
};

export const forgotPassword = async (email) => {
    const res = await fetch(`${BASE_URL}/api/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
    });

    return parseJsonResponse(res);
};

export const resetPassword = async (token, password) => {
    const res = await fetch(`${BASE_URL}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
    });

    return parseJsonResponse(res);
};
