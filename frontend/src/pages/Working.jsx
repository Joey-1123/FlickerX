import { Command } from "lucide-react";

export default function Working() {
    // Define the list of commands with their details
    const commands = [
        {
            name: "/fix",
            title: "Fix Code Errors",
            description:
                "This command helps you debug code issues. It analyzes your code, finds errors, and suggests clean fixes like a senior developer.",
            usage: "/fix your code or error message",
            example: "/fix TypeError: Cannot read properties of undefined",
        },
        {
            name: "/explain",
            title: "Explain Concepts",
            description:
                "Breaks down complex topics into simple explanations that are easy to understand, even for beginners.",
            usage: "/explain any topic",
            example: "/explain closures in JavaScript",
        },
        {
            name: "/summarize",
            title: "Summarize Content",
            description:
                "Turns long text, articles, or notes into short and structured summaries.",
            usage: "/summarize your text",
            example: "/summarize React lifecycle methods in simple points",
        },
        {
            name: "/code",
            title: "Generate Code",
            description:
                "Generates clean and optimized code based on your prompt.",
            usage: "/code what you want to build",
            example: "/code build a login form in React",
        },
        {
            name: "/debug",
            title: "Debug Issues",
            description:
                "Helps identify logical or runtime errors and explains why they happen.",
            usage: "/debug your error",
            example: "/debug Cannot read property 'map' of undefined",
        },
        {
            name: "/optimize",
            title: "Optimize Backend",
            description:
                "Improve backend logic, performance, and structure for scalable applications.",
            usage: "/optimize your backend logic",
            example: "/optimize Express API performance",
        },
        {
            name: "/analyze",
            title: "Logic Analysis",
            description:
                "Analyzes logic flow and identifies issues or improvements in your system or code.",
            usage: "/analyze your logic or system",
            example: "/analyze authentication flow",
        },
        {
            name: "/api",
            title: "Generate API",
            description:
                "Generates backend API structure, endpoints, and architecture suggestions.",
            usage: "/api what you want to build",
            example: "/api user authentication system",
        },
        {
            name: "/docs",
            title: "Write Documentation",
            description:
                "Creates clean, structured technical documentation for your project or code.",
            usage: "/docs your project or feature",
            example: "/docs REST API for ecommerce app",
        },
    ];

    return (
        <div className="min-h-screen bg-white text-gray-900">

            {/* Header */}
            <div className="max-w-4xl mx-auto px-6 py-14 text-center">
                <div className="flex justify-center mb-4">
                    <div className="p-3 rounded-xl bg-blue-50 border border-blue-100">
                        <Command className="h-6 w-6 text-blue-600" />
                    </div>
                </div>

                <h1 className="text-4xl font-bold mb-3">
                    Slash Commands Guide
                </h1>

                <p className="text-gray-500 text-sm max-w-2xl mx-auto">
                    Learn how to use FlickerX commands to control AI faster and improve your workflow.
                </p>
            </div>

            {/* Blog Content */}
            <div className="max-w-3xl mx-auto px-6 pb-20 space-y-12">

                {commands.map((cmd, index) => (
                    <article
                        key={index}
                        className="border-b border-gray-100 pb-10"
                    >

                        {/* Command Title */}
                        <h2 className="text-2xl font-semibold text-blue-600 mb-2">
                            {cmd.name} — {cmd.title}
                        </h2>

                        {/* Description */}
                        <p className="text-gray-600 text-sm leading-relaxed mb-4">
                            {cmd.description}
                        </p>

                        {/* Usage */}
                        <div className="mb-3">
                            <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-1">
                                Usage
                            </h3>
                            <code className="block bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700">
                                {cmd.usage}
                            </code>
                        </div>

                        {/* Example */}
                        <div>
                            <h3 className="text-xs uppercase tracking-wider text-gray-400 mb-1">
                                Example
                            </h3>
                            <code className="block bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-sm text-gray-700">
                                {cmd.example}
                            </code>
                        </div>

                    </article>
                ))}

            </div>
        </div>
    );
}