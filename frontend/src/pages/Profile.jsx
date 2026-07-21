import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getProfile, updateProfile, deleteAccount } from "../services/auth";
import { Trash2, AlertTriangle, ArrowLeft } from "lucide-react";
import { useTheme } from "../context/ThemeContext"; // Adjust path as needed

const PRESETS_KEY = "promptPresets";

// load saved presets from localStorage
function loadPresets() {
    try { return JSON.parse(localStorage.getItem(PRESETS_KEY)) || []; }
    catch { return []; }
}

// Helper to map accent strings to safe Tailwind classes
const getAccentClasses = (accent) => {
    const variants = {
        blue: { btnBg: "bg-blue-600", btnHover: "hover:bg-blue-700", focusBorder: "focus:border-blue-500", focusRing: "focus:ring-blue-100 dark:focus:ring-blue-900/30", hoverBorder: "hover:border-blue-400 dark:hover:border-blue-500", hoverBg: "hover:bg-blue-50 dark:hover:bg-blue-900/30", hoverText: "hover:text-blue-600 dark:hover:text-blue-400" },
        purple: { btnBg: "bg-purple-600", btnHover: "hover:bg-purple-700", focusBorder: "focus:border-purple-500", focusRing: "focus:ring-purple-100 dark:focus:ring-purple-900/30", hoverBorder: "hover:border-purple-400 dark:hover:border-purple-500", hoverBg: "hover:bg-purple-50 dark:hover:bg-purple-900/30", hoverText: "hover:text-purple-600 dark:hover:text-purple-400" },
        green: { btnBg: "bg-green-600", btnHover: "hover:bg-green-700", focusBorder: "focus:border-green-500", focusRing: "focus:ring-green-100 dark:focus:ring-green-900/30", hoverBorder: "hover:border-green-400 dark:hover:border-green-500", hoverBg: "hover:bg-green-50 dark:hover:bg-green-900/30", hoverText: "hover:text-green-600 dark:hover:text-green-400" },
        orange: { btnBg: "bg-orange-600", btnHover: "hover:bg-orange-700", focusBorder: "focus:border-orange-500", focusRing: "focus:ring-orange-100 dark:focus:ring-orange-900/30", hoverBorder: "hover:border-orange-400 dark:hover:border-orange-500", hoverBg: "hover:bg-orange-50 dark:hover:bg-orange-900/30", hoverText: "hover:text-orange-600 dark:hover:text-orange-400" },
        pink: { btnBg: "bg-pink-600", btnHover: "hover:bg-pink-700", focusBorder: "focus:border-pink-500", focusRing: "focus:ring-pink-100 dark:focus:ring-pink-900/30", hoverBorder: "hover:border-pink-400 dark:hover:border-pink-500", hoverBg: "hover:bg-pink-50 dark:hover:bg-pink-900/30", hoverText: "hover:text-pink-600 dark:hover:text-pink-400" },
        teal: { btnBg: "bg-teal-600", btnHover: "hover:bg-teal-700", focusBorder: "focus:border-teal-500", focusRing: "focus:ring-teal-100 dark:focus:ring-teal-900/30", hoverBorder: "hover:border-teal-400 dark:hover:border-teal-500", hoverBg: "hover:bg-teal-50 dark:hover:bg-teal-900/30", hoverText: "hover:text-teal-600 dark:hover:text-teal-400" },
    };
    return variants[accent] || variants.blue;
};

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

    // Theme context
    const { accent, colors } = useTheme();
    const themeStyles = getAccentClasses(accent);
    const ringClass = colors[accent]?.ring || "ring-blue-500";

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
            <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0a0a0a] transition-colors duration-300">
                <div className="rounded-3xl bg-white dark:bg-[#111111] p-8 shadow-lg border border-slate-200 dark:border-gray-800 text-gray-900 dark:text-gray-100">Loading profile...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-[#0a0a0a] py-10 px-4 transition-colors duration-300">
            <div className="mx-auto max-w-3xl rounded-3xl bg-white dark:bg-[#111111] p-4 sm:p-8 shadow-lg border border-slate-200 dark:border-gray-800 transition-colors duration-300">
                <div className="flex flex-col sm:flex-row items-start justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-gray-100 transition-colors duration-300">Your Profile</h1>
                        <p className="text-sm text-slate-500 dark:text-gray-400 transition-colors duration-300">Manage your account and AI preferences.</p>
                    </div>
                    <button
                        onClick={logout}
                        className={`rounded-2xl px-4 py-2 text-sm font-semibold text-white transition-colors duration-300 ${themeStyles.btnBg} ${themeStyles.btnHover}`}
                    >
                        Logout
                    </button>
                </div>

                {error && (
                    <div className="rounded-2xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 px-4 py-3 text-sm text-red-700 dark:text-red-400 mb-4 transition-colors duration-300">{error}</div>
                )}

                {profile ? (
                    <div className="space-y-4">
                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-[#0a0a0a] p-6 transition-colors duration-300">
                            <p className="text-sm text-slate-500 dark:text-gray-400">Name</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-gray-100">{profile.name}</p>
                        </div>
                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-[#0a0a0a] p-6 transition-colors duration-300">
                            <p className="text-sm text-slate-500 dark:text-gray-400">Email</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-gray-100">{profile.email}</p>
                        </div>
                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-[#0a0a0a] p-6 transition-colors duration-300">
                            <p className="text-sm text-slate-500 dark:text-gray-400">Role</p>
                            <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-gray-100">{profile.role}</p>
                        </div>

                        {/* system prompt editor with presets */}
                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-[#0a0a0a] p-6 transition-colors duration-300">
                            <p className="text-sm text-slate-500 dark:text-gray-400 mb-1">System Prompt</p>
                            <p className="text-xs text-slate-400 dark:text-gray-500 mb-3">
                                Instructions prepended to every conversation. Reset by clearing the field and saving.
                            </p>
                            <textarea
                                value={systemPrompt}
                                onChange={(e) => setSystemPrompt(e.target.value)}
                                rows={4}
                                className={`w-full rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-[#111111] px-4 py-3 text-sm text-slate-900 dark:text-gray-100 focus:outline-none focus:ring-2 transition-all duration-300 ${themeStyles.focusBorder} ${themeStyles.focusRing}`}
                                placeholder="e.g. You are a helpful coding assistant..."
                            />
                            <button
                                onClick={handleSavePrompt}
                                className={`mt-3 rounded-2xl px-4 py-2 text-sm font-semibold text-white transition-colors duration-300 ${themeStyles.btnBg} ${themeStyles.btnHover}`}
                            >
                                {saved ? "Saved!" : "Save Prompt"}
                            </button>

                            {/* save as preset */}
                            <div className="mt-4 pt-4 border-t border-slate-200 dark:border-gray-800 transition-colors duration-300">
                                <p className="text-xs text-slate-500 dark:text-gray-400 mb-2">Save as preset</p>
                                <div className="flex gap-2">
                                    <input
                                        value={presetName}
                                        onChange={(e) => setPresetName(e.target.value)}
                                        placeholder="Preset name"
                                        className={`flex-1 rounded-xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-[#111111] px-3 py-1.5 text-xs text-slate-900 dark:text-gray-100 outline-none transition-colors duration-300 ${themeStyles.focusBorder}`}
                                    />
                                    <button
                                        onClick={savePreset}
                                        className={`rounded-xl px-3 py-1.5 text-xs text-white transition-colors duration-300 ${themeStyles.btnBg} ${themeStyles.btnHover}`}
                                    >
                                        Save
                                    </button>
                                </div>
                            </div>

                            {/* saved presets list */}
                            {presets.length > 0 && (
                                <div className="mt-3 space-y-1">
                                    {presets.map((p, idx) => (
                                        <div key={idx} className="flex items-center gap-2 text-xs">
                                            <button
                                                onClick={() => loadPreset(p)}
                                                className={`flex-1 text-left px-3 py-1.5 rounded-lg bg-white dark:bg-[#111111] border border-slate-200 dark:border-gray-700 text-slate-700 dark:text-gray-300 transition-colors duration-300 truncate ${themeStyles.hoverBorder}`}
                                            >
                                                {p.name}
                                            </button>
                                            <button
                                                onClick={() => deletePreset(idx)}
                                                className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-500 transition-colors duration-300"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-[#0a0a0a] p-6 transition-colors duration-300">
                            <p className="text-sm text-slate-500 dark:text-gray-400">User ID</p>
                            <p className="mt-2 text-xs font-medium text-slate-600 dark:text-gray-400 break-all">{profile.id}</p>
                        </div>

                        {/* delete account - Left hardcoded to RED for danger UI */}
                        <div className="rounded-3xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/20 p-6 transition-colors duration-300">
                            <div className="flex items-center gap-2 mb-2">
                                <AlertTriangle className="w-4 h-4 text-red-500" />
                                <p className="text-sm font-semibold text-red-700 dark:text-red-400">Danger Zone</p>
                            </div>
                            <p className="text-xs text-red-600 dark:text-red-400/80 mb-3">
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
                                className="rounded-2xl bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 transition-colors duration-300"
                            >
                                Delete Account
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-[#0a0a0a] p-6 text-sm text-slate-600 dark:text-gray-400 transition-colors duration-300">No profile data available.</div>
                )}
            </div>

            {/* Back Button */}
            <div className="flex justify-center w-full max-w-3xl ml-auto mr-auto mt-6">
                <button
                    onClick={() => navigate(-1)}
                    className={`flex items-center px-5 py-2.5 bg-white dark:bg-[#111111] border border-gray-200 dark:border-gray-800 text-sm font-medium text-gray-600 dark:text-gray-400 rounded-full shadow-sm hover:border-transparent transition-all duration-200 focus:outline-none focus:ring-2 ${themeStyles.hoverBg} ${themeStyles.hoverText} ${ringClass}`}
                    aria-label="Go back to previous page"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Go Back
                </button>
            </div>
        </div>
    );
}