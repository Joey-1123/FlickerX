import { readUsers } from "../services/userService.js";

export const getAllUsers = async (req, res) => {
    try {
        const users = await readUsers();
        const sanitizedUsers = users.map((user) => ({
            id: user.id,
            email: user.email,
            name: user.name,
            role: user.role,
            createdAt: user.createdAt,
        }));
        return res.json({ users: sanitizedUsers });
    } catch (err) {
        console.error("Admin fetch failed:", err);
        return res.status(500).json({ error: "Unable to fetch users." });
    }
};
