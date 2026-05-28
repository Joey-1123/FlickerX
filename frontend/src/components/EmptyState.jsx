// This component renders an empty state for the chat interface, providing users with suggestions on how to start a conversation with FlickerX. It includes an icon, a title, a subtitle, and a list of actionable suggestions that users can click to initiate specific interactions with the AI.
import {
    Sparkles,
    Code2,
    Lightbulb,
    MessageSquarePlus,
    HelpCircle
} from "lucide-react";

export default function EmptyState({ onActionClick }) {
    // Predefined suggestions that users can click to start a conversation with FlickerX. Each suggestion includes an icon, title, description, and a tag indicating the category of the command.
    const suggestions = [
        {
            icon: <Code2 className="h-5 w-5 text-blue-600" />,
            title: "Optimize Backend",
            description: "Get assistance with your Django queries and data workflows.",
            tag: "AI"
        },
        {
            icon: <Lightbulb className="h-5 w-5 text-blue-600" />,
            title: "Logic Analysis",
            description: "Verify categorical syllogisms and propositional logic.",
            tag: "Logic"
        },
        {
            icon: <MessageSquarePlus className="h-5 w-5 text-blue-600" />,
            title: "Learnalytics",
            description: "Review current microservices architecture and API responses.",
            tag: "System"
        }
    ];

    const handleClick = (item) => {
        onActionClick?.(item);
    };

    return (
        <div className="h-full flex flex-col items-center justify-center text-center p-6 select-none max-w-4xl mx-auto">

            {/* Icon */}
            <div className="h-16 w-16 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-4 shadow-sm">
                <Sparkles className="h-6 w-6 text-blue-600" />
            </div>

            {/* Title */}
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Start a conversation with FlickerX
            </h2>

            {/* Subtitle */}
            <p className="text-sm text-gray-500 max-w-md mb-10">
                Ask anything, analyze complex logic, or upload a file to begin.
            </p>

            {/* Suggestions */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-3xl px-4">
                {suggestions.map((item, index) => (
                    <button
                        key={index}
                        onClick={() => handleClick(item)}
                        className="group flex flex-col items-start p-4 sm:p-5 bg-white border border-gray-200 rounded-2xl text-left hover:border-blue-400 hover:shadow-md active:scale-[0.98] transition-all duration-200"
                    >
                        <div className="flex justify-between w-full mb-4">
                            <div className="p-2 rounded-xl bg-blue-50 group-hover:bg-blue-100 transition">
                                {item.icon}
                            </div>

                            <span className="text-[10px] font-semibold tracking-wide uppercase text-blue-600 bg-blue-50/80 border border-blue-100/50 px-2 py-2 rounded-md shadow-sm">
                                {item.tag}
                            </span> 
                        </div>

                        <h3 className="text-sm font-semibold text-gray-800 mb-1 group-hover:text-blue-600 transition">
                            {item.title}
                        </h3>

                        <p className="text-xs text-gray-400">
                            {item.description}
                        </p>
                    </button>
                ))}
            </div>

            {/* Footer hint */}
            <div className="mt-10 flex items-center gap-2 text-xs text-gray-500 bg-white px-4 py-2 rounded-xl border border-gray-200 shadow-sm">
                <HelpCircle className="h-3.5 w-3.5 text-gray-400" />
                <span>
                    Press{" "}
                    <kbd className="px-2 py-0.5 bg-gray-100 border border-gray-200 rounded text-gray-600">
                        /
                    </kbd>{" "}
                    to browse prompt categories
                </span>
            </div>
        </div>
    );
}