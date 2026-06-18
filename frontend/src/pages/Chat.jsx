import { useEffect, useState, useRef, useCallback } from "react";
import { Navigate } from "react-router-dom";
import ChatNavbar from "../components/Navbar";
import ChatBox from "../components/ChatBox";
import ChatInput from "../components/ChatInput";
import CommandPalette from "../components/CommandPalette";
import ShortcutsModal from "../components/ShortcutsModal";
import Sidebar from "../components/Sidebar";
import { useAuth } from "../auth/AuthContext";
import { sendMessageToBackend, streamChat, uploadFile } from "../services/api";
import { getProfile } from "../services/auth";
import {
    getSessions, getActiveSessionId, setActiveSessionId,
    createSession, updateSession, deleteSession, generateTitle,
} from "../utils/sessions";
import { ALL_MODELS, PREMIUM_MODEL_IDS, VISION_MODELS } from "../utils/models";
import { useTheme, ACCENT_COLORS } from "../context/ThemeContext";

// rough token estimate: ~4 chars per token
function estimateTokens(text) {
    return Math.ceil((text || "").length / 4);
}

export default function Chat() {
    const { token, isAuthenticated, user } = useAuth();
    const { accent, setAccent, ACCENTS } = useTheme();

    const [sessions, setSessions] = useState([]);
    const [activeId, setActiveId] = useState(null);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [toast, setToast] = useState(null);
    const toastTimeoutRef = useRef(null);
    const showToast = (msg, duration = 2000) => {
        clearTimeout(toastTimeoutRef.current);
        setToast(msg);
        toastTimeoutRef.current = setTimeout(() => setToast(null), duration);
    };
    const [isCommandOpen, setIsCommandOpen] = useState(false);
    const [showShortcuts, setShowShortcuts] = useState(false);
    const [input, setInput] = useState("");
    const [file, setFile] = useState(null);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [model, setModel] = useState(() => {
        const stored = localStorage.getItem("selectedModel");
        if (stored && !PREMIUM_MODEL_IDS.has(stored)) return stored;
        const firstFree = ALL_MODELS.find((m) => !m.premium);
        return firstFree ? firstFree.id : ALL_MODELS[0].id;
    });
    const [streamEnabled, setStreamEnabled] = useState(true);
    const [systemPrompt, setSystemPrompt] = useState("");
    const [userApiKey, setUserApiKey] = useState(() => localStorage.getItem("userApiKey") || "");
    const [pinnedIds, setPinnedIds] = useState(() => {
        try { return new Set(JSON.parse(localStorage.getItem("pinnedIds") || "[]")); }
        catch { return new Set(); }
    });
    const [temperature, setTemperature] = useState(0.7);
    const [topP, setTopP] = useState(0.9);
    const [folderFilter, setFolderFilter] = useState(null);
    const uid = user?.id;

    // persist pinned IDs
    useEffect(() => {
        localStorage.setItem("pinnedIds", JSON.stringify([...pinnedIds]));
    }, [pinnedIds]);

    // load system prompt
    useEffect(() => {
        if (!token) return;
        getProfile(token).then((res) => setSystemPrompt(res.user?.systemPrompt || "")).catch(() => {});
    }, [token]);

    // persist model choice
    useEffect(() => { localStorage.setItem("selectedModel", model); }, [model]);

    // load or initialise sessions
    useEffect(() => {
        if (!uid) return;
        const stored = getSessions(uid);
        let active = getActiveSessionId(uid);
        if (active && !stored.find((s) => s.id === active)) active = null;
        if (!active && stored.length > 0) active = stored[0].id;
        if (!active) {
            const s = createSession(uid);
            setSessions([s]); setActiveId(s.id); setMessages([]);
            return;
        }
        setActiveId(active); setActiveSessionId(uid, active);
        setSessions(stored); setMessages(stored.find((s) => s.id === active)?.messages ?? []);
    }, [uid]);

    // persist messages
    const lastSaved = useRef(null);
    useEffect(() => {
        if (!uid || !activeId) return;
        if (lastSaved.current === messages) return;
        lastSaved.current = messages;
        const title = generateTitle(messages);
        const updated = updateSession(uid, activeId, { messages, title });
        if (updated) setSessions((prev) => prev.map((s) => (s.id === activeId ? updated : s)));
    }, [messages, activeId, uid]);

    // helpers
    const switchSession = (id) => {
        const s = sessions.find((x) => x.id === id);
        if (!s) return;
        setActiveId(id); setActiveSessionId(uid, id); setMessages(s.messages); setSidebarOpen(false);
    };

    const newSession = () => {
        const s = createSession(uid);
        setSessions((prev) => [...prev, s]); setActiveId(s.id); setMessages([]); setSidebarOpen(false);
    };

    const removeSession = (id) => {
        const remaining = deleteSession(uid, id);
        setSessions(remaining);
        if (activeId === id) {
            if (remaining.length > 0) {
                const next = remaining[0]; setActiveId(next.id); setActiveSessionId(uid, next.id); setMessages(next.messages);
            } else {
                const s = createSession(uid); setSessions([s]); setActiveId(s.id); setMessages([]);
            }
        }
    };

    const clearChat = () => {
        if (messages.length === 0) return;
        if (!window.confirm("Clear all messages in this chat?")) return;
        setMessages([]);
    };

    // build messages with system prompt
    const buildMessages = useCallback((history) => {
        const msgs = systemPrompt?.trim()
            ? [{ role: "system", content: systemPrompt.trim() }, ...history]
            : history;
        return msgs;
    }, [systemPrompt]);

    // core send function (supports streaming)
    const doSend = async (history, fileUrl, editingId) => {
        const msgs = buildMessages(history);
        let reply = "";
        let replyId = Date.now() + 1;

        if (editingId) {
            // edit mode: replace the assistant reply that follows the edited message
        }

        if (streamEnabled) {
            setMessages((prev) => [...prev, { role: "assistant", content: "", id: replyId }]);

            const fullReply = await streamChat(msgs, token, fileUrl, model, (chunk) => {
                reply += chunk;
                setMessages((prev) =>
                    prev.map((m) => (m.id === replyId ? { ...m, content: reply } : m))
                );
            }, userApiKey);

            setMessages((prev) =>
                prev.map((m) => (m.id === replyId ? { ...m, content: fullReply || reply } : m))
            );
        } else {
            const res = await sendMessageToBackend(msgs, token, fileUrl, model, userApiKey);
            reply = res.reply;
            setMessages((prev) => [...prev, { role: "assistant", content: reply, id: replyId }]);
        }
    };

    // Handle /key command locally
    const handleKeyCommand = (input) => {
        const parts = input.trim().split(/\s+/);
        const cmd = parts[0]?.toLowerCase();
        if (cmd === "/key" && parts[1] === "set" && parts[2]) {
            const key = parts.slice(2).join(" ");
            localStorage.setItem("userApiKey", key);
            setUserApiKey(key);
            showToast("API key saved");
            return true;
        }
        if (cmd === "/key" && parts[1] === "clear") {
            localStorage.removeItem("userApiKey");
            setUserApiKey("");
            showToast("API key cleared");
            return true;
        }
        if (cmd === "/key" && parts[1] === "status") {
            const stored = localStorage.getItem("userApiKey");
            const display = stored ? `${stored.slice(0, 7)}...${stored.slice(-4)}` : "not set";
            showToast(`API key: ${display}`, 3000);
            return true;
        }
        return false;
    };

    const handleSend = async (input, file) => {
        if (isLoading) return;
        if (!isAuthenticated) return;
        if (!input.trim() && !file) return;

        if (input.trim().startsWith("/key")) {
            handleKeyCommand(input);
            return;
        }

        if (PREMIUM_MODEL_IDS.has(model) && !userApiKey) {
            showToast("Premium models require an API key. Use /key set <your-key>", 4000);
            return;
        }

        setIsLoading(true);

        try {
            let previewUrl = null;
            if (file) previewUrl = URL.createObjectURL(file);

            const tempId = Date.now();
            setMessages((prev) => [...prev, { id: tempId, role: "user", content: input, image: previewUrl }]);

            let fileUrl = null;
            if (file) fileUrl = await uploadFile(file, token);
            if (!isAuthenticated || !token) throw new Error("Authentication failed");

            const history = [...messages, { role: "user", content: input }];
            await doSend(history, fileUrl, null);

            if (file && fileUrl) {
                setMessages((prev) => prev.map((m) => (m.image === previewUrl ? { ...m, image: fileUrl } : m)));
            }

            setInput("");
            setFile(null);
        } catch (error) {
            const msg = error.message?.includes("Too many")
                ? "You're sending messages too fast. Please wait a bit."
                : error.message;
            setMessages((prev) => [...prev, { role: "assistant", content: msg, id: Date.now() + 2 }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRegenerate = async () => {
        if (isLoading) return;
        const lastUserIdx = [...messages].reverse().findIndex((m) => m.role === "user");
        if (lastUserIdx === -1) return;
        const idx = messages.length - 1 - lastUserIdx;
        if (idx < 0) return;

        setIsLoading(true);
        try {
            const history = messages.slice(0, idx + 1);
            setMessages(history);
            await doSend(history, null, null);
        } catch (error) {
            setMessages((prev) => [...prev, { role: "assistant", content: error.message, id: Date.now() + 2 }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEdit = async (newContent) => {
        if (isLoading) return;
        const lastUserIdx = [...messages].reverse().findIndex((m) => m.role === "user");
        if (lastUserIdx === -1) return;
        setIsLoading(true);
        try {
            const idx = messages.length - 1 - lastUserIdx;

            const history = messages.slice(0, idx).concat([{ role: "user", content: newContent }]);
            setMessages(history);
            await doSend(history, null, null);
        } catch (error) {
            setMessages((prev) => [...prev, { role: "assistant", content: error.message, id: Date.now() + 2 }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleExport = () => {
        const lines = messages.map((m) => {
            const tag = m.role === "user" ? "**You**" : "**FlickerX**";
            const img = m.image ? `\n![Image](${m.image})` : "";
            const pin = pinnedIds.has(m.id) ? " [PINNED]" : "";
            return `${tag}: ${m.content}${img}${pin}`;
        });
        const md = `# Chat Export\n\n${lines.join("\n\n")}`;
        const blob = new Blob([md], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = `chat-${new Date().toISOString().slice(0, 10)}.md`; a.click();
        URL.revokeObjectURL(url);
    };

    const handleCopy = async (text) => {
        try { await navigator.clipboard.writeText(text); showToast("Copied!"); }
        catch { showToast("Failed to copy!"); }
    };

    // toggle pin state for a message
    const handleTogglePin = (msgId) => {
        setPinnedIds((prev) => {
            const next = new Set(prev);
            if (next.has(msgId)) next.delete(msgId);
            else next.add(msgId);
            return next;
        });
    };

    // command palette
    useEffect(() => {
        const handler = (e) => {
            const el = document.activeElement;
            if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA")) return;
            if (e.key === "/") { e.preventDefault(); setIsCommandOpen(true); }
            if (e.key === "?" || (e.ctrlKey && e.key === "/")) { e.preventDefault(); setShowShortcuts(true); }
            if (e.key === "Escape") { setIsCommandOpen(false); setShowShortcuts(false); }
        };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, []);

    const handleSelectCommand = (cmd) => {
        setInput(`Help me with: ${cmd}`); setIsCommandOpen(false);
        setTimeout(() => document.getElementById("chat-input")?.focus(), 100);
    };

    // context window token count
    const totalTokens = messages.reduce((sum, m) => sum + estimateTokens(m.content) + estimateTokens(m.image), 0);
    const maxTokens = 128000;
    const tokenPct = Math.min((totalTokens / maxTokens) * 100, 100);

    if (!isAuthenticated) return <Navigate to="/login" replace />;

    return (
        <>
            {toast && (
                <div className="fixed top-4 sm:top-20 left-1/2 -translate-x-1/2 bg-black backdrop-blur-md text-white text-sm px-4 py-2 rounded-xl shadow-xl border border-white/10 animate-toast z-50">
                    {toast}
                </div>
            )}

            <Sidebar
                sessions={sessions} activeId={activeId} onSelect={switchSession}
                onNew={newSession} onDelete={removeSession} onClose={() => setSidebarOpen(false)}
                open={sidebarOpen}
                model={model} onModelChange={setModel}
                streamEnabled={streamEnabled} onStreamToggle={() => setStreamEnabled((v) => !v)}
                userApiKey={userApiKey}
                temperature={temperature} onTemperatureChange={setTemperature}
                topP={topP} onTopPChange={setTopP}
                folderFilter={folderFilter} onFolderFilter={setFolderFilter}
            />
            <ShortcutsModal open={showShortcuts} onClose={() => setShowShortcuts(false)} />

            <div className="flex flex-col h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">
                <CommandPalette open={isCommandOpen} onClose={() => setIsCommandOpen(false)} onSelect={handleSelectCommand} />

                <ChatNavbar clearChat={clearChat} onToggleSidebar={() => setSidebarOpen((v) => !v)} onNewChat={newSession} onExport={handleExport} />

                <div className="flex-1 flex flex-col overflow-hidden">
                    <ChatBox messages={messages} isLoading={isLoading} user={user} onCopy={handleCopy} onRegenerate={handleRegenerate} onEdit={handleEdit} onTogglePin={handleTogglePin} pinnedIds={pinnedIds} />
                </div>

                <ChatInput input={input} setInput={setInput} onSend={handleSend} file={file} setFile={setFile} supportsVision={VISION_MODELS.has(model)} />

                {/* footer with token counter and accent color picker */}
                <footer className="flex items-center justify-between text-black dark:text-gray-400 text-xs py-2 px-4 border-t border-gray-100/80 dark:border-gray-800 bg-white/70 dark:bg-gray-900/70 backdrop-blur-md">
                    <div className="flex items-center gap-3">
                        {/* token context indicator */}
                        <span className="text-[10px] text-gray-400 dark:text-gray-500" title={`${totalTokens.toLocaleString()} / ${maxTokens.toLocaleString()} tokens`}>
                            {tokenPct.toFixed(0)}% context
                        </span>
                        <div className="w-20 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                            <div
                                className="h-full rounded-full transition-all duration-300"
                                style={{ width: `${tokenPct}%`, backgroundColor: tokenPct > 80 ? "#ef4444" : "#3b82f6" }}
                            />
                        </div>
                    </div>

                    <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-gray-400">Theme:</span>
                        {ACCENTS.map((c) => (
                            <button
                                key={c}
                                onClick={() => setAccent(c)}
                                className={`w-4 h-4 rounded-full transition-all ${
                                    accent === c ? "ring-2 ring-offset-2 ring-gray-400 dark:ring-gray-500 scale-110" : "hover:scale-110"
                                }`}
                                style={{ backgroundColor: ACCENT_COLORS[c].hex }}
                                title={c}
                            />
                        ))}
                    </div>

                    <button onClick={() => setShowShortcuts(true)} className="underline text-blue-500 hover:text-blue-600">Shortcuts</button>
                </footer>
            </div>
        </>
    );
}
