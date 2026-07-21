import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getUsers, deleteUser, changeUserRole } from "../services/admin";
import { ArrowLeft } from "lucide-react";
import { useTheme } from "../context/ThemeContext"; // Adjust the import path as needed

// Helper to map accent strings to safe Tailwind classes
const getAccentClasses = (accent) => {
    const variants = {
        blue: { softBg: "bg-blue-50 dark:bg-blue-900/20", softText: "text-blue-600 dark:text-blue-400", softHover: "hover:bg-blue-100 dark:hover:bg-blue-900/40", hoverBg: "hover:bg-blue-50 dark:hover:bg-blue-900/30", hoverText: "hover:text-blue-600 dark:hover:text-blue-400" },
        purple: { softBg: "bg-purple-50 dark:bg-purple-900/20", softText: "text-purple-600 dark:text-purple-400", softHover: "hover:bg-purple-100 dark:hover:bg-purple-900/40", hoverBg: "hover:bg-purple-50 dark:hover:bg-purple-900/30", hoverText: "hover:text-purple-600 dark:hover:text-purple-400" },
        green: { softBg: "bg-green-50 dark:bg-green-900/20", softText: "text-green-600 dark:text-green-400", softHover: "hover:bg-green-100 dark:hover:bg-green-900/40", hoverBg: "hover:bg-green-50 dark:hover:bg-green-900/30", hoverText: "hover:text-green-600 dark:hover:text-green-400" },
        orange: { softBg: "bg-orange-50 dark:bg-orange-900/20", softText: "text-orange-600 dark:text-orange-400", softHover: "hover:bg-orange-100 dark:hover:bg-orange-900/40", hoverBg: "hover:bg-orange-50 dark:hover:bg-orange-900/30", hoverText: "hover:text-orange-600 dark:hover:text-orange-400" },
        pink: { softBg: "bg-pink-50 dark:bg-pink-900/20", softText: "text-pink-600 dark:text-pink-400", softHover: "hover:bg-pink-100 dark:hover:bg-pink-900/40", hoverBg: "hover:bg-pink-50 dark:hover:bg-pink-900/30", hoverText: "hover:text-pink-600 dark:hover:text-pink-400" },
        teal: { softBg: "bg-teal-50 dark:bg-teal-900/20", softText: "text-teal-600 dark:text-teal-400", softHover: "hover:bg-teal-100 dark:hover:bg-teal-900/40", hoverBg: "hover:bg-teal-50 dark:hover:bg-teal-900/30", hoverText: "hover:text-teal-600 dark:hover:text-teal-400" },
    };
    return variants[accent] || variants.blue;
};

export default function Admin() {
    const { token, user, isAuthenticated } = useAuth();
    const [users, setUsers] = useState([]);
    const [error, setError] = useState("");
    const [toast, setToast] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    // Theme context
    const { accent, colors } = useTheme();
    const themeStyles = getAccentClasses(accent);
    const ringClass = colors[accent]?.ring || "ring-blue-500";

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
            <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0a0a0a] transition-colors duration-300">
                <div className="rounded-3xl bg-white dark:bg-[#111111] p-8 shadow-lg border border-slate-200 dark:border-gray-800 text-gray-900 dark:text-gray-100 transition-colors duration-300">Loading admin data...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-[#0a0a0a] py-10 px-4 transition-colors duration-300">
            {toast && (
                <div className="fixed top-4 left-1/2 -translate-x-1/2 bg-black dark:bg-white text-white dark:text-black text-sm px-4 py-2 rounded-xl shadow-xl z-50 transition-colors duration-300">
                    {toast}
                </div>
            )}

            <div className="mx-auto max-w-6xl rounded-3xl bg-white dark:bg-[#111111] p-4 sm:p-8 shadow-lg border border-slate-200 dark:border-gray-800 transition-colors duration-300">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-gray-100 transition-colors duration-300">Admin Dashboard</h1>
                        <p className="text-sm text-slate-500 dark:text-gray-400 transition-colors duration-300">Welcome, {user?.name}. Manage your user base below.</p>
                    </div>
                    <div className="rounded-3xl bg-slate-50 dark:bg-[#0a0a0a] p-4 text-sm text-slate-600 dark:text-gray-400 border border-slate-200 dark:border-gray-800 transition-colors duration-300">
                        Role: <span className="font-semibold text-slate-900 dark:text-gray-100">{user?.role}</span>
                    </div>
                </div>

                {error ? (
                    <div className="rounded-2xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 px-4 py-3 text-sm text-red-700 dark:text-red-400 mb-6 transition-colors duration-300">
                        {error}
                    </div>
                ) : null}

                <div className="overflow-x-auto rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-[#0a0a0a] transition-colors duration-300">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-gray-800">
                        <thead className="bg-slate-100 dark:bg-[#111111] transition-colors duration-300">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Name</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Email</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Role</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Created</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-gray-400">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 dark:divide-gray-800 bg-white dark:bg-[#0a0a0a] transition-colors duration-300">
                            {users.map((u) => (
                                <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-[#111111] transition-colors duration-200">
                                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-slate-700 dark:text-gray-300 whitespace-nowrap">{u.name}</td>
                                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-slate-700 dark:text-gray-300 whitespace-nowrap">{u.email}</td>
                                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-slate-700 dark:text-gray-300 whitespace-nowrap">{u.role}</td>
                                    <td className="px-4 sm:px-6 py-4 text-xs sm:text-sm text-slate-500 dark:text-gray-500 whitespace-nowrap">{new Date(u.createdAt).toLocaleString()}</td>
                                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap">
                                        <div className="flex gap-2">
                                            {u.id !== user?.id && (
                                                <>
                                                    <button
                                                        onClick={() => handleRoleToggle(u.id, u.role)}
                                                        className={`text-xs px-3 py-1.5 rounded-xl transition-colors duration-200 ${themeStyles.softBg} ${themeStyles.softText} ${themeStyles.softHover}`}
                                                    >
                                                        {u.role === "admin" ? "Demote" : "Promote"}
                                                    </button>
                                                    <button
                                                        onClick={() => handleDeleteUser(u.id, u.name)}
                                                        className="text-xs px-3 py-1.5 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors duration-200"
                                                    >
                                                        Delete
                                                    </button>
                                                </>
                                            )}
                                            {u.id === user?.id && (
                                                <span className="text-xs text-slate-400 dark:text-gray-500 italic">You</span>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Back Button */}
                <div className="flex justify-center w-full mt-8">
                    <button
                        onClick={() => navigate(-1)}
                        className={`flex items-center px-5 py-2.5 bg-white dark:bg-[#0a0a0a] border border-gray-200 dark:border-gray-800 text-sm font-medium text-gray-600 dark:text-gray-400 rounded-full shadow-sm hover:border-transparent transition-all duration-200 focus:outline-none focus:ring-2 ${themeStyles.hoverBg} ${themeStyles.hoverText} ${ringClass}`}
                        aria-label="Go back to previous page"
                    >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Go Back
                    </button>
                </div>
            </div>
        </div>
    );
}