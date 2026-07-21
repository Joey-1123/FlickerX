import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { useTheme } from "../context/ThemeContext"; // Adjust the import path to wherever your provider is located

// Helper to map accent strings to safe Tailwind classes
const getAccentClasses = (accent) => {
    const variants = {
        blue: { icon: "text-blue-600 dark:text-blue-400", softBg: "bg-blue-50 dark:bg-blue-900/20", softBorder: "border-blue-100 dark:border-blue-800/50", hoverBg: "hover:bg-blue-50 dark:hover:bg-blue-900/30", hoverText: "hover:text-blue-600 dark:hover:text-blue-400", gradient: "from-blue-500 to-blue-700" },
        purple: { icon: "text-purple-600 dark:text-purple-400", softBg: "bg-purple-50 dark:bg-purple-900/20", softBorder: "border-purple-100 dark:border-purple-800/50", hoverBg: "hover:bg-purple-50 dark:hover:bg-purple-900/30", hoverText: "hover:text-purple-600 dark:hover:text-purple-400", gradient: "from-purple-500 to-purple-700" },
        green: { icon: "text-green-600 dark:text-green-400", softBg: "bg-green-50 dark:bg-green-900/20", softBorder: "border-green-100 dark:border-green-800/50", hoverBg: "hover:bg-green-50 dark:hover:bg-green-900/30", hoverText: "hover:text-green-600 dark:hover:text-green-400", gradient: "from-green-500 to-green-700" },
        orange: { icon: "text-orange-600 dark:text-orange-400", softBg: "bg-orange-50 dark:bg-orange-900/20", softBorder: "border-orange-100 dark:border-orange-800/50", hoverBg: "hover:bg-orange-50 dark:hover:bg-orange-900/30", hoverText: "hover:text-orange-600 dark:hover:text-orange-400", gradient: "from-orange-500 to-orange-700" },
        pink: { icon: "text-pink-600 dark:text-pink-400", softBg: "bg-pink-50 dark:bg-pink-900/20", softBorder: "border-pink-100 dark:border-pink-800/50", hoverBg: "hover:bg-pink-50 dark:hover:bg-pink-900/30", hoverText: "hover:text-pink-600 dark:hover:text-pink-400", gradient: "from-pink-500 to-pink-700" },
        teal: { icon: "text-teal-600 dark:text-teal-400", softBg: "bg-teal-50 dark:bg-teal-900/20", softBorder: "border-teal-100 dark:border-teal-800/50", hoverBg: "hover:bg-teal-50 dark:hover:bg-teal-900/30", hoverText: "hover:text-teal-600 dark:hover:text-teal-400", gradient: "from-teal-500 to-teal-700" },
    };
    return variants[accent] || variants.blue;
};

export default function Contact() {
    const navigate = useNavigate();
    const { accent, colors } = useTheme();

    // Get the dynamic styles based on the current context
    const themeStyles = getAccentClasses(accent);
    const ringClass = colors[accent]?.ring || "ring-blue-500";

    const people = [
        {
            name: "Omkar Tamalwad",
            role: "Avg TY-BSc AI&ML Student",
            email: "tamalwadomkar2006@gmail.com",
            github: { user: "Omii-004", url: "https://github.com/Omii-004" },
            twitter: { user: "@omii_004", url: "https://twitter.com/omii_004" },
            linkedin: { user: "omkar-tamalwad", url: "https://linkedin.com/in/omkar-tamalwad" },
            location: "Pune, Maharashtra, India",
        },
        {
            name: "Shubham Panchal (Joey)",
            role: "Avg TY-BSc AI&ML Student",
            email: "shubhampanchal9168@gmail.com",
            github: { user: "Joey-1123", url: "https://github.com/Joey-1123" },
            twitter: { user: "@ShubhamPanchal9168", url: "https://twitter.com/ShubhamPanchal9168" },
            linkedin: { user: "Shubhampanchal(Joey)", url: "https://linkedin.com/in/shubhampanchal" },
            location: "Pune, Maharashtra, India",
        },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-[#0a0a0a] dark:to-black text-gray-900 dark:text-gray-100 flex items-center justify-center px-4 py-16 transition-colors duration-300">
            <div className="w-full max-w-4xl">

                {/* Header */}
                <div className="text-center mb-14">
                    <div className={`mx-auto w-16 h-16 flex items-center justify-center rounded-2xl transition-colors duration-300 border ${themeStyles.softBg} ${themeStyles.softBorder} mb-6`}>
                        <svg xmlns="http://www.w3.org/2000/svg" className={`w-7 h-7 transition-colors duration-300 ${themeStyles.icon}`}
                            viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                    </div>
                    <h1 className="text-4xl font-bold mb-2">Contact Us</h1>
                    <p className="text-gray-500 dark:text-gray-400 text-sm transition-colors duration-300">Feel free to reach out anytime</p>
                </div>

                {/* Contact Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {people.map((p) => (
                        <div
                            key={p.name}
                            className="rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-[#111111] p-6 text-left space-y-4 shadow-sm hover:shadow-md transition-all duration-300"
                        >
                            {/* Avatar + Name/Role */}
                            <div className="flex items-center gap-4">
                                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${themeStyles.gradient} flex items-center justify-center text-white font-bold text-lg shrink-0 transition-colors duration-300`}>
                                    {p.name.charAt(0)}
                                </div>
                                <div>
                                    <p className="text-lg font-semibold">{p.name}</p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">{p.role}</p>
                                </div>
                            </div>

                            <div className="border-t border-gray-100 dark:border-gray-800 transition-colors duration-300" />

                            {/* Contact Links */}
                            <a href={`mailto:${p.email}`}
                                className={`flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 ${themeStyles.hoverText} transition-colors duration-300 min-w-0`}>
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">✉</span>
                                <span className="break-all">{p.email}</span>
                            </a>
                            <a href={p.github.url}
                                target="_blank" rel="noopener noreferrer"
                                className={`flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 ${themeStyles.hoverText} transition-colors duration-300 min-w-0`}>
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">⌂</span>
                                <span className="break-all">{p.github.user}</span>
                            </a>
                            <a href={p.twitter.url}
                                target="_blank" rel="noopener noreferrer"
                                className={`flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 ${themeStyles.hoverText} transition-colors duration-300 min-w-0`}>
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">𝕏</span>
                                <span className="break-all">{p.twitter.user}</span>
                            </a>
                            <a href={p.linkedin.url}
                                target="_blank" rel="noopener noreferrer"
                                className={`flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 ${themeStyles.hoverText} transition-colors duration-300 min-w-0`}>
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">🔗</span>
                                <span className="break-all">{p.linkedin.user}</span>
                            </a>
                            <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400 min-w-0 transition-colors duration-300">
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">📍</span>
                                <span className="break-all">{p.location}</span>
                            </div>
                        </div>
                    ))}

                    {/* Back Button */}
                    <div className="flex justify-center w-full mt-6 md:col-span-2">
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
                <div className="text-center text-gray-400 dark:text-gray-600 text-xs mt-10 border-t border-gray-100 dark:border-gray-800 pt-6 transition-colors duration-300">
                    <p>&copy; {new Date().getFullYear()} FlickerX. Built for smarter conversations.</p>
                    <p className="mt-1">
                        <Link to="/policies" className={`transition-colors duration-300 ${themeStyles.icon} hover:underline`}>Policies & Terms</Link>
                    </p>
                    <p className="mt-1 text-gray-500 dark:text-gray-500">v{import.meta.env.VITE_APP_VERSION || "1.3.Beta"}</p>
                </div>

            </div>
        </div>
    );
}