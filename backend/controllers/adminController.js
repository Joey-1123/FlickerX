import { readUsers, deleteUserById, updateUserRole } from "../services/userService.js";

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

export const deleteUser = async (req, res) => {
    try {
        const { id } = req.params;
        if (id === req.user.id) {
            return res.status(400).json({ error: "Cannot delete yourself." });
        }
        const deleted = await deleteUserById(id);
        if (!deleted) {
            return res.status(404).json({ error: "User not found." });
        }
        return res.json({ message: "User deleted." });
    } catch (err) {
        console.error("Admin delete user failed:", err);
        return res.status(500).json({ error: "Unable to delete user." });
    }
};

export const changeUserRole = async (req, res) => {
    try {
        const { id } = req.params;
        const { role } = req.body;
        if (!["user", "admin"].includes(role)) {
            return res.status(400).json({ error: "Invalid role. Must be 'user' or 'admin'." });
        }
        if (id === req.user.id) {
            return res.status(400).json({ error: "Cannot change your own role." });
        }
        const updated = await updateUserRole(id, role);
        if (!updated) {
            return res.status(404).json({ error: "User not found." });
        }
        return res.json({ message: `User role updated to ${role}.` });
    } catch (err) {
        console.error("Admin change role failed:", err);
        return res.status(500).json({ error: "Unable to update role." });
    }
};
