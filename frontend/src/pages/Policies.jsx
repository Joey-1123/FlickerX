import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function Policies() {
    return (
        <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">
            <div className="max-w-3xl mx-auto px-6 py-10">
                <Link to="/" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline mb-6">
                    <ArrowLeft className="w-4 h-4" /> Back to home
                </Link>

                <h1 className="text-3xl font-bold mb-8">Policies & Terms</h1>

                <div className="space-y-8">
                    <section className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                        <h2 className="text-lg font-semibold mb-3">Terms of Service</h2>
                        <div className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed space-y-2">
                            <p>These terms govern your use of FlickerX. By accessing or using the service, you agree to be bound by these terms.</p>
                            <p>You are responsible for maintaining the confidentiality of your account and for all activities under your account.</p>
                            <p>You may not use the service for any unlawful purpose or in violation of any applicable laws.</p>
                            <p>We reserve the right to modify these terms at any time. Changes will be effective immediately upon posting.</p>
                            <p>The service is provided "as is" without warranties of any kind, either express or implied.</p>
                            <p className="text-gray-400 dark:text-gray-500 italic mt-3">[Details to be updated]</p>
                        </div>
                    </section>

                    <section className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                        <h2 className="text-lg font-semibold mb-3">Privacy Policy</h2>
                        <div className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed space-y-2">
                            <p>We collect information you provide when creating an account, including your email address and name.</p>
                            <p>Chat messages and uploaded files are processed to provide the AI service and are not shared with third parties.</p>
                            <p>We do not sell your personal data to third parties.</p>
                            <p>We use cookies and similar technologies to maintain session state and improve your experience.</p>
                            <p>You may request deletion of your account and associated data at any time through your profile settings.</p>
                            <p className="text-gray-400 dark:text-gray-500 italic mt-3">[Details to be updated]</p>
                        </div>
                    </section>

                    <section className="p-6 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900">
                        <h2 className="text-lg font-semibold mb-3">Cookies Policy</h2>
                        <div className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed space-y-2">
                            <p>FlickerX uses cookies and local storage to provide essential functionality:</p>
                            <ul className="list-disc pl-5 space-y-1">
                                <li><strong>Authentication:</strong> JWT tokens are stored to maintain your session.</li>
                                <li><strong>Preferences:</strong> Theme selection, model choice, and settings are saved locally.</li>
                                <li><strong>Session Data:</strong> Chat history is stored in your browser for quick access.</li>
                            </ul>
                            <p>You can clear this data at any time through your browser settings.</p>
                            <p className="text-gray-400 dark:text-gray-500 italic mt-3">[Details to be updated]</p>
                        </div>
                    </section>
                </div>

                <div className="mt-10 text-center text-xs text-gray-400 dark:text-gray-500">
                    <p>&copy; {new Date().getFullYear()} FlickerX. All rights reserved.</p>
                </div>
            </div>
        </div>
    );
}
