import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getProfile, updateProfile, deleteAccount } from "../services/auth";
import { Trash2, AlertTriangle } from "lucide-react";

const PRESETS_KEY = "promptPresets";

// load saved presets from localStorage
function loadPresets() {
    try { return JSON.parse(localStorage.getItem(PRESETS_KEY)) || []; }
    catch { return []; }
}

// profile page with system prompt editor and saved presets
export default function Profile() {
    const { token, logout, isAuthenticated } = useAuth();
    const [profile, setProfile] = useState(null);
    const [systemPrompt, setSystemPrompt] = useState("");
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const [presets, setPresets] = useState(loadPresets);
    const [presetName, setPresetName] = useState("");
    const navigate = useNavigate();

    useEffect(() => {
        if (!isAuthenticated) { navigate("/login"); return; }
        const load = async () => {
            try {
                const res = await getProfile(token);
                setProfile(res.user);
                setSystemPrompt(res.user.systemPrompt || "");
            } catch (err) {
                setError(err.message || "Unable to load profile.");
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [isAuthenticated, token, navigate]);

    const handleSavePrompt = async () => {
        try {
            await updateProfile(token, { systemPrompt });
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (err) {
            setError(err.message || "Failed to save.");
        }
    };

    // save current prompt as a named preset
    const savePreset = () => {
        if (!presetName.trim() || !systemPrompt.trim()) return;
        const updated = [...presets, { name: presetName.trim(), prompt: systemPrompt }];
        setPresets(updated);
        localStorage.setItem(PRESETS_KEY, JSON.stringify(updated));
        setPresetName("");
    };

    // load a preset into the editor
    const loadPreset = (p) => {
        setSystemPrompt(p.prompt);
    };

    // delete a preset
    const deletePreset = (idx) => {
        const updated = presets.filter((_, i) => i !== idx);
        setPresets(updated);
        localStorage.setItem(PRESETS_KEY, JSON.stringify(updated));
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950">
                <div className="rounded-3xl bg-white dark:bg-gray-900 p-8 shadow-lg border border-slate-200 dark:border-gray-800">Loading profile...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-gray-950 py-10 px-4">
            <div className="mx-auto max-w-3xl rounded-3xl bg-white dark:bg-gray-900 p-4 sm:p-8 shadow-lg border border-slate-200 dark:border-gray-800">
                <div className="flex flex-col sm:flex-row items-start justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-gray-100">Your Profile</h1>
                        <p className="text-sm text-slate-500 dark:text-gray-400">Manage your account and AI preferences.</p>
                    </div>
                    <button onClick={logout} className="rounded-2xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">Logout</button>
                </div>

                {error && (
                    <div className="rounded-2xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 px-4 py-3 text-sm text-red-700 dark:text-red-400 mb-4">{error}</div>
                )}

                {profile ? (
                    <div className="space-y-4">
                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-800/50 p-6">
                            <p className="text-sm text-slate-500 dark:text-gray-400">Name</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-gray-100">{profile.name}</p>
                        </div>
                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-800/50 p-6">
                            <p className="text-sm text-slate-500 dark:text-gray-400">Email</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-gray-100">{profile.email}</p>
                        </div>
                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-800/50 p-6">
                            <p className="text-sm text-slate-500 dark:text-gray-400">Role</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-gray-100">{profile.role}</p>
                        </div>

                        {/* system prompt editor with presets */}
                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-800/50 p-6">
                            <p className="text-sm text-slate-500 dark:text-gray-400 mb-1">System Prompt</p>
                            <p className="text-xs text-slate-400 dark:text-gray-500 mb-3">
                                Instructions prepended to every conversation. Reset by clearing the field and saving.
                            </p>
                            <textarea
                                value={systemPrompt}
                                onChange={(e) => setSystemPrompt(e.target.value)}
                                rows={4}
                                className="w-full rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm text-slate-900 dark:text-gray-100 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 dark:focus:ring-blue-900"
                                placeholder="e.g. You are a helpful coding assistant..."
                            />
                            <button
                                onClick={handleSavePrompt}
                                className="mt-3 rounded-2xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
                            >
                                {saved ? "Saved!" : "Save Prompt"}
                            </button>

                            {/* save as preset */}
                            <div className="mt-4 pt-4 border-t border-slate-200 dark:border-gray-700">
                                <p className="text-xs text-slate-500 dark:text-gray-400 mb-2">Save as preset</p>
                                <div className="flex gap-2">
                                    <input
                                        value={presetName}
                                        onChange={(e) => setPresetName(e.target.value)}
                                        placeholder="Preset name"
                                        className="flex-1 rounded-xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-xs text-slate-900 dark:text-gray-100 outline-none focus:border-blue-500"
                                    />
                                    <button onClick={savePreset} className="rounded-xl bg-blue-600 px-3 py-1.5 text-xs text-white hover:bg-blue-700 transition">Save</button>
                                </div>
                            </div>

                            {/* saved presets list */}
                            {presets.length > 0 && (
                                <div className="mt-3 space-y-1">
                                    {presets.map((p, idx) => (
                                        <div key={idx} className="flex items-center gap-2 text-xs">
                                            <button onClick={() => loadPreset(p)} className="flex-1 text-left px-3 py-1.5 rounded-lg bg-white dark:bg-gray-800 border border-slate-200 dark:border-gray-700 text-slate-700 dark:text-gray-300 hover:border-blue-400 transition truncate">
                                                {p.name}
                                            </button>
                                            <button onClick={() => deletePreset(idx)} className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/50 text-gray-400 hover:text-red-500 transition">
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-800/50 p-6">
                            <p className="text-sm text-slate-500 dark:text-gray-400">User ID</p>
                            <p className="mt-2 text-xs font-medium text-slate-600 dark:text-gray-400 break-all">{profile.id}</p>
                        </div>
                        {/* delete account */}
                        <div className="rounded-3xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/50 p-6">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle className="w-4 h-4 text-red-500" />
                                <p className="text-sm font-semibold text-red-700 dark:text-red-400">Danger Zone</p>
                            </div>
                            <p className="text-xs text-red-600 dark:text-red-400 mb-3">
                                Permanently delete your account and all associated data. This cannot be undone.
                            </p>
                            <button
                                onClick={async () => {
                                    if (!window.confirm("Are you sure you want to delete your account? This cannot be undone.")) return;
                                    try {
                                        await deleteAccount(token);
                                        logout();
                                        navigate("/");
                                    } catch (err) {
                                        setError(err.message || "Failed to delete account.");
                                    }
                                }}
                                className="rounded-2xl bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 transition"
                            >
                                Delete Account
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-800/50 p-6 text-sm text-slate-600 dark:text-gray-400">No profile data available.</div>
                )}
            </div>
        </div>
    );
}
