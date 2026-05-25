import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5000";

export default function Admin() {
    const { token, user, isAuthenticated } = useAuth();
    const [users, setUsers] = useState([]);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        if (!isAuthenticated) {
            navigate("/login");
            return;
        }

        const fetchAdminData = async () => {
            try {
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
                setUsers(payload.users || []);
            } catch (err) {
                setError(err.message || "Failed to load admin data.");
            } finally {
                setLoading(false);
            }
        };

        fetchAdminData();
    }, [isAuthenticated, token, navigate]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="rounded-3xl bg-white p-8 shadow-lg border border-slate-200">Loading admin data...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 py-10 px-4">
            <div className="mx-auto max-w-5xl rounded-3xl bg-white p-8 shadow-lg border border-slate-200">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Admin Dashboard</h1>
                        <p className="text-sm text-slate-500">Welcome, {user?.name}. Manage your user base below.</p>
                    </div>
                    <div className="rounded-3xl bg-slate-50 p-4 text-sm text-slate-600 border border-slate-200">
                        Role: <span className="font-semibold text-slate-900">{user?.role}</span>
                    </div>
                </div>

                {error ? (
                    <div className="rounded-2xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 mb-6">
                        {error}
                    </div>
                ) : null}

                <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-slate-50">
                    <table className="min-w-full divide-y divide-slate-200">
                        <thead className="bg-slate-100">
                            <tr>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Name</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Email</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Role</th>
                                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">Created</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 bg-white">
                            {users.map((u) => (
                                <tr key={u.id} className="hover:bg-slate-50">
                                    <td className="px-6 py-4 text-sm text-slate-700">{u.name}</td>
                                    <td className="px-6 py-4 text-sm text-slate-700">{u.email}</td>
                                    <td className="px-6 py-4 text-sm text-slate-700">{u.role}</td>
                                    <td className="px-6 py-4 text-sm text-slate-500">{new Date(u.createdAt).toLocaleString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
