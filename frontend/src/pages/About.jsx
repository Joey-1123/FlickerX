import { Link } from "react-router-dom";
import { Sparkles, Bot, FileText, Zap, Shield, Code2 } from "lucide-react";

// About page component with information about FlickerX
export default function About() {
    return (
        <div className="min-h-screen bg-white text-gray-900">

            {/* Header */}
            <div className="max-w-4xl mx-auto px-6 py-16 text-center">

                <div className="flex justify-center mb-5">
                    <div className="p-3 rounded-xl bg-blue-50 border border-blue-100">
                        <Sparkles className="h-6 w-6 text-blue-600" />
                    </div>
                </div>

                <h1 className="text-4xl font-bold mb-4">
                    About FlickerX
                </h1>

                <p className="text-gray-500 text-sm max-w-2xl mx-auto leading-relaxed">
                    FlickerX is a modern AI-powered chat platform designed to help developers,
                    students, and creators work faster using intelligent conversations,
                    file understanding, and slash commands.
                </p>
            </div>

            {/* Mission */}
            <div className="max-w-3xl mx-auto px-6 mb-16">
                <div className="p-6 rounded-2xl border border-gray-100 bg-gray-50">
                    <h2 className="text-lg font-semibold mb-2">Our Mission</h2>
                    <p className="text-sm text-gray-600 leading-relaxed">
                        We aim to simplify complex workflows using AI. Whether you're debugging code,
                        learning new concepts, or generating APIs, FlickerX gives you fast, structured,
                        and useful responses in real time.
                    </p>
                </div>
            </div>

            {/* Features */}
            <div className="max-w-5xl mx-auto px-6 pb-20 grid md:grid-cols-3 gap-6">

                <div className="p-6 border border-gray-100 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                    <Bot className="h-5 w-5 text-blue-600 mb-3" />
                    <h3 className="font-semibold mb-2">AI Chat Assistant</h3>
                    <p className="text-sm text-gray-500">
                        Chat with an intelligent assistant for coding, learning, and problem-solving.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                    <FileText className="h-5 w-5 text-blue-600 mb-3" />
                    <h3 className="font-semibold mb-2">File Understanding</h3>
                    <p className="text-sm text-gray-500">
                        Upload files or code and get instant analysis, summaries, and explanations.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                    <Zap className="h-5 w-5 text-blue-600 mb-3" />
                    <h3 className="font-semibold mb-2">Slash Commands</h3>
                    <p className="text-sm text-gray-500">
                        Use commands like /fix, /explain, and /summarize to control AI faster.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                    <Code2 className="h-5 w-5 text-blue-600 mb-3" />
                    <h3 className="font-semibold mb-2">Developer Friendly</h3>
                    <p className="text-sm text-gray-500">
                        Built for developers with clean responses, code formatting, and debugging support.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                    <Shield className="h-5 w-5 text-blue-600 mb-3" />
                    <h3 className="font-semibold mb-2">Secure Access</h3>
                    <p className="text-sm text-gray-500">
                        Authentication handled securely using JWT sessions for safe user access.
                    </p>
                </div>

                <div className="p-6 border border-gray-100 rounded-2xl bg-white shadow-sm hover:shadow-md transition">
                    <Sparkles className="h-5 w-5 text-blue-600 mb-3" />
                    <h3 className="font-semibold mb-2">Smart Experience</h3>
                    <p className="text-sm text-gray-500">
                        Designed for speed, clarity, and productivity with modern UI/UX.
                    </p>
                </div>

            </div>

            {/* Footer */}
            <div className="text-center text-gray-400 text-xs pb-10 border-t border-gray-100 pt-6">
                <p>&copy; {new Date().getFullYear()} FlickerX. Built for smarter conversations.</p>
                <p className="mt-1">
                    <Link to="/policies" className="text-blue-600 hover:underline">Policies & Terms</Link>
                </p>
                <p className="mt-1 text-gray-500">v{import.meta.env.VITE_APP_VERSION || "1.3.Beta"}</p>
            </div>

        </div>
    );
}