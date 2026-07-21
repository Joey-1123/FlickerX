import {
    Sparkles,
    Code2,
    Lightbulb,
    MessageSquarePlus,
    HelpCircle,
    FileText,
    Zap
} from "lucide-react";
import { useTheme } from "../context/ThemeContext"; // Adjust the import path as needed

// Helper to map accent strings to safe Tailwind classes
const getAccentClasses = (accent) => {
    const variants = {
        blue: { icon: "text-blue-600 dark:text-blue-400", softBg: "bg-blue-50 dark:bg-blue-900/20", softBorder: "border-blue-100 dark:border-blue-800/50", hoverBorder: "hover:border-blue-400 dark:hover:border-blue-500", hoverText: "group-hover:text-blue-600 dark:group-hover:text-blue-400", groupHoverBg: "group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40", tagBg: "bg-blue-50/80 dark:bg-blue-900/30" },
        purple: { icon: "text-purple-600 dark:text-purple-400", softBg: "bg-purple-50 dark:bg-purple-900/20", softBorder: "border-purple-100 dark:border-purple-800/50", hoverBorder: "hover:border-purple-400 dark:hover:border-purple-500", hoverText: "group-hover:text-purple-600 dark:group-hover:text-purple-400", groupHoverBg: "group-hover:bg-purple-100 dark:group-hover:bg-purple-900/40", tagBg: "bg-purple-50/80 dark:bg-purple-900/30" },
        green: { icon: "text-green-600 dark:text-green-400", softBg: "bg-green-50 dark:bg-green-900/20", softBorder: "border-green-100 dark:border-green-800/50", hoverBorder: "hover:border-green-400 dark:hover:border-green-500", hoverText: "group-hover:text-green-600 dark:group-hover:text-green-400", groupHoverBg: "group-hover:bg-green-100 dark:group-hover:bg-green-900/40", tagBg: "bg-green-50/80 dark:bg-green-900/30" },
        orange: { icon: "text-orange-600 dark:text-orange-400", softBg: "bg-orange-50 dark:bg-orange-900/20", softBorder: "border-orange-100 dark:border-orange-800/50", hoverBorder: "hover:border-orange-400 dark:hover:border-orange-500", hoverText: "group-hover:text-orange-600 dark:group-hover:text-orange-400", groupHoverBg: "group-hover:bg-orange-100 dark:group-hover:bg-orange-900/40", tagBg: "bg-orange-50/80 dark:bg-orange-900/30" },
        pink: { icon: "text-pink-600 dark:text-pink-400", softBg: "bg-pink-50 dark:bg-pink-900/20", softBorder: "border-pink-100 dark:border-pink-800/50", hoverBorder: "hover:border-pink-400 dark:hover:border-pink-500", hoverText: "group-hover:text-pink-600 dark:group-hover:text-pink-400", groupHoverBg: "group-hover:bg-pink-100 dark:group-hover:bg-pink-900/40", tagBg: "bg-pink-50/80 dark:bg-pink-900/30" },
        teal: { icon: "text-teal-600 dark:text-teal-400", softBg: "bg-teal-50 dark:bg-teal-900/20", softBorder: "border-teal-100 dark:border-teal-800/50", hoverBorder: "hover:border-teal-400 dark:hover:border-teal-500", hoverText: "group-hover:text-teal-600 dark:group-hover:text-teal-400", groupHoverBg: "group-hover:bg-teal-100 dark:group-hover:bg-teal-900/40", tagBg: "bg-teal-50/80 dark:bg-teal-900/30" },
    };
    return variants[accent] || variants.blue;
};

