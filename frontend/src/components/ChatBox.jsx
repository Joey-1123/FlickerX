import { useEffect, useRef, useState } from "react";
import Message from "./Message";
import EmptyState from "./EmptyState";
import { Search, Star, Bot } from "lucide-react";

// displays messages with search, pin support, typing indicator, animated entry
export default function ChatBox({ messages, isLoading, onCopy, onRegenerate, onEdit, onTogglePin, user, pinnedIds }) {
    const containerRef = useRef(null);
    const bottomRef = useRef(null);
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [showPinnedOnly, setShowPinnedOnly] = useState(false);

    const handleScroll = () => {
        const el = containerRef.current;
        if (!el) return;
        setShouldAutoScroll(el.scrollHeight - el.scrollTop - el.clientHeight < 100);
    };

    useEffect(() => {
        if (shouldAutoScroll) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, shouldAutoScroll]);

    // filter messages by search or pinned
    let displayed = messages;
    if (showPinnedOnly) {
        displayed = displayed.filter((m) => pinnedIds?.has(m.id));
    }
    if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        displayed = displayed.filter((m) => m.content?.toLowerCase().includes(q));
    }

    const pinnedCount = pinnedIds?.size || 0;

    return (
        <div ref={containerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto px-4 sm:px-6 py-10 bg-white dark:bg-gray-950 scroll-smooth">
            {messages.length === 0 ? (
                <EmptyState />
            ) : (
                <>
                    {/* search bar */}
                    <div className="max-w-4xl mx-auto mb-4 flex items-center gap-2">
                        <div className="flex-1 flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-sm">
                            <Search className="w-3.5 h-3.5 text-gray-400" />
                            <input
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search messages..."
                                className="flex-1 bg-transparent outline-none text-gray-700 dark:text-gray-300 placeholder:text-gray-400 text-xs"
                            />
                        </div>
                        {pinnedCount > 0 && (
                            <button
                                onClick={() => setShowPinnedOnly((v) => !v)}
                                className={`flex items-center gap-1 text-xs px-3 py-1.5 rounded-xl border transition ${
                                    showPinnedOnly
                                        ? "bg-yellow-50 dark:bg-yellow-900/30 border-yellow-300 text-yellow-700 dark:text-yellow-400"
                                        : "border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800"
                                }`}
                            >
                                <Star className="w-3 h-3" /> {pinnedCount}
                            </button>
                        )}
                    </div>

                    <div className="max-w-4xl mx-auto space-y-6 w-full">
                        {displayed.map((msg, idx) => (
                            <div key={msg.id} style={{ animationDelay: `${idx * 50}ms` }}>
                                <Message
                                    role={msg.role}
                                    content={msg.content}
                                    image={msg.image}
                                    user={user}
                                    onCopy={onCopy}
                                    onRegenerate={msg.role === "assistant" && !isLoading ? onRegenerate : undefined}
                                    onEdit={msg.role === "user" && !isLoading ? onEdit : undefined}
                                    pinned={pinnedIds?.has(msg.id)}
                                    onTogglePin={onTogglePin ? () => onTogglePin(msg.id) : undefined}
                                />
                            </div>
                        ))}

                        {/* typing indicator with animated avatar */}
                        {isLoading && (
                            <div className="flex items-start gap-3 animate-fade-in">
                                <div className="w-8 h-8 rounded-full bg-gray-700 dark:bg-gray-600 flex items-center justify-center flex-shrink-0 animate-pulse">
                                    <Bot className="h-4 w-4 text-white" />
                                </div>
                                <div className="flex items-center gap-3 px-5 py-3.5 rounded-2xl bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm">
                                    <div className="h-2 w-2 rounded-full bg-blue-500 animate-bounce"></div>
                                    <div className="h-2 w-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.2s]"></div>
                                    <div className="h-2 w-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.4s]"></div>
                                    <span className="text-blue-600 dark:text-blue-400 text-xs font-medium tracking-wide uppercase">FlickerX is thinking...</span>
                                </div>
                            </div>
                        )}

                        <div ref={bottomRef} />
                    </div>
                </>
            )}
        </div>
    );
}
