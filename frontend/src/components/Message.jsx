import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot, Copy, RefreshCw, Pencil, Star } from "lucide-react";
import { useTheme } from "../context/ThemeContext"; // Adjust the import path as needed

// Helper to map accent strings to safe Tailwind classes
const getAccentClasses = (accent) => {
    const variants = {
        blue: { bg: "bg-blue-500" },
        purple: { bg: "bg-purple-500" },
        green: { bg: "bg-green-500" },
        orange: { bg: "bg-orange-500" },
        pink: { bg: "bg-pink-500" },
        teal: { bg: "bg-teal-500" },
    };
    return variants[accent] || variants.blue;
};

// supports pin/star, copy, regenerate, edit
export default function Message({ role, content, image, user, onCopy, onRegenerate, onEdit, pinned, onTogglePin }) {
    const isUser = role === "user";
    const { accent } = useTheme();
    const themeStyles = getAccentClasses(accent);

    return (
        <div className={`flex w-full mb-4 ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}>
            {/* Bot Avatar */}
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-gray-700 dark:bg-gray-800 flex items-center justify-center text-xs mr-2 flex-shrink-0 text-white shadow-sm">
                    <Bot className="h-4 w-4" />
                </div>
            )}

            {/* Message Bubble */}
            <div
                className={`relative max-w-[90%] sm:max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm transition-colors duration-300 ${isUser
                    ? `${themeStyles.bg} text-white rounded-br-sm`
                    : "bg-gray-100 dark:bg-[#111111] border border-transparent dark:border-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-sm"
                    } ${pinned ? "ring-2 ring-yellow-400 dark:ring-yellow-500" : ""}`}
            >
                {/* Content */}
                {content && (
                    <div className="overflow-x-auto">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                    </div>
                )}

                {/* Uploaded Image */}
                {image && (
                    <img src={image} alt="Uploaded" className="max-w-full sm:max-w-[220px] rounded-lg mt-2 shadow-sm" />
                )}

                {/* Action Buttons */}
                {content && (
                    <div className="mt-3 flex items-center gap-2 justify-end">
                        {/* pin/star toggle */}
                        {onTogglePin && (
                            <button
                                onClick={() => onTogglePin()}
                                className={`flex items-center gap-1 text-xs transition-colors duration-200 ${isUser ? "text-white/70 hover:text-white" : "text-gray-400 hover:text-yellow-500"
                                    }`}
                                title={pinned ? "Unpin" : "Pin"}
                            >
                                <Star className={`w-3.5 h-3.5 ${pinned ? (isUser ? "fill-white text-white" : "fill-yellow-400 text-yellow-400") : ""}`} />
                            </button>
                        )}

                        {/* Regenerate (Bot Only) */}
                        {!isUser && onRegenerate && (
                            <button
                                onClick={() => onRegenerate()}
                                className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200"
                            >
                                <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                        )}

                        {/* Edit (User Only) */}
                        {isUser && onEdit && (
                            <button
                                onClick={() => onEdit(content)}
                                className="flex items-center gap-1 text-xs text-white/70 hover:text-white transition-colors duration-200"
                            >
                                <Pencil className="w-3.5 h-3.5" />
                            </button>
                        )}

                        {/* Copy (Both) */}
                        <button
                            onClick={() => onCopy(content)}
                            className={`flex items-center gap-1 text-xs transition-colors duration-200 ${isUser ? "text-white/70 hover:text-white" : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                }`}
                        >
                            <Copy className="w-3.5 h-3.5" />
                        </button>
                    </div>
                )}
            </div>

            {/* User Avatar */}
            {isUser && (
                <div className={`w-8 h-8 rounded-full ${themeStyles.bg} flex items-center justify-center text-xs ml-2 flex-shrink-0 uppercase font-semibold text-white shadow-sm transition-colors duration-300`}>
                    {user?.name?.[0] || <User className="h-4 w-4" />}
                </div>
            )}
        </div>
    );
}