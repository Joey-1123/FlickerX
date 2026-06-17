import { useState } from "react";
import { Link } from "react-router-dom";
import {
    MessageSquare, Plus, Trash2, PanelLeftClose, Search, Settings, Cpu,
    Info, Phone, Moon, Sun, User, Shield, LogOut, LogIn, Folder, Tag,
} from "lucide-react";
import { MODELS, PREMIUM_MODEL_IDS, SECTION_LABELS } from "../utils/models";
import { useAuth } from "../auth/AuthContext";
import { useTheme } from "../context/ThemeContext";

// sidebar with history, model settings (temp sliders), user nav
export default function Sidebar({
    sessions, activeId, onSelect, onNew, onDelete, onClose, open,
    model, onModelChange, streamEnabled, onStreamToggle, userApiKey,
    temperature, onTemperatureChange, topP, onTopPChange,
    folderFilter, onFolderFilter,
}) {
    const { isAuthenticated, user, logout } = useAuth();
    const { dark, toggle } = useTheme();
    const [query, setQuery] = useState("");
    const [showSettings, setShowSettings] = useState(false);

    // collect unique folder tags from sessions
    const allTags = [...new Set(sessions.flatMap((s) => s.tags || []))];

    const filtered = query
        ? sessions.filter((s) => s.title.toLowerCase().includes(query.toLowerCase()))
        : folderFilter
            ? sessions.filter((s) => (s.tags || []).includes(folderFilter))
            : sessions;

    return (
        <>
            {open && <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />}
            <div
                className={`fixed top-0 left-0 h-full w-72 max-w-[85vw] bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 shadow-xl z-50 flex flex-col transition-transform duration-200 ${
                    open ? "translate-x-0" : "-translate-x-full"
                }`}
            >
                <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-800">
                    <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 tracking-wide uppercase">
                        History
                    </h2>
                    <div className="flex items-center gap-1">
                        <button onClick={onNew} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500" title="New chat">
                            <Plus className="w-4 h-4" />
                        </button>
                        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500" title="Close">
                            <PanelLeftClose className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* search + folder tags */}
                <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-800 space-y-2">
                    <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-gray-50 dark:bg-gray-800 text-sm">
                        <Search className="w-3.5 h-3.5 text-gray-400" />
                        <input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search history..."
                            className="flex-1 bg-transparent outline-none text-gray-700 dark:text-gray-300 placeholder:text-gray-400"
                        />
                    </div>
                    {/* folder tags */}
                    {allTags.length > 0 && (
                        <div className="flex gap-1 flex-wrap">
                            {onFolderFilter && folderFilter && (
                                <button
                                    onClick={() => onFolderFilter(null)}
                                    className="text-[10px] px-2 py-0.5 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
                                >
                                    All
                                </button>
                            )}
                            {allTags.map((tag) => (
                                <button
                                    key={tag}
                                    onClick={() => onFolderFilter?.(tag)}
                                    className={`text-[10px] px-2 py-0.5 rounded-full transition ${
                                        folderFilter === tag
                                            ? "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400"
                                            : "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
                                    }`}
                                >
                                    <Tag className="w-2.5 h-2.5 inline mr-0.5" />
                                    {tag}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                <div className="flex-1 overflow-y-auto py-2">
                    {filtered.length === 0 && (
                        <p className="text-xs text-gray-400 text-center mt-8">
                            {query ? "No matches" : "No conversations yet"}
                        </p>
                    )}
                    {filtered.map((s) => (
                        <div
                            key={s.id}
                            onClick={() => onSelect(s.id)}
                            className={`group flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors ${
                                s.id === activeId
                                    ? "bg-blue-50 dark:bg-blue-900/30 border-l-2 border-blue-600"
                                    : "hover:bg-gray-50 dark:hover:bg-gray-800/50 border-l-2 border-transparent"
                            }`}
                        >
                            <MessageSquare className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                            <div className="flex-1 min-w-0">
                                <p className="text-sm text-gray-700 dark:text-gray-300 truncate">{s.title}</p>
                                <p className="text-xs text-gray-400 mt-0.5">
                                    {new Date(s.updatedAt).toLocaleDateString(undefined, {
                                        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                                    })}
                                </p>
                                {/* tags on session */}
                                {s.tags?.length > 0 && (
                                    <div className="flex gap-1 mt-1">
                                        {s.tags.map((t) => (
                                            <span key={t} className="text-[9px] px-1.5 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-400">
                                                {t}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <button
                                onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}
                                className="p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-red-100 dark:hover:bg-red-900/50 transition-opacity"
                                title="Delete"
                            >
                                <Trash2 className="w-3.5 h-3.5 text-gray-400 hover:text-red-500" />
                            </button>
                        </div>
                    ))}
                </div>

                {/* bottom section — model settings + user nav */}
                <div className="border-t border-gray-100 dark:border-gray-800">
                    {/* model settings toggle */}
                    <button
                        onClick={() => setShowSettings((v) => !v)}
                        className="flex items-center gap-2 w-full px-4 py-3 text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                    >
                        <Settings className="w-3.5 h-3.5" />
                        Model Settings
                        <Cpu className="w-3.5 h-3.5 ml-auto" />
                    </button>
                    {showSettings && (
                        <div className="px-4 py-3 space-y-3 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
                            <div>
                                <label className="text-[10px] uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium">Model</label>
                                <select
                                    value={model}
                                    onChange={(e) => onModelChange(e.target.value)}
                                    className="mt-1 w-full text-xs rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-2 py-1.5 text-gray-700 dark:text-gray-300 outline-none focus:ring-1 focus:ring-blue-500"
                                >
                                    {Object.entries(MODELS).map(([key, models]) => (
                                        <optgroup key={key} label={SECTION_LABELS[key]}>
                                            {models.map((m) => (
                                                <option key={m.id} value={m.id}>
                                                    {m.name}{m.premium ? " (API Key)" : ""}
                                                </option>
                                            ))}
                                        </optgroup>
                                    ))}
                                </select>
                            </div>

                            {/* temperature slider */}
                            <div>
                                <label className="text-[10px] uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium">Temperature: {temperature?.toFixed(1)}</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="2"
                                    step="0.1"
                                    value={temperature ?? 0.7}
                                    onChange={(e) => onTemperatureChange?.(parseFloat(e.target.value))}
                                    className="w-full mt-1 accent-blue-500"
                                />
                            </div>

                            {/* top_p slider */}
                            <div>
                                <label className="text-[10px] uppercase tracking-wider text-gray-400 dark:text-gray-500 font-medium">Top P: {topP?.toFixed(1)}</label>
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.05"
                                    value={topP ?? 0.9}
                                    onChange={(e) => onTopPChange?.(parseFloat(e.target.value))}
                                    className="w-full mt-1 accent-blue-500"
                                />
                            </div>

                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={streamEnabled}
                                    onChange={onStreamToggle}
                                    className="rounded"
                                />
                                <span className="text-xs text-gray-500 dark:text-gray-400">Stream responses</span>
                            </label>
                            {PREMIUM_MODEL_IDS.has(model) && !userApiKey && (
                                <p className="text-[10px] text-amber-500">Key required -- /key set &lt;key&gt;</p>
                            )}
                            {userApiKey && (
                                <p className="text-[10px] text-green-500" title={userApiKey.slice(0, 7) + "..." + userApiKey.slice(-4)}>
                                    API key active
                                </p>
                            )}
                        </div>
                    )}
                </div>

                {/* user nav section */}
                <div className="border-t border-gray-100 dark:border-gray-800 px-3 py-3 space-y-1">
                    <Link to="/about" onClick={onClose} className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        <Info className="w-4 h-4" /> About
                    </Link>
                    <Link to="/contact" onClick={onClose} className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                        <Phone className="w-4 h-4" /> Contact
                    </Link>
                    <button onClick={toggle} className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left">
                        {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                        {dark ? "Light Mode" : "Dark Mode"}
                    </button>

                    {isAuthenticated ? (
                        <>
                            <div className="border-t border-gray-100 dark:border-gray-800 my-1" />
                            <div className="px-3 py-1.5 text-[10px] uppercase tracking-wider text-gray-400 font-medium">{user?.email || "User"}</div>
                            <Link to="/profile" onClick={onClose} className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                <User className="w-4 h-4" /> Profile
                            </Link>
                            {user?.role === "admin" && (
                                <Link to="/admin" onClick={onClose} className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                    <Shield className="w-4 h-4" /> Admin
                                </Link>
                            )}
                            <button onClick={logout} className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/50 transition-colors text-left">
                                <LogOut className="w-4 h-4" /> Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <div className="border-t border-gray-100 dark:border-gray-800 my-1" />
                            <Link to="/login" onClick={onClose} className="flex items-center gap-3 px-3 py-2 rounded-lg text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/50 transition-colors">
                                <LogIn className="w-4 h-4" /> Login
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </>
    );
}
