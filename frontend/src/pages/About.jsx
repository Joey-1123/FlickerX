import { Link, useNavigate } from "react-router-dom";
import { Sparkles, Bot, FileText, Zap, Shield, Code2, ArrowLeft } from "lucide-react";
import { useTheme } from "../context/ThemeContext"; // Adjust the import path to wherever your provider is located

// Helper to map accent strings to safe Tailwind classes
const getAccentClasses = (accent) => {
    const variants = {
        blue: { icon: "text-blue-600 dark:text-blue-400", softBg: "bg-blue-50 dark:bg-blue-900/20", softBorder: "border-blue-100 dark:border-blue-800/50", hoverBg: "hover:bg-blue-50 dark:hover:bg-blue-900/30", hoverText: "hover:text-blue-600 dark:hover:text-blue-400" },
        purple: { icon: "text-purple-600 dark:text-purple-400", softBg: "bg-purple-50 dark:bg-purple-900/20", softBorder: "border-purple-100 dark:border-purple-800/50", hoverBg: "hover:bg-purple-50 dark:hover:bg-purple-900/30", hoverText: "hover:text-purple-600 dark:hover:text-purple-400" },
        green: { icon: "text-green-600 dark:text-green-400", softBg: "bg-green-50 dark:bg-green-900/20", softBorder: "border-green-100 dark:border-green-800/50", hoverBg: "hover:bg-green-50 dark:hover:bg-green-900/30", hoverText: "hover:text-green-600 dark:hover:text-green-400" },
        orange: { icon: "text-orange-600 dark:text-orange-400", softBg: "bg-orange-50 dark:bg-orange-900/20", softBorder: "border-orange-100 dark:border-orange-800/50", hoverBg: "hover:bg-orange-50 dark:hover:bg-orange-900/30", hoverText: "hover:text-orange-600 dark:hover:text-orange-400" },
        pink: { icon: "text-pink-600 dark:text-pink-400", softBg: "bg-pink-50 dark:bg-pink-900/20", softBorder: "border-pink-100 dark:border-pink-800/50", hoverBg: "hover:bg-pink-50 dark:hover:bg-pink-900/30", hoverText: "hover:text-pink-600 dark:hover:text-pink-400" },
        teal: { icon: "text-teal-600 dark:text-teal-400", softBg: "bg-teal-50 dark:bg-teal-900/20", softBorder: "border-teal-100 dark:border-teal-800/50", hoverBg: "hover:bg-teal-50 dark:hover:bg-teal-900/30", hoverText: "hover:text-teal-600 dark:hover:text-teal-400" },
    };
    return variants[accent] || variants.blue;
};

