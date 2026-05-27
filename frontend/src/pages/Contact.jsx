export default function Contact() {
    const people = [
        {
            name: "Omkar Tamalwad",
            role: "Developer",
            email: "tamalwadomkar2006@gmail.com",
            github: { user: "Omii-004", url: "https://github.com/Omii-004" },
            twitter: { user: "@omii_004", url: "https://twitter.com/omii_004" },
            linkedin: { user: "omkar-tamalwad", url: "https://linkedin.com/in/omkar-tamalwad" },
            location: "India",
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
        <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-950 text-gray-900 dark:text-gray-100 flex items-center justify-center px-4 py-16">
            <div className="w-full max-w-4xl">

                {/* header */}
                <div className="text-center mb-14">
                    <div className="mx-auto w-16 h-16 flex items-center justify-center rounded-2xl bg-blue-50 dark:bg-blue-900/30 border border-blue-100 dark:border-blue-800 mb-6">
                        <svg xmlns="http://www.w3.org/2000/svg" className="w-7 h-7 text-blue-600 dark:text-blue-400"
                            viewBox="0 0 24 24" fill="none" stroke="currentColor"
                            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                        </svg>
                    </div>
                    <h1 className="text-4xl font-bold mb-2">Contact Me</h1>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">Feel free to reach out anytime</p>
                </div>

                {/* two equal cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {people.map((p) => (
                        <div
                            key={p.name}
                            className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/50 p-6 text-left space-y-4 shadow-sm hover:shadow-md transition-shadow"
                        >
                            {/* avatar + name/role */}
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-lg shrink-0">
                                    {p.name.charAt(0)}
                                </div>
                                <div>
                                    <p className="text-lg font-semibold">{p.name}</p>
                                    <p className="text-xs text-gray-400 dark:text-gray-500">{p.role}</p>
                                </div>
                            </div>

                            <div className="border-t border-gray-100 dark:border-gray-700" />

                            {/* contact rows */}
                            <a href={`mailto:${p.email}`}
                               className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition min-w-0">
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">✉</span>
                                <span className="break-all">{p.email}</span>
                            </a>
                            <a href={p.github.url}
                               target="_blank" rel="noopener noreferrer"
                               className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition min-w-0">
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">⌂</span>
                                <span className="break-all">{p.github.user}</span>
                            </a>
                            <a href={p.twitter.url}
                               target="_blank" rel="noopener noreferrer"
                               className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition min-w-0">
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">𝕏</span>
                                <span className="break-all">{p.twitter.user}</span>
                            </a>
                            <a href={p.linkedin.url}
                               target="_blank" rel="noopener noreferrer"
                               className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition min-w-0">
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">🔗</span>
                                <span className="break-all">{p.linkedin.user}</span>
                            </a>
                            <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400 min-w-0">
                                <span className="text-gray-400 dark:text-gray-500 w-5 shrink-0 text-center">📍</span>
                                <span className="break-all">{p.location}</span>
                            </div>
                        </div>
                    ))}
                </div>

                <footer className="text-center text-xs text-gray-400 dark:text-gray-600 pt-12 border-t border-gray-100 dark:border-gray-800 mt-14">
                    <p className="font-medium text-gray-500 dark:text-gray-500">
                        Built with ❤️ using React + Tailwind
                    </p>
                    <p className="mt-1">© {new Date().getFullYear()} FlickerX. All rights reserved.</p>
                </footer>

            </div>
        </div>
    );
}