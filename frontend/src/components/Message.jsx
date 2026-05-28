import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot, Copy, RefreshCw, Pencil, Star } from "lucide-react";

// supports pin/star, copy, regenerate, edit
export default function Message({ role, content, image, user, onCopy, onRegenerate, onEdit, pinned, onTogglePin }) {
    const isUser = role === "user";

    return (
        <div className={`flex w-full mb-4 ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}>
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-gray-700 dark:bg-gray-600 flex items-center justify-center text-xs mr-2 flex-shrink-0 text-white">
                    <Bot className="h-4 w-4" />
                </div>
            )}

            <div
                className={`relative max-w-[90%] sm:max-w-[75%] px-4 py-2 rounded-2xl text-sm leading-relaxed shadow-sm ${
                    isUser
                        ? "bg-blue-500 text-white rounded-br-sm"
                        : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-sm"
                } ${pinned ? "ring-2 ring-yellow-400 dark:ring-yellow-500" : ""}`}
            >
                {content && (
                    <div className="overflow-x-auto">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {content}
                        </ReactMarkdown>
                    </div>
                )}

                {image && (
                    <img src={image} alt="Uploaded" className="max-w-full sm:max-w-[220px] rounded-lg mt-2" />
                )}

                {content && (
                    <div className="mt-2 flex items-center gap-2 justify-end">
                        {/* pin/star toggle */}
                        {onTogglePin && (
                            <button onClick={() => onTogglePin()} className="flex items-center gap-1 text-xs text-gray-400 hover:text-yellow-500 transition" title={pinned ? "Unpin" : "Pin"}>
                                <Star className={`w-3.5 h-3.5 ${pinned ? "fill-yellow-400 text-yellow-400" : ""}`} />
                            </button>
                        )}
                        {!isUser && onRegenerate && (
                            <button onClick={() => onRegenerate()} className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
                                <RefreshCw className="w-3.5 h-3.5" />
                            </button>
                        )}
                        {isUser && onEdit && (
                            <button onClick={() => onEdit(content)} className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
                                <Pencil className="w-3.5 h-3.5" />
                            </button>
                        )}
                        <button onClick={() => onCopy(content)} className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition">
                            <Copy className="w-3.5 h-3.5" />
                        </button>
                    </div>
                )}
            </div>

            {isUser && (
                <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-xs ml-2 flex-shrink-0 uppercase font-semibold text-white">
                    {user?.name?.[0] || <User className="h-4 w-4" />}
                </div>
            )}
        </div>
    );
}
