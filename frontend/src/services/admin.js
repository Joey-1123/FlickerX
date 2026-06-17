const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

const parseJson = async (res) => {
    const payload = await res.json();
    if (!res.ok) throw new Error(payload?.error || "Request failed");
    return payload;
};

export const getUsers = async (token) => {
    const res = await fetch(`${BASE_URL}/api/admin/users`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    });
    const payload = await parseJson(res);
    return payload.users || [];
};

export const deleteUser = async (token, userId) => {
    return parseJson(await fetch(`${BASE_URL}/api/admin/users/${userId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    }));
};

export const changeUserRole = async (token, userId, role) => {
    return parseJson(await fetch(`${BASE_URL}/api/admin/users/${userId}/role`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ role }),
    }));
};
