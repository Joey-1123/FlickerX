const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

export const getUsers = async (token) => {
    const res = await fetch(`${BASE_URL}/api/admin/users`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    });
    const payload = await res.json();
    if (!res.ok) {
        throw new Error(payload?.error || "Unable to load admin data.");
    }
    return payload.users || [];
};