export default function EmptyState({ onActionClick }) {
    const { accent } = useTheme();
    const themeStyles = getAccentClasses(accent);

    // Store component references instead of JSX so we can apply dynamic colors during render
    const suggestions = [
        {
            icon: Code2,
            title: "Optimize Backend",
            description: "Get assistance with your Django queries and data workflows.",
            tag: "AI"
        },
        {
            icon: Lightbulb,
            title: "Logic Analysis",
            description: "Verify categorical syllogisms and propositional logic.",
            tag: "Logic"
        },
        {
            icon: MessageSquarePlus,
            title: "Learnalytics",
            description: "Review current microservices architecture and API responses.",
            tag: "System"
        }
    ];

    const handleClick = (item) => {
        onActionClick?.(item);
    };

    return (
        <div className="h-full flex flex-col items-center justify-center text-center p-6 select-none max-w-4xl mx-auto transition-colors duration-300">

            {/* Icon */}
            <div className={`h-16 w-16 rounded-2xl flex items-center justify-center mb-2 shadow-sm border transition-colors duration-300 ${themeStyles.softBg} ${themeStyles.softBorder}`}>
                <Sparkles className={`h-10 w-6 transition-colors duration-300 ${themeStyles.icon}`} />
            </div>

            {/* Title */}
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 transition-colors duration-300">
                Start a conversation with FlickerX
            </h2>

            {/* Subtitle */}
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mb-6 transition-colors duration-300">
                Ask anything, analyze complex logic, or upload a file to begin.
            </p>

            {/* Bento Grid Suggestions */}
            <div className="grid grid-cols-1 md:grid-cols-4 md:grid-rows-2 gap-4 w-full max-w-4xl px-2 h-auto md:h-64">

                {/* Primary Action (Spans 2 columns & 2 rows) */}
                <button
                    onClick={() => handleClick({ tag: "System", title: "File Analysis" })}
                    className={`group relative flex flex-col items-start p-6 bg-white dark:bg-[#111111] border border-gray-200 dark:border-gray-800 rounded-3xl text-left shadow-sm hover:shadow-md active:scale-[0.98] transition-all duration-300 md:col-span-2 md:row-span-2 overflow-hidden ${themeStyles.hoverBorder}`}
                >
                    <div className={`p-3 rounded-2xl mb-auto transition-colors duration-300 ${themeStyles.softBg} ${themeStyles.groupHoverBg}`}>
                        <FileText className={`h-8 w-8 transition-colors duration-300 ${themeStyles.icon}`} />
                    </div>

                    <div className="mt-8 z-10">
                        <span className={`inline-block text-[10px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-md mb-3 border transition-colors duration-300 ${themeStyles.icon} ${themeStyles.tagBg} ${themeStyles.softBorder}`}>
                            Workspace
                        </span>
                        <h3 className={`text-xl font-bold text-gray-800 dark:text-gray-100 mb-2 transition-colors duration-300 ${themeStyles.hoverText}`}>
                            Analyze a Document
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 transition-colors duration-300">
                            Upload your datasets, code files, or academic papers for deep summarization and extraction.
                        </p>
                    </div>
                </button>

                {/* Secondary Action (Spans 2 columns, 1 row) */}
                <button
                    onClick={() => handleClick({ tag: "AI", title: "Optimize Backend" })}
                    className={`group flex items-center justify-between p-5 bg-white dark:bg-[#111111] border border-gray-200 dark:border-gray-800 rounded-3xl text-left shadow-sm hover:shadow-md active:scale-[0.98] transition-all duration-300 md:col-span-2 ${themeStyles.hoverBorder}`}
                >
                    <div>
                        <span className={`inline-block text-[10px] font-bold tracking-wider uppercase px-2 py-1 rounded-md mb-2 border transition-colors duration-300 ${themeStyles.icon} ${themeStyles.tagBg} ${themeStyles.softBorder}`}>
                            Code
                        </span>
                        <h3 className={`text-base font-bold text-gray-800 dark:text-gray-100 mb-1 transition-colors duration-300 ${themeStyles.hoverText}`}>
                            Optimize Backend
                        </h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Review microservices and API responses.</p>
                    </div>
                    <div className={`p-3 rounded-2xl ml-4 shrink-0 transition-colors duration-300 ${themeStyles.softBg} ${themeStyles.groupHoverBg}`}>
                        <Code2 className={`h-6 w-6 transition-colors duration-300 ${themeStyles.icon}`} />
                    </div>
                </button>

                {/* Small Action 1 (Spans 1 column, 1 row) */}
                <button
                    onClick={() => handleClick({ tag: "Logic", title: "Logic Analysis" })}
                    className={`group flex flex-col justify-between p-5 bg-white dark:bg-[#111111] border border-gray-200 dark:border-gray-800 rounded-3xl text-left shadow-sm hover:shadow-md active:scale-[0.98] transition-all duration-300 ${themeStyles.hoverBorder}`}
                >
                    <div className="flex justify-between items-start w-full mb-2">
                        <div className={`p-2.5 rounded-xl transition-colors duration-300 ${themeStyles.softBg} ${themeStyles.groupHoverBg}`}>
                            <Lightbulb className={`h-5 w-5 transition-colors duration-300 ${themeStyles.icon}`} />
                        </div>
                    </div>
                    <h3 className={`text-sm font-bold text-gray-800 dark:text-gray-100 transition-colors duration-300 ${themeStyles.hoverText}`}>
                        Logic Proofs
                    </h3>
                </button>

                {/* Small Action 2 (Spans 1 column, 1 row) */}
                <button
                    onClick={() => handleClick({ tag: "System", title: "Generate API" })}
                    className={`group flex flex-col justify-between p-5 bg-white dark:bg-[#111111] border border-gray-200 dark:border-gray-800 rounded-3xl text-left shadow-sm hover:shadow-md active:scale-[0.98] transition-all duration-300 ${themeStyles.hoverBorder}`}
                >
                    <div className="flex justify-between items-start w-full mb-2">
                        <div className={`p-2.5 rounded-xl transition-colors duration-300 ${themeStyles.softBg} ${themeStyles.groupHoverBg}`}>
                            <Zap className={`h-5 w-5 transition-colors duration-300 ${themeStyles.icon}`} />
                        </div>
                    </div>
                    <h3 className={`text-sm font-bold text-gray-800 dark:text-gray-100 transition-colors duration-300 ${themeStyles.hoverText}`}>
                        Generate API
                    </h3>
                </button>

            </div>

            {/* Footer hint */}
            <div className="mt-4 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 bg-white dark:bg-[#111111] px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm transition-colors duration-300">
                <HelpCircle className="h-3.5 w-3.5 text-gray-400 dark:text-gray-500" />
                <span>
                    Press{" "}
                    <kbd className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded text-gray-600 dark:text-gray-300 transition-colors duration-300">
                        /
                    </kbd>{" "}
                    to browse prompt categories
                </span>
            </div>
        </div>
    );
}