import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getUsers, deleteUser, changeUserRole } from "../services/admin";

export default function Admin() {
    const { token, user, isAuthenticated } = useAuth();
    const [users, setUsers] = useState([]);
    const [error, setError] = useState("");
    const [toast, setToast] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    const fetchUsers = async () => {
        try {
            setError("");
            const data = await getUsers(token);
            setUsers(data);
        } catch (err) {
            setError(err.message || "Failed to load admin data.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (!isAuthenticated) {
            navigate("/login");
            return;
        }
        fetchUsers();
    }, [isAuthenticated, token, navigate]);

    const handleDeleteUser = async (userId, userName) => {
        if (!window.confirm(`Delete user "${userName}"? This cannot be undone.`)) return;
        try {
            await deleteUser(token, userId);
            setToast("User deleted.");
            fetchUsers();
        } catch (err) {
            setError(err.message);
        }
    };

    const handleRoleToggle = async (userId, currentRole) => {
        const newRole = currentRole === "admin" ? "user" : "admin";
        try {
            await changeUserRole(token, userId, newRole);
            setToast(`User role changed to ${newRole}.`);
            fetchUsers();
        } catch (err) {
            setError(err.message);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950">
                <div className="rounded-3xl bg-white dark:bg-gray-900 p-8 shadow-lg border border-slate-200 dark:border-gray-800">Loading admin data...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-gray-950 py-10 px-4">
            {toast && (
                <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-black text-white text-sm px-4 py-2 rounded-xl shadow-xl z-50">
                    {toast}
                </div>
            )}

            <div className="mx-auto max-w-6xl rounded-3xl bg-white dark:bg-gray-900 p-4 sm:p-8 shadow-lg border border-slate-200 dark:border-gray-800">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-gray-100">Admin Dashboard</h1>
                        <p className="text-sm text-slate-500 dark:text-gray-400">Welcome, {user?.name}. Manage your user base below.</p>
                    </div>
                    <div className="rounded-3xl bg-slate-50 dark:bg-gray-800 p-4 text-sm text-slate-600 dark:text-gray-400 border border-slate-200 dark:border-gray-700">
                        Role: <span className="font-semibold text-slate-900 dark:text-gray-100">{user?.role}</span>
                    </div>
                </div>

                {error ? (
                    <div className="rounded-2xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 px-4 py-3 text-sm text-red-700 dark:text-red-400 mb-6">
                        {error}
                    </div>
                ) : null}

                <div className="overflow-x-auto rounded-3xl border border-slate-200 dark:border-gray-700 bg-slate-50 dark:bg-gray-800">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-gray-700">
                        <thead className="bg-slate-100 dark:bg-gray-800">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Name</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Email</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Role</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Created</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
                            {users.map((u) => (
                                <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-gray-800">
                                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-slate-700 dark:text-gray-300 whitespace-nowrap">{u.name}</td>
                                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-slate-700 dark:text-gray-300 whitespace-nowrap">{u.email}</td>
                                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-slate-700 dark:text-gray-300 whitespace-nowrap">{u.role}</td>
                                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-slate-500 dark:text-gray-400 whitespace-nowrap">{new Date(u.createdAt).toLocaleString()}</td>
                                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="flex gap-2">
                                            {u.id !== user?.id && (
                                                <>
                                                    <button
                                                        onClick={() => handleRoleToggle(u.id, u.role)}
                                                        className="text-xs px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition"
                                                    >
                                                        {u.role === "admin" ? "Demote" : "Promote"}
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteUser(u.id, u.name)}
                                                        className="text-xs px-3 py-1.5 rounded-xl bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50 transition"
                                                    >
                                                        Delete
                                                    </button>
                                                </>
                                            )}
                                            {u.id === user?.id && (
                                                <span className="text-xs text-slate-400 italic">You</span>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
