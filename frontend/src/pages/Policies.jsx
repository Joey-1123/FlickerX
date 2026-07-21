import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
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

export default function Policies() {
    const navigate = useNavigate();
    const { accent, colors } = useTheme();

    // Get the dynamic styles based on the current context
    const themeStyles = getAccentClasses(accent);
    const ringClass = colors[accent]?.ring || "ring-blue-500";

    return (
        <div className="min-h-screen bg-white dark:bg-[#0a0a0a] text-gray-900 dark:text-gray-100 transition-colors duration-300">
            <div className="max-w-3xl mx-auto px-6 py-10">

                {/* Header */}
                <div className="text-center mb-14">
                    <div className={`mx-auto w-16 h-16 flex items-center justify-center rounded-2xl transition-colors duration-300 border ${themeStyles.softBg} ${themeStyles.softBorder} mb-6`}>
                        <svg xmlns="http://www.w3.org/2000/svg" className={`w-7 h-7 transition-colors duration-300 ${themeStyles.icon}`}
                            viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                        </svg>
                    </div>
                    <h1 className="text-4xl font-bold mb-2">Policies & Terms</h1>
                    <p className="text-gray-500 dark:text-gray-400 text-sm transition-colors duration-300">Please read our terms, conditions, and privacy guidelines carefully</p>
                </div>

                <div className="space-y-8">
                    {/* Terms Section */}
                    <section className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-[#111111] transition-colors duration-300">
                        <h2 className="text-lg font-semibold mb-3">Terms of Service</h2>
                        <div className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed space-y-2 transition-colors duration-300">
                            <ul className="list-disc pl-5 space-y-1">
                                <li><p>These terms govern your use of FlickerX. By accessing or using the service, you agree to be bound by these terms.</p></li>
                                <li><p>You are responsible for maintaining the confidentiality of your account and for all activities under your account.</p></li>
                                <li><p>You may not use the service for any unlawful purpose or in violation of any applicable laws.</p></li>
                                <li><p>We reserve the right to modify these terms at any time. Changes will be effective immediately upon posting.</p></li>
                                <li><p>The service is provided "as is" without warranties of any kind, either express or implied.</p></li>
                            </ul>
                            <p className="text-gray-400 dark:text-gray-500 italic mt-3 transition-colors duration-300">[Details to be updated]</p>
                        </div>
                    </section>

                    {/* Privacy Section */}
                    <section className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-[#111111] transition-colors duration-300">
                        <h2 className="text-lg font-semibold mb-3">Privacy Policy</h2>
                        <div className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed space-y-2 transition-colors duration-300">
                            <ul className="list-disc pl-5 space-y-1">
                                <li><p>We collect information you provide when creating an account, including your email address and name.</p></li>
                                <li><p>Chat messages and uploaded files are processed to provide the AI service and are not shared with third parties.</p></li>
                                <li><p>We do not sell your personal data to third parties.</p></li>
                                <li><p>We use cookies and similar technologies to maintain session state and improve your experience.</p></li>
                                <li><p>You may request deletion of your account and associated data at any time through your profile settings.</p></li>
                            </ul>
                            <p className="text-gray-400 dark:text-gray-500 italic mt-3 transition-colors duration-300">[Details to be updated]</p>
                        </div>
                    </section>

                    {/* Cookies Section */}
                    <section className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-[#111111] transition-colors duration-300">
                        <h2 className="text-lg font-semibold mb-3">Cookies Policy</h2>
                        <div className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed space-y-2 transition-colors duration-300">
                            <p>FlickerX uses cookies and local storage to provide essential functionality:</p>
                            <ul className="list-disc pl-5 space-y-1">
                                <li><strong>Authentication:</strong> JWT tokens are stored to maintain your session.</li>
                                <li><strong>Preferences:</strong> Theme selection, model choice, and settings are saved locally.</li>
                                <li><strong>Session Data:</strong> Chat history is stored in your browser for quick access.</li>
                            </ul>
                            <p>You can clear this data at any time through your browser settings.</p>
                            <p className="text-gray-400 dark:text-gray-500 italic mt-3 transition-colors duration-300">[Details to be updated]</p>
                        </div>
                    </section>

                    {/* Back Button */}
                    <div className="flex justify-center w-full ml-auto mr-auto mt-10 md:col-span-3">
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
                <div className="text-center text-gray-400 dark:text-gray-600 text-xs pb-10 border-t border-gray-100 dark:border-gray-800 pt-6 mt-10 transition-colors duration-300">
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