export default function About() {
    const navigate = useNavigate();
    const { accent, colors } = useTheme();

    // Get the dynamic styles based on the current context
    const themeStyles = getAccentClasses(accent);
    const ringClass = colors[accent]?.ring || "ring-blue-500";

    return (
        <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-gray-100 transition-colors duration-300">

            {/* Header */}
            <div className="max-w-4xl mx-auto px-6 py-16 text-center">
                <div className="flex justify-center mb-5">
                    <div className={`p-3 rounded-xl transition-colors duration-300 ${themeStyles.softBg} border ${themeStyles.softBorder}`}>
                        <Sparkles className={`h-6 w-6 transition-colors duration-300 ${themeStyles.icon}`} />
                    </div>
                </div>

                <h1 className="text-4xl font-bold mb-4">
                    About FlickerX
                </h1>

                <p className="text-gray-500 dark:text-gray-400 text-sm max-w-2xl mx-auto leading-relaxed transition-colors duration-300">
                    FlickerX is a modern AI-powered chat platform designed to help developers,
                    students, and creators work faster using intelligent conversations,
                    file understanding, and slash commands.
                </p>
            </div>

            {/* Mission */}
            <div className="max-w-3xl mx-auto px-6 mb-16">
                <div className="p-6 rounded-2xl border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-[#0a0a0a] transition-colors duration-300">
                    <h2 className="text-lg font-semibold mb-2">Our Mission</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed transition-colors duration-300">
                        We aim to simplify complex workflows using AI. Whether you're debugging code,
                        learning new concepts, or generating APIs, FlickerX gives you fast, structured,
                        and useful responses in real time.
                    </p>
                </div>
            </div>

            {/* Features */}
            <div className="max-w-5xl mx-auto px-6 pb-20 grid md:grid-cols-3 gap-6">

                <div className="p-6 border border-gray-100 dark:border-gray-800 rounded-2xl bg-white dark:bg-[#0a0a0a] shadow-sm hover:shadow-md dark:shadow-none transition-all duration-300">
                    <Bot className={`h-5 w-5 mb-3 transition-colors duration-300 ${themeStyles.icon}`} />
                    <h3 className="font-semibold mb-2">AI Chat Assistant</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 transition-colors duration-300">
                        Chat with an intelligent assistant for coding, learning, and problem-solving.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 dark:border-gray-800 rounded-2xl bg-white dark:bg-[#0a0a0a] shadow-sm hover:shadow-md dark:shadow-none transition-all duration-300">
                    <FileText className={`h-5 w-5 mb-3 transition-colors duration-300 ${themeStyles.icon}`} />
                    <h3 className="font-semibold mb-2">File Understanding</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 transition-colors duration-300">
                        Upload files or code and get instant analysis, summaries, and explanations.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 dark:border-gray-800 rounded-2xl bg-white dark:bg-[#0a0a0a] shadow-sm hover:shadow-md dark:shadow-none transition-all duration-300">
                    <Zap className={`h-5 w-5 mb-3 transition-colors duration-300 ${themeStyles.icon}`} />
                    <h3 className="font-semibold mb-2">Slash Commands</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 transition-colors duration-300">
                        Use commands like /fix, /explain, and /summarize to control AI faster.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 dark:border-gray-800 rounded-2xl bg-white dark:bg-[#0a0a0a] shadow-sm hover:shadow-md dark:shadow-none transition-all duration-300">
                    <Code2 className={`h-5 w-5 mb-3 transition-colors duration-300 ${themeStyles.icon}`} />
                    <h3 className="font-semibold mb-2">Developer Friendly</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 transition-colors duration-300">
                        Built for developers with clean responses, code formatting, and debugging support.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 dark:border-gray-800 rounded-2xl bg-white dark:bg-[#0a0a0a] shadow-sm hover:shadow-md dark:shadow-none transition-all duration-300">
                    <Shield className={`h-5 w-5 mb-3 transition-colors duration-300 ${themeStyles.icon}`} />
                    <h3 className="font-semibold mb-2">Secure Access</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 transition-colors duration-300">
                        Authentication handled securely using JWT sessions for safe user access.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 dark:border-gray-800 rounded-2xl bg-white dark:bg-[#0a0a0a] shadow-sm hover:shadow-md dark:shadow-none transition-all duration-300">
                    <Sparkles className={`h-5 w-5 mb-3 transition-colors duration-300 ${themeStyles.icon}`} />
                    <h3 className="font-semibold mb-2">Smart Experience</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 transition-colors duration-300">
                        Designed for speed, clarity, and productivity with modern UI/UX.
                    </p>
                </div>

                {/* BACK BUTTON */}
                <div className="flex justify-center w-full ml-auto mr-auto mt-6 md:col-span-3">
                    <button
                        onClick={() => navigate(-1)}
                        className={`flex items-center px-5 py-2.5 bg-white dark:bg-black border border-gray-200 dark:border-gray-800 text-sm font-medium text-gray-600 dark:text-gray-400 rounded-full shadow-sm ${themeStyles.hoverBg} ${themeStyles.hoverText} hover:border-transparent transition-all duration-200 focus:outline-none focus:ring-2 ${ringClass}`}
                        aria-label="Go back to previous page"
                    >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Go Back
                    </button>
                </div>

            </div>

            {/* Footer */}
            <div className="text-center text-gray-400 dark:text-gray-600 text-xs pb-10 border-t border-gray-100 dark:border-gray-800 pt-6 transition-colors duration-300">
                <p>&copy; {new Date().getFullYear()} FlickerX. Built for smarter conversations.</p>
                <p className="mt-1">
                    <Link to="/policies" className={`transition-colors duration-300 ${themeStyles.icon} hover:underline`}>Policies & Terms</Link>
                </p>
                <p className="mt-1 text-gray-500 dark:text-gray-500">v{import.meta.env.VITE_APP_VERSION || "1.3.Beta"}</p>
            </div>

        </div>
    );
}