// This component renders individual chat messages in the conversation. It supports both user and AI messages, displaying text content (with markdown support) and images. The component also includes avatars for the user and AI, and styles messages differently based on the sender.
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { User } from "lucide-react";
import { Bot } from "lucide-react";
import { Copy } from "lucide-react";

export default function Message({ role, content, image, user, onCopy, }) {
    const isUser = role === "user";

    return (
        <div className={`flex w-full mb-4 ${isUser ? "justify-end" : "justify-start"}`}>

            {/* AI Avatar */}
            {!isUser && (
                <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs mr-2 flex-shrink-0 text-white">
                    <Bot className="h-4 w-4" />
                </div>
            )}

            {/* Message Bubble */}
            <div
                className={`
        relative max-w-[75%] px-4 py-2 rounded-2xl text-sm leading-relaxed shadow-sm 
        ${isUser
                        ? "bg-blue-500 text-white rounded-br-sm"
                        : "bg-gray-800 text-gray-200 rounded-bl-sm"
                    }
    `}
            >
                {/* TEXT (markdown) */}
                {content && (
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {content}
                    </ReactMarkdown>
                )}

                {/* IMAGE (preview + cloudinary URL) */}
                {image && (
                    <img
                        src={image}
                        alt="Expired!!"
                        className="max-w-[220px] rounded-lg mt-2"
                    />
                )}

                {/* COPY BUTTON BELOW MESSAGE */}
                {content && (
                    <div className="mt-2 flex justify-end">
                        <button
                            onClick={() => onCopy(content)}
                            className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition"
                        >
                            <Copy className="w-4 h-4" />
                            Copy
                        </button>
                    </div>
                )}
            </div>


            {/* User Avatar */}
            {isUser && (
                <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-xs ml-2 flex-shrink-0 uppercase font-semibold text-white">
                    {user?.firstName?.[0] ||
                        user?.username?.[0] || (
                            <User className="h-4 w-4" />
                        )}
                </div>
            )}

        </div>
    );
}