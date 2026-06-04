import { useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { resetPassword } from "../services/auth";

export default function ResetPassword() {
    const [searchParams] = useSearchParams();
    const token = searchParams.get("token");
    const navigate = useNavigate();

    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setMessage("");

        if (!token) {
            setError("Invalid or missing reset token.");
            return;
        }

        if (password.length < 8) {
            setError("Password must be at least 8 characters.");
            return;
        }

        if (password !== confirm) {
            setError("Passwords do not match.");
            return;
        }

        setLoading(true);
        try {
            const res = await resetPassword(token, password);
            setMessage(res.message);
            setTimeout(() => navigate("/login"), 2000);
        } catch (err) {
            setError(err.message || "Failed to reset password.");
        } finally {
            setLoading(false);
        }
    };

    if (!token) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950 px-4">
                <div className="w-full max-w-md rounded-3xl bg-white dark:bg-gray-900 p-8 shadow-lg border border-slate-200 dark:border-gray-800 text-center">
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-100 mb-2">Invalid Link</h1>
                    <p className="text-sm text-slate-500 dark:text-gray-400 mb-4">
                        This password reset link is invalid or expired.
                    </p>
                    <Link to="/forgot-password" className="text-blue-600 hover:underline text-sm">
                        Request a new reset link
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950 px-4">
            <div className="w-full max-w-md rounded-3xl bg-white dark:bg-gray-900 p-8 shadow-lg border border-slate-200 dark:border-gray-800">
                <div className="text-center mb-6">
                    <div className="h-10 w-10 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold mx-auto mb-4">
                        F
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-100">Reset Password</h1>
                    <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">
                        Enter your new password.
                    </p>
                </div>

                {message && (
                    <div className="rounded-2xl bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-900 px-4 py-3 text-sm text-green-700 dark:text-green-400 mb-4">
                        {message} Redirecting to login...
                    </div>
                )}

                {error && (
                    <div className="rounded-2xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 px-4 py-3 text-sm text-red-700 dark:text-red-400 mb-4">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="New password (min 8 chars)"
                        required
                        className="w-full rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm outline-none focus:border-blue-500 text-slate-900 dark:text-gray-100"
                    />
                    <input
                        type="password"
                        value={confirm}
                        onChange={(e) => setConfirm(e.target.value)}
                        placeholder="Confirm new password"
                        required
                        className="w-full rounded-2xl border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm outline-none focus:border-blue-500 text-slate-900 dark:text-gray-100"
                    />
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full rounded-2xl bg-blue-600 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition"
                    >
                        {loading ? "Resetting..." : "Reset Password"}
                    </button>
                </form>

                <p className="text-center text-sm text-slate-500 dark:text-gray-400 mt-6">
                    <Link to="/login" className="text-blue-600 hover:underline">Back to Login</Link>
                </p>
            </div>
        </div>
    );
}
