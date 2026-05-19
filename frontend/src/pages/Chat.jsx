// Chat.jsx - Main chat interface component
import { useEffect, useState } from "react";
import ChatNavbar from "../components/Navbar";
import ChatBox from "../components/ChatBox";
import ChatInput from "../components/ChatInput";
import CommandPalette from "../components/CommandPalette";
import { useAuth, useUser } from "@clerk/clerk-react";
import { sendMessageToBackend, uploadFile } from "../services/api";

export default function Chat() {

    const { getToken, isSignedIn } = useAuth();// authentication hooks from Clerk
    const { user } = useUser();// user data from Clerk


    const [messages, setMessages] = useState([]);// chat messages state
    const [isLoading, setIsLoading] = useState(false);// loading state for async operations
    const [copiedId, setCopiedId] = useState(null); // state to track which message ID was copied for feedback purposes
    const [toast, setToast] = useState(null);

    const [isCommandOpen, setIsCommandOpen] = useState(false);
    const [input, setInput] = useState(""); // text input state
    const [file, setFile] = useState(null); // file input state
    const [loading, setLoading] = useState(false);


    useEffect(() => {
        const savedMessages = localStorage.getItem("chatMessages");
        if (savedMessages) {
            setMessages(JSON.parse(savedMessages));
        }
    }, []);

    useEffect(() => {
        localStorage.setItem("chatMessages", JSON.stringify(messages));
    }, [messages]);

    // Command palette
    useEffect(() => {
        const handleKeyDown = (e) => {
            const activeElement = document.activeElement;
            const isTyping =
                activeElement &&
                (activeElement.tagName === "INPUT" ||
                    activeElement.tagName === "TEXTAREA");

            if (isTyping) return;

            if (e.key === "/") {
                e.preventDefault();
                setIsCommandOpen(true);
            }

            if (e.key === "Escape") {
                setIsCommandOpen(false);
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, []);

    const handleSelectCommand = (cmd) => {
        setInput(`Help me with: ${cmd}`);
        setIsCommandOpen(false);

        setTimeout(() => {
            document.getElementById("chat-input")?.focus();
        }, 100);
    };

    // Handle sending messages, including text and optional file uploads. This function also manages optimistic UI updates for a smoother user experience.
    const handleSend = async (input, file) => {
        // 🚨 Prevent spam clicks
        if (isLoading) return;

        try {
            if (!isSignedIn) return;
            if (!input.trim() && !file) return;

            setIsLoading(true); // ✅ single source of truth

            // 🟣 IMAGE GENERATION FLOW
            if (input.trim().toLowerCase().startsWith("/image")) {
                console.log("✅ IMAGE FLOW TRIGGERED:", input);

                const prompt = input.trim().substring(6).trim();

                // add user message
                setMessages((prev) => [
                    ...prev,
                    {
                        id: Date.now(),
                        role: "user",
                        content: input,
                    }
                ]);

                try {
                    const { image } = await generateImage(prompt);

                    setMessages((prev) => [
                        ...prev,
                        {
                            id: Date.now() + 1,
                            role: "assistant",
                            content: `Here’s your image for: "${prompt}"`,
                            image: image,
                        }
                    ]);

                } catch (error) {
                    setMessages((prev) => [
                        ...prev,
                        {
                            id: Date.now() + 2,
                            role: "assistant",
                            content: `⚠️ ${error.message}`,
                        }
                    ]);
                }

                return; // ✅ exit early (outer finally will handle loading)
            }

            // 🔵 NORMAL CHAT FLOW

            let previewUrl = null;

            if (file) {
                previewUrl = URL.createObjectURL(file);
            }

            // add user message
            setMessages((prev) => [
                ...prev,
                {
                    id: Date.now(),
                    role: "user",
                    content: input,
                    image: previewUrl
                }
            ]);

            const token = await getToken();
            if (!token) throw new Error("Authentication failed");

            let fileUrl = null;

            if (file) {
                fileUrl = await uploadFile(file);
            }

            const { reply } = await sendMessageToBackend(input, token, fileUrl);

            // replace preview image with uploaded image
            if (file && fileUrl) {
                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.image === previewUrl
                            ? { ...msg, image: fileUrl }
                            : msg
                    )
                );
            }

            // add assistant reply
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: reply,
                    id: Date.now() + 1
                }
            ]);

            // clear input
            setInput("");
            setFile(null);

        } catch (error) {
            let message = error.message;

            if (message?.includes("Too many")) {
                message = "You're sending messages too fast. Please wait a bit.";
            }

            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: `⚠️ ${message}`,
                    id: Date.now() + 2
                }
            ]);

        } finally {
            setIsLoading(false); // ✅ ALWAYS runs once
        }
    };

    // Copy to clipboard function with feedback
    const handleCopy = async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            setToast("Copied!!");
        } catch {
            setToast("Failed to copy!");
        }

        setTimeout(() => setToast(null), 2000);
    };

    // Clear chat function with confirmation
    const clearChat = () => {
        if (messages.length === 0) {
            alert("No chat to clear");
            return;
        }

        const confirmClear = window.confirm("Are you sure you want to clear all chats?");
        if (!confirmClear) return;

        setMessages([]);
        localStorage.removeItem("chatMessages");
    };

    return (
        <>
            {toast && (
                <div className="fixed top-20 left-1/2 -translate-x-1/2 bg-black backdrop-blur-md text-white text-sm px-4 py-2 rounded-xl shadow-xl border border-white/10 animate-toast z-50">
                    {toast}
                </div>
            )}

            <div className="flex flex-col h-screen bg-white text-gray-900">

                <CommandPalette
                    open={isCommandOpen}
                    onClose={() => setIsCommandOpen(false)}
                    onSelect={handleSelectCommand}
                />

                <ChatNavbar clearChat={clearChat} />

                <div className="flex-1 flex flex-col overflow-hidden">
                    <ChatBox
                        messages={messages}
                        isLoading={isLoading}
                        user={user}
                        onCopy={handleCopy}

                    />
                </div>

                {/* ChatInput handles file selection */}
                <ChatInput
                    input={input}
                    setInput={setInput}
                    onSend={handleSend}
                    file={file}
                    setFile={setFile}
                />

                <footer className="text-center text-black text-xs py-4 border-t border-gray-100/80 bg-white/70 backdrop-blur-md">
                    &copy; {new Date().getFullYear()} FlickerX. All rights reserved.
                </footer>
            </div>
        </>
    );

}
