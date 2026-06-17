// Home.jsx - The landing page with hero section, features, and workflow explanation
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useEffect } from "react";
// Lucide icons
import { Sparkles, ArrowRight, Brain, CheckCircle2 } from "lucide-react";
import { MessageSquare, FileText, Terminal } from "lucide-react";

export default function Home() {
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (isAuthenticated) navigate("/chat");
    }, [isAuthenticated, navigate]);

    return (
        <div className="min-h-screen bg-white text-gray-900 flex flex-col font-sans">

            {/* Navbar */}
            <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur border-b border-gray-200 px-6 py-4 flex justify-between items-center">

                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold shadow-sm">
                        F
                    </div>
                    <h1 className="text-xl font-bold text-gray-900">
                        FlickerX
                    </h1>
                </div>

                <div className="flex items-center gap-3">
                    {!isAuthenticated ? (
                        <>
                            <Link
                                to="/login"
                                className="px-4 py-2 text-sm rounded-xl border border-gray-300 hover:bg-gray-50 transition"
                            >
                                Login
                            </Link>

                            <Link
                                to="/working"
                                className="px-4 py-2 text-sm rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition shadow-sm"
                            >
                                Working
                            </Link>
                        </>
                    ) : (
                        <Link
                            to="/chat"
                            className="px-4 py-2 text-sm rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition shadow-sm"
                        >
                            Go to Chat
                        </Link>
                    )}
                </div>
            </nav>

            {/* Hero Section */}
            <section className="flex-1 flex flex-col justify-center items-center text-center px-6 max-w-5xl mx-auto py-12 sm:py-20">
                {/* Top Badge */}
                <span className="px-4 py-1.5 bg-blue-50/80 text-blue-600 border border-blue-100/60 rounded-full text-xs font-semibold tracking-wide flex items-center gap-2 mb-8 shadow-sm">
                    <Sparkles className="h-3.5 w-3.5 text-blue-600 animate-pulse" />
                    AI Chat + File Intelligence Platform
                </span>

                {/* Main Headline */}
                <h2 className="text-4xl sm:text-6xl font-extrabold mb-6 leading-tight tracking-tight text-gray-900">
                    Build smarter workflows with{" "}
                    <span className="text-blue-600 underline decoration-blue-200 decoration-wavy underline-offset-4">
                        AI-powered chat
                    </span>
                </h2>

                {/* Description */}
                <p className="text-gray-500 text-lg max-w-2xl mb-10 leading-relaxed">
                    FlickerX is your intelligent assistant for coding, debugging, learning, and analyzing files. Chat with AI, upload documents, and get structured answers instantly.
                </p>

                {/* Buttons */}
                <div className="flex gap-4 flex-wrap justify-center items-center">
                    {!isAuthenticated ? (
                        <Link
                            to="/login"
                            className="px-6 py-3 font-semibold rounded-xl bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-all duration-300 flex items-center gap-2"
                        >
                            Start Free
                            <ArrowRight className="h-4 w-4" />
                        </Link>
                    ) : (
                        <Link
                            to="/chat"
                            className="px-6 py-3 font-semibold rounded-xl bg-blue-600 text-white hover:bg-blue-700 shadow-sm shadow-blue-500/10 transition-all duration-300 flex items-center gap-2"
                        >
                            Open Chat
                            <ArrowRight className="h-4 w-4" />
                        </Link>
                    )}

                    <a
                        href="#features"
                        className="px-6 py-3 font-medium rounded-xl border border-gray-200 bg-white/80 text-gray-700 hover:bg-gray-50/80 hover:text-gray-900 transition-all duration-300 shadow-sm"
                    >
                        Explore Features
                    </a>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="py-12 sm:py-20 border-t border-gray-100 bg-gray-50/60 backdrop-blur-sm">
                <div className="text-center max-w-2xl mx-auto mb-14 px-6">
                    <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50/80 border border-blue-100/50 px-3 py-1 rounded-md shadow-sm">
                        Features
                    </span>
                    <h3 className="text-3xl font-bold tracking-tight text-gray-900 mt-5 mb-3">
                        Everything you need in one AI tool
                    </h3>
                    <p className="text-gray-500 text-sm max-w-md mx-auto leading-relaxed">
                        Built for developers, students, and creators who want faster, more consistent results.
                    </p>
                </div>

                <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-6 px-6">

                    {/* Smart Chat Card */}
                    <div className="bg-white p-7 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200/80 transition-all duration-300 flex flex-col items-start">
                        <div className="h-10 w-10 rounded-xl bg-blue-50 border border-blue-100/80 flex items-center justify-center mb-5">
                            <MessageSquare className="h-5 w-5 text-blue-600" />
                        </div>
                        <h4 className="font-semibold text-sm text-gray-800 mb-2">
                            Smart Chat
                        </h4>
                        <p className="text-gray-400 text-xs leading-relaxed">
                            Ask anything, debug technical errors, or brainstorm new data workflows with AI.
                        </p>
                    </div>

                    {/* File Understanding Card */}
                    <div className="bg-white p-7 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200/80 transition-all duration-300 flex flex-col items-start">
                        <div className="h-10 w-10 rounded-xl bg-blue-50 border border-blue-100/80 flex items-center justify-center mb-5">
                            <FileText className="h-5 w-5 text-blue-600" />
                        </div>
                        <h4 className="font-semibold text-sm text-gray-800 mb-2">
                            File Understanding
                        </h4>
                        <p className="text-gray-400 text-xs leading-relaxed">
                            Upload architecture files or code snippets and get summaries, explanations, or fixes.
                        </p>
                    </div>

                    {/* Slash Commands Card */}
                    <div className="bg-white p-7 rounded-2xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200/80 transition-all duration-300 flex flex-col items-start">
                        <div className="h-10 w-10 rounded-xl bg-blue-50 border border-blue-100/80 flex items-center justify-center mb-5">
                            <Terminal className="h-5 w-5 text-blue-600" />
                        </div>
                        <h4 className="font-semibold text-sm text-gray-800 mb-2">
                            Slash Commands
                        </h4>
                        <p className="text-gray-400 text-xs leading-relaxed">
                            Speed up your control with shortcuts like `/fix`, `/explain`, and `/summarize` on your dashboard.
                        </p>
                    </div>

                </div>
            </section>

            {/* How It Works Section */}
            <section className="py-12 sm:py-20 bg-white/50 backdrop-blur-sm">
                <div className="text-center max-w-3xl mx-auto mb-16 px-6">
                    <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50/80 border border-blue-100/50 px-3 py-1 rounded-md shadow-sm">
                        Workflow
                    </span>
                    <h3 className="text-3xl font-bold tracking-tight text-gray-900 mt-5 mb-3">
                        How FlickerX works
                    </h3>
                    <p className="text-sm text-gray-500 max-w-md mx-auto leading-relaxed">
                        Experience a streamlined AI-driven workflow designed for analytical depth, from input to insights.
                    </p>
                </div>

                <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-8 px-6 text-center">

                    {/* Step 1 */}
                    <div className="flex flex-col items-center p-8 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200/80 transition-all duration-300">
                        <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100/80 flex items-center justify-center mb-6">
                            <span className="text-blue-600 font-bold text-base">1</span>
                        </div>
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">
                            Input or Upload
                        </h4>
                        <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
                            Start a chat, share files, or use prompts for complex logic and optimization.
                        </p>
                    </div>

                    {/* Step 2 */}
                    <div className="flex flex-col items-center p-8 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200/80 transition-all duration-300">
                        <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100/80 flex items-center justify-center mb-6">
                            <span className="text-blue-600 font-bold text-base">2</span>
                        </div>
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">
                            Analyze Input
                        </h4>
                        <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
                            The engine processes your queries instantly while checking for analytical consistency.
                        </p>
                    </div>

                    {/* Step 3 */}
                    <div className="flex flex-col items-center p-8 rounded-2xl bg-white border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200/80 transition-all duration-300">
                        <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100/80 flex items-center justify-center mb-6">
                            <span className="text-blue-600 font-bold text-base">3</span>
                        </div>
                        <h4 className="text-sm font-semibold text-gray-800 mb-2">
                            Intelligent Response
                        </h4>
                        <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
                            Get structured insights and solutions displayed directly on the dashboard.
                        </p>
                    </div>

                </div>
            </section>

            {/* Footer */}
            <footer className="text-center text-black text-xs py-6 border-t border-gray-200/50 bg-white/70 backdrop-blur-md">
                <p>&copy; {new Date().getFullYear()} FlickerX. Built for smart conversations. All rights reserved.</p>
                <p className="mt-1">
                    <Link to="/policies" className="text-blue-600 hover:underline">Policies & Terms</Link>
                </p>
                <p className="mt-1 text-gray-400">v{import.meta.env.VITE_APP_VERSION || "1.3.Beta"}</p>
            </footer>
        </div>
    );
}