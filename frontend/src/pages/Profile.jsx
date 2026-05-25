import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getProfile } from "../services/auth";

export default function Profile() {
    const { token, logout, isAuthenticated } = useAuth();
    const [profile, setProfile] = useState(null);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        if (!isAuthenticated) {
            navigate("/login");
            return;
        }

        const loadProfile = async () => {
            try {
                const response = await getProfile(token);
                setProfile(response.user);
            } catch (err) {
                setError(err.message || "Unable to load profile.");
            } finally {
                setLoading(false);
            }
        };

        loadProfile();
    }, [isAuthenticated, token, navigate]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <div className="rounded-3xl bg-white p-8 shadow-lg border border-slate-200">Loading profile...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 py-10 px-4">
            <div className="mx-auto max-w-3xl rounded-3xl bg-white p-8 shadow-lg border border-slate-200">
                <div className="flex items-start justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900">Your Profile</h1>
                        <p className="text-sm text-slate-500">Manage your account information and session details.</p>
                    </div>
                    <button
                        onClick={logout}
                        className="rounded-2xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                    >
                        Logout
                    </button>
                </div>

                {error ? (
                    <div className="rounded-2xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                        {error}
                    </div>
                ) : null}

                {profile ? (
                    <div className="space-y-4">
                        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                            <p className="text-sm text-slate-500">Name</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900">{profile.name}</p>
                        </div>
                        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                            <p className="text-sm text-slate-500">Email</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900">{profile.email}</p>
                        </div>
                        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                            <p className="text-sm text-slate-500">Role</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900">{profile.role}</p>
                        </div>
                        <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                            <p className="text-sm text-slate-500">User ID</p>
                            <p className="mt-2 text-xs font-medium text-slate-600 break-all">{profile.id}</p>
                        </div>
                    </div>
                ) : (
                    <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6 text-sm text-slate-600">
                        No profile data available.
                    </div>
                )}
            </div>
        </div>
    );
}
