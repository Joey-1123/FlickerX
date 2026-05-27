import { useEffect } from "react";
import { X } from "lucide-react";

const shortcuts = [
    { key: "/", desc: "Open command palette" },
    { key: "? / Ctrl+/", desc: "Show this shortcut reference" },
    { key: "Escape", desc: "Close modals and palettes" },
    { key: "Enter", desc: "Send message" },
];

export default function ShortcutsModal({ open, onClose }) {
    useEffect(() => {
        if (!open) return;
        const handler = (e) => { if (e.key === "Escape") onClose(); };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [open, onClose]);

    if (!open) return null;

    return (
        <>
            <div className="fixed inset-0 bg-black/30 z-50" onClick={onClose} />
            <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[90vw] max-w-sm bg-white dark:bg-gray-800 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 p-6">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">
                        Keyboard Shortcuts
                    </h2>
                    <button onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                        <X className="w-4 h-4 text-gray-500" />
                    </button>
                </div>
                <div className="space-y-2">
                    {shortcuts.map((s) => (
                        <div key={s.key} className="flex items-center justify-between text-sm">
                            <span className="text-gray-600 dark:text-gray-400">{s.desc}</span>
                            <kbd className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-mono text-xs border border-gray-200 dark:border-gray-600">
                                {s.key}
                            </kbd>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
}
