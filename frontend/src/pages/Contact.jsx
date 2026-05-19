// Contact.jsx - A simple contact page with email and GitHub links
export default function Contact() {
    return (
        <div className="min-h-screen bg-white text-gray-900 flex items-center justify-center px-6">

            <div className="w-full max-w-md text-center">

                {/* Icon */}
                <div className="mx-auto w-14 h-14 flex items-center justify-center rounded-2xl bg-blue-50 border border-blue-100 mb-6">
                    <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6 text-blue-600"
                        viewBox="0 0 24 24" fill="none" stroke="currentColor"
                        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                </div>

                {/* Title */}
                <h1 className="text-3xl font-bold mb-2">
                    Contact Me
                </h1>

                <p className="text-gray-500 text-sm mb-10">
                    Feel free to reach out anytime
                </p>

                {/* Cards */}
                <div className="space-y-4">

                    {/* Email */}
                    <a
                        href="mailto:tamalwadomkar2006@gmail.com"
                        className="flex items-center gap-4 p-4 rounded-2xl border border-gray-200 hover:border-gray-400 hover:bg-gray-50 transition"
                    >
                        <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-100 border border-gray-200">
                            <svg xmlns="http://www.w3.org/2000/svg"
                                className="w-5 h-5 text-gray-700"
                                viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" strokeWidth="2"
                                strokeLinecap="round" strokeLinejoin="round">
                                <rect width="20" height="16" x="2" y="4" rx="2" />
                                <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                            </svg>
                        </div>

                        <div className="text-left">
                            <p className="text-sm font-semibold">Email</p>
                            <p className="text-xs text-gray-500">tamalwadomkar2006@gmail.com</p>
                        </div>
                    </a>

                    {/* GitHub */}
                    <a
                        href="https://github.com/Omii-004"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-4 p-4 rounded-2xl border border-gray-200 hover:border-gray-400 hover:bg-gray-50 transition"
                    >
                        <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-gray-100 border border-gray-200">
                            <svg xmlns="http://www.w3.org/2000/svg"
                                className="w-5 h-5 text-gray-700"
                                viewBox="0 0 24 24" fill="none"
                                stroke="currentColor" strokeWidth="2"
                                strokeLinecap="round" strokeLinejoin="round">
                                <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.26 1.23-.26 1.86v4" />
                            </svg>
                        </div>

                        <div className="text-left">
                            <p className="text-sm font-semibold">GitHub</p>
                            <p className="text-xs text-gray-500">github.com/Omii-004</p>
                        </div>
                    </a>

                </div>

                <footer className="text-center text-xs text-gray-400 pt-10 border-t border-gray-100 mt-10">
                    <p className="font-medium text-gray-500">
                        Built with ❤️ using React + Tailwind
                    </p>
                    <p className="mt-1">
                        © {new Date().getFullYear()} FlickerX. All rights reserved.
                    </p>
                </footer>

            </div>
        </div>
    );
}