// This component renders the chat input area where users can type messages and upload images. It handles the state of the input, file selection, and sending messages to the backend.
import { useRef, useState } from "react";
import { Send, Paperclip } from "lucide-react";

export default function ChatInput({ input, setInput, onSend, isLoading }) {
    const fileInputRef = useRef(null);
    const [file, setFile] = useState(null);
    const [preview, setPreview] = useState(null);

    const handleSend = () => {
        if (!input.trim() && !file) return;

        onSend(input, file);

        setInput("");
        setFile(null);
        setPreview(null);

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleFileChange = (e) => {
        const selected = e.target.files?.[0];
        if (!selected) return;

        setFile(selected);

        // 🔥 THIS WAS MISSING
        const previewUrl = URL.createObjectURL(selected);
        setPreview(previewUrl);
    };



    return (
        <div className="w-full px-6 pb-6 pt-4 border-t border-gray-200 bg-white">

            {/* Preview */}
            {preview && (
                <div className="max-w-4xl mx-auto mb-2">
                    <div className="relative w-fit">
                        <img
                            src={preview}
                            alt="preview"
                            className="w-24 h-24 object-cover rounded-lg border"
                        />

                        <button
                            onClick={() => {
                                setFile(null);
                                setPreview(null);
                            }}
                            className="absolute top-0 right-0 bg-black text-white text-xs px-1 rounded"
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            <div className="max-w-4xl mx-auto flex items-center gap-3 p-2 bg-white border border-gray-200 rounded-2xl shadow-sm">

                {/* Upload Button */}
                <button
                    onClick={() => fileInputRef.current?.click()}
                    className="h-10 w-10 flex items-center justify-center bg-gray-100 rounded-xl"
                    disabled={isLoading}
                >
                    <Paperclip className="w-5 h-5" />
                </button>

                <input
                    type="file"
                    ref={fileInputRef}
                    className="hidden"
                    accept="image/*"
                    onChange={handleFileChange}
                />

                {/* ✅ SINGLE INPUT (FIXED) */}
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !isLoading) {
                            handleSend(input, file);
                        }
                    }}
                    placeholder={file ? "Image selected ✔" : "Message FlickerX..."}
                    disabled={isLoading} // ✅ disables typing while loading
                    className="flex-1 outline-none text-sm"
                />

                {/* Send */}
                <button
                    onClick={() => handleSend(input, file)}
                    disabled={isLoading} // ✅ prevents spam click
                    className="h-10 w-10 bg-blue-600 text-white rounded-full flex items-center justify-center disabled:opacity-50"
                >
                    {isLoading ? (
                        <span className="text-xs">...</span>
                    ) : (
                        <Send className="w-4 h-4" />
                    )}
                </button>
            </div>
        </div>
    );
}