import { useEffect, useRef, useState, useCallback } from "react";
import { Send, Paperclip, EyeOff, Mic, MicOff, Sparkles } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { ACCENT_COLORS } from "../context/ThemeContext";

// preset templates for quick selection
const TEMPLATES = [
    { label: "Explain", text: "Explain this in simple terms:" },
    { label: "Fix", text: "/fix" },
    { label: "Summarize", text: "/summarize" },
    { label: "Code", text: "/code" },
];

// shows warning when model doesnt support image input
export default function ChatInput({ input, setInput, onSend, isLoading, supportsVision, onFileDrop }) {
    const { accent } = useTheme();
    const sendColor = ACCENT_COLORS[accent]?.hex || "#3b82f6";
    const fileInputRef = useRef(null);
    const inputRef = useRef(null);
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [listening, setListening] = useState(false);
    const [dragOver, setDragOver] = useState(false);
    const [showTemplates, setShowTemplates] = useState(false);
    const recognitionRef = useRef(null);

    // clear file when switching to non-vision model
    useEffect(() => {
        if (!supportsVision && file) {
            setFile(null);
            setPreview(null);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    }, [supportsVision]);

    const handleSend = () => {
        if (!input.trim() && !file) return;
        onSend(input, file);
        setInput("");
        setFile(null);
        setPreview(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const handleFileChange = (e) => {
        const selected = e.target.files?.[0];
        if (!selected) return;
        setFile(selected);
        const previewUrl = URL.createObjectURL(selected);
        setPreview(previewUrl);
    };

    // drag & drop handlers
    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setDragOver(true);
    }, []);

    const handleDragLeave = useCallback(() => setDragOver(false), []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer?.files?.[0];
        if (!dropped || !dropped.type.startsWith("image/")) return;
        setFile(dropped);
        setPreview(URL.createObjectURL(dropped));
        onFileDrop?.(dropped);
    }, [onFileDrop]);

    // voice input using Web Speech API
    const toggleListening = () => {
        if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
            alert("Speech recognition is not supported in this browser.");
            return;
        }
        if (listening) {
            recognitionRef.current?.stop();
            setListening(false);
            return;
        }
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.interimResults = true;
        recognition.continuous = true;
        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map((r) => r[0].transcript)
                .join("");
            setInput((prev) => prev + transcript);
        };
        recognition.onend = () => setListening(false);
        recognition.onerror = () => setListening(false);
        recognition.start();
        recognitionRef.current = recognition;
        setListening(true);
    };

    // insert template text
    const applyTemplate = (text) => {
        setInput(text);
        setShowTemplates(false);
        inputRef.current?.focus();
    };

    return (
        <div
            className={`w-full px-3 sm:px-6 pb-6 pt-4 border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950 transition-colors ${
                dragOver ? "bg-blue-50 dark:bg-blue-900/20" : ""
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            {dragOver && (
                <div className="max-w-4xl mx-auto mb-2 text-center text-sm text-blue-500 border-2 border-dashed border-blue-300 rounded-xl py-4">
                    Drop image to attach
                </div>
            )}

            {preview && (
                <div className="max-w-4xl mx-auto mb-2">
                    <div className="relative w-fit">
                        <img src={preview} alt="preview" className="w-24 h-24 object-cover rounded-lg border dark:border-gray-700" />
                        <button onClick={() => { setFile(null); setPreview(null); }} className="absolute top-0 right-0 bg-black text-white text-xs px-1 rounded">X</button>
                    </div>
                </div>
            )}

            <div className="max-w-4xl mx-auto flex flex-col gap-2">
                {/* template chips */}
                <div className="flex gap-1.5">
                    <button
                        onClick={() => setShowTemplates((v) => !v)}
                        className="text-xs px-2 py-1 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition flex items-center gap-1"
                        title="Templates"
                    >
                        <Sparkles className="w-3 h-3" /> Templates
                    </button>
                    {showTemplates && (
                        <div className="flex gap-1.5 flex-wrap">
                            {TEMPLATES.map((t) => (
                                <button
                                    key={t.label}
                                    onClick={() => applyTemplate(t.text)}
                                    className="text-xs px-2 py-1 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition"
                                >
                                    {t.label}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-3 p-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl shadow-sm">
                    {/* attach / voice buttons group */}
                    <div className="flex items-center gap-1">
                        {/* disabled when model lacks vision support */}
                        <div className="relative">
                            <button
                                onClick={() => supportsVision && fileInputRef.current?.click()}
                                className="h-10 w-10 flex items-center justify-center bg-gray-100 dark:bg-gray-800 rounded-xl disabled:opacity-40"
                                disabled={isLoading || !supportsVision}
                                title={!supportsVision ? "Selected model does not support images" : "Attach image"}
                            >
                                {supportsVision ? <Paperclip className="w-5 h-5" /> : <EyeOff className="w-5 h-5 text-gray-400" />}
                            </button>
                            {!supportsVision && (
                                <span className="absolute -bottom-5 left-0 text-[10px] text-gray-400 dark:text-gray-500 whitespace-nowrap">
                                    No image support
                                </span>
                            )}
                        </div>

                        {/* voice input */}
                        <button
                            onClick={toggleListening}
                            disabled={isLoading}
                            className={`h-10 w-10 flex items-center justify-center rounded-xl transition ${
                                listening
                                    ? "bg-red-100 dark:bg-red-900/50 text-red-500 animate-pulse"
                                    : "bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                            }`}
                            title={listening ? "Stop recording" : "Voice input"}
                        >
                            {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                        </button>
                    </div>

                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        accept="image/*"
                        onChange={handleFileChange}
                    />

                    <div className="flex-1 flex items-center gap-2">
                        <input
                            id="chat-input"
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => { if (e.key === "Enter" && !isLoading) handleSend(); }}
                            placeholder={file ? "Image selected" : "Message FlickerX..."}
                            disabled={isLoading}
                            className="flex-1 outline-none text-sm bg-transparent dark:text-gray-100 placeholder-gray-400"
                        />
                    </div>

                    <button
                        onClick={handleSend}
                        disabled={isLoading}
                        className="h-10 w-10 text-white rounded-full flex items-center justify-center disabled:opacity-50 shrink-0 transition"
                        style={{ backgroundColor: sendColor }}
                    >
                        {isLoading ? <span className="text-xs">...</span> : <Send className="w-4 h-4" />}
                    </button>
                </div>
            </div>
        </div>
    );
}
