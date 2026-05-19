// This component renders the chat box where messages are displayed. It handles auto-scrolling to the latest message and shows a typing indicator when the AI is generating a response.
import { useEffect, useRef, useState } from "react";
import Message from "./Message";
import EmptyState from "./EmptyState";
import { Sparkles } from "lucide-react";

export default function ChatBox({ messages, isLoading, onCopy, copiedId }) {
    const containerRef = useRef(null);
    const bottomRef = useRef(null);
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

    const handleScroll = () => {
        const el = containerRef.current;
        if (!el) return;

        const threshold = 100;
        const isNearBottom =
            el.scrollHeight - el.scrollTop - el.clientHeight < threshold;

        setShouldAutoScroll(isNearBottom);
    };

    useEffect(() => {
        if (shouldAutoScroll) {
            bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, shouldAutoScroll]);

    return (
        <div
            ref={containerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto px-6 py-10 bg-white scroll-smooth selection:bg-blue-200"
        >

            {/* Empty state */}
            {messages.length === 0 && (
                <EmptyState />
            )}

            {/* Messages */}
            <div className="max-w-4xl mx-auto space-y-6 w-full">
                {messages.map((msg, index) => (
                    <Message
                        key={msg.id}
                        id={msg.id}
                        role={msg.role}
                        content={msg.content}
                        image={msg.image}
                        onCopy={onCopy}
                        copiedId={copiedId}
                    />
                ))}

                {/* Typing indicator */}
                {isLoading && (
                    <div className="flex items-center gap-3 px-5 py-3.5 rounded-2xl bg-gray-100 border border-gray-200 shadow-sm max-w-fit animate-pulse">
                        <div className="h-2 w-2 rounded-full bg-blue-500 animate-bounce"></div>
                        <div className="h-2 w-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.2s]"></div>
                        <div className="h-2 w-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0.4s]"></div>

                        <span className="text-blue-600 text-xs font-medium tracking-wide uppercase">
                            FlickerX is thinking...
                        </span>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>
        </div>
    );
}