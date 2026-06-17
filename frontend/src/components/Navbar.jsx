import { Sparkles, Trash2, Menu, Plus, Download } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { ACCENT_COLORS } from "../context/ThemeContext";

// Changed: removed About, Contact, theme, login/auth links — moved to Sidebar
export default function ChatNavbar({ clearChat, onToggleSidebar, onNewChat, onExport }) {
    const { accent } = useTheme();
    const ac = ACCENT_COLORS[accent];
    return (
        <nav className="sticky top-0 z-30 bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-800/50 px-4 py-4 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2 select-none">
                <button onClick={onToggleSidebar} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400" title="Chat history">
                    <Menu className="w-5 h-5" />
                </button>
                <div
                    className={`h-8 w-8 rounded-xl ${ac.bg} flex items-center justify-center text-white font-bold shadow-sm`}
                    style={{ backgroundColor: ac.hex }}
                >F</div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 items-center gap-2 hidden sm:flex">
                    FlickerX
                    <Sparkles className="h-4 w-4 animate-pulse" style={{ color: ac.hex }} />
                </h1>
            </div>

            <div className="flex items-center gap-1 sm:gap-2">
                <button onClick={onExport} className="text-xs px-2 sm:px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center gap-1.5 shadow-sm font-medium" title="Export chat">
                    <Download className="h-3.5 w-3.5" /> <span className="hidden sm:inline">Export</span>
                </button>
                <button onClick={onNewChat} className="text-xs px-2 sm:px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 transition flex items-center gap-1.5 shadow-sm font-medium" title="New chat">
                    <Plus className="h-3.5 w-3.5" /> <span className="hidden sm:inline">New</span>
                </button>
                <button onClick={clearChat} className="text-xs px-2 sm:px-3 py-2 rounded-xl border border-red-200 dark:border-red-900 bg-red-50/70 dark:bg-red-950/50 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950 transition flex items-center gap-1.5 shadow-sm font-medium">
                    <Trash2 className="h-3.5 w-3.5" /> <span className="hidden sm:inline">Clear</span>
                </button>
            </div>
        </nav>
    );
}
