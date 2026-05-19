// This component renders a command palette that allows users to quickly search and execute predefined commands. It includes a search input, a list of commands that filter based on the user's query, and handles keyboard interactions for opening and closing the palette.
import { X } from "lucide-react";
import { useEffect, useState } from "react";

export default function CommandPalette({ open, onClose, onSelect }) {
    const [query, setQuery] = useState("");

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
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-start justify-center pt-24 z-50">
            <div className="w-full max-w-xl bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">

                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search commands..."
                        className="w-full text-sm outline-none"
                        autoFocus
                    />

                    <button onClick={onClose}>
                        <X className="h-5 w-5 text-gray-500" />
                    </button>
                </div>

                {/* List */}
                <div className="max-h-80 overflow-y-auto">
                    {filtered.length === 0 ? (
                        <p className="p-4 text-sm text-gray-400">No commands found</p>
                    ) : (
                        filtered.map((cmd, idx) => (
                            <button
                                key={idx}
                                onClick={() => {
                                    onSelect(cmd);
                                    onClose();
                                }}
                                className="w-full text-left px-4 py-3 text-sm hover:bg-gray-100 transition"
                            >
                                {cmd}
                            </button>
                        ))
                    )}
                </div>

                {/* Footer hint */}
                <div className="px-4 py-2 text-xs text-gray-400 border-t border-gray-100">
                    Press <kbd className="px-1 bg-gray-100 border rounded">Esc</kbd> to close
                </div>
            </div>
        </div>
    );
}