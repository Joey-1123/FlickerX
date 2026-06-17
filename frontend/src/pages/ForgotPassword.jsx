import { useState } from "react";
import { Link } from "react-router-dom";
import { forgotPassword } from "../services/auth";

export default function ForgotPassword() {
    const [email, setEmail] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");
        if (!email.trim()) return;
        setLoading(true);
        try {
            const res = await forgotPassword(email);
            setMessage(res.message);
        } catch (err) {
            setError(err.message || "Something went wrong.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950 px-4">
            <div className="w-full max-w-md rounded-3xl bg-white dark:bg-gray-900 p-8 shadow-lg border border-slate-200 dark:border-gray-800">
                <div className="text-center mb-6">
                    <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold mx-auto mb-4">
                        F
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-100">Forgot Password</h1>
                    <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">
                        Enter your email to receive a reset link.
                    </p>
                </div>

                {message && (
                    <div className="rounded-2xl bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-900 px-4 py-3 text-sm text-green-700 dark:text-green-400 mb-4">
                        {message}
                    </div>
                )}

                {error && (
                    <div className="rounded-2xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 px-4 py-3 text-sm text-red-700 dark:text-red-400 mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Your email"
                        required
                        className="w-full rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm outline-none focus:border-blue-500 text-slate-900 dark:text-gray-100"
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full rounded-2xl bg-blue-600 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition"
                    >
                        {loading ? "Sending..." : "Send Reset Link"}
                    </button>
                </form>

                <p className="text-center text-sm text-slate-500 dark:text-gray-400 mt-6">
                    Remember your password?{" "}
                    <Link to="/login" className="text-blue-600 hover:underline">Login</Link>
                </p>
            </div>
        </div>
    );
}
