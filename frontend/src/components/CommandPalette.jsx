import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { useTheme } from "../context/ThemeContext"; // Adjust the import path as needed

// Helper to map accent strings to safe Tailwind classes
const getAccentClasses = (accent) => {
    const variants = {
        blue: { hoverBg: "hover:bg-blue-50 dark:hover:bg-blue-900/30", hoverText: "hover:text-blue-600 dark:hover:text-blue-400", focusText: "focus:text-blue-600 dark:focus:text-blue-400" },
        purple: { hoverBg: "hover:bg-purple-50 dark:hover:bg-purple-900/30", hoverText: "hover:text-purple-600 dark:hover:text-purple-400", focusText: "focus:text-purple-600 dark:focus:text-purple-400" },
        green: { hoverBg: "hover:bg-green-50 dark:hover:bg-green-900/30", hoverText: "hover:text-green-600 dark:hover:text-green-400", focusText: "focus:text-green-600 dark:focus:text-green-400" },
        orange: { hoverBg: "hover:bg-orange-50 dark:hover:bg-orange-900/30", hoverText: "hover:text-orange-600 dark:hover:text-orange-400", focusText: "focus:text-orange-600 dark:focus:text-orange-400" },
        pink: { hoverBg: "hover:bg-pink-50 dark:hover:bg-pink-900/30", hoverText: "hover:text-pink-600 dark:hover:text-pink-400", focusText: "focus:text-pink-600 dark:focus:text-pink-400" },
        teal: { hoverBg: "hover:bg-teal-50 dark:hover:bg-teal-900/30", hoverText: "hover:text-teal-600 dark:hover:text-teal-400", focusText: "focus:text-teal-600 dark:focus:text-teal-400" },
    };
    return variants[accent] || variants.blue;
};

export default function CommandPalette({ open, onClose, onSelect }) {
    const [query, setQuery] = useState("");
    const { accent } = useTheme();
    const themeStyles = getAccentClasses(accent);

    // Predefined list of commands that users can execute. This can be expanded or modified as needed.
    const commands = [
        "Optimize Backend",
        "Logic Analysis",
        "Explain Code",
        "Debug Issue",
        "Summarize File",
        "Generate API",
        "Write Documentation"
    ];

    const filtered = commands.filter((c) =>
        c.toLowerCase().includes(query.toLowerCase())
    );

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === "Escape") onClose();
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [onClose]);

    if (!open) return null;

    return (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-start justify-center pt-12 sm:pt-24 z-50 transition-opacity">
            <div className="w-full max-w-xl bg-white dark:bg-[#111111] rounded-2xl shadow-xl border border-gray-200 dark:border-gray-800 overflow-hidden max-h-[calc(100vh-8rem)] flex flex-col transition-colors duration-300">

                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800 transition-colors duration-300">
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search commands..."
                        className="w-full text-sm outline-none bg-transparent text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 transition-colors"
                        autoFocus
                    />

                    <button
                        onClick={onClose}
                        className={`p-1 rounded-md transition-colors duration-200 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 ${themeStyles.hoverText}`}
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                {/* List */}
                <div className="overflow-y-auto overflow-x-hidden flex-1">
                    {filtered.length === 0 ? (
                        <p className="p-4 text-sm text-gray-400 dark:text-gray-500 text-center">No commands found</p>
                    ) : (
                        filtered.map((cmd, idx) => (
                            <button
                                key={idx}
                                onClick={() => {
                                    onSelect(cmd);
                                    onClose();
                                }}
                                className={`w-full text-left px-4 py-3 text-sm text-gray-700 dark:text-gray-300 transition-colors duration-200 ${themeStyles.hoverBg} ${themeStyles.hoverText}`}
                            >
                                {cmd}
                            </button>
                        ))
                    )}
                </div>

                {/* Footer hint */}
                <div className="px-4 py-3 text-xs text-gray-400 dark:text-gray-500 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-[#0a0a0a] transition-colors duration-300 flex items-center justify-between">
                    <span>Quick Actions</span>
                    <div>
                        Press <kbd className="px-1.5 py-0.5 ml-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md text-gray-500 dark:text-gray-400 shadow-sm transition-colors duration-300 font-mono text-[10px] font-semibold">ESC</kbd> to close
                    </div>
                </div>
            </div>
        </div>
    );
}