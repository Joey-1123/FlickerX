import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
    const { isAuthenticated, login } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    useEffect(() => {
        if (isAuthenticated) {
            navigate("/chat");
        }
    }, [isAuthenticated, navigate]);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setErrorMessage("");
        setIsLoading(true);

        try {
            await login(email, password);
            navigate("/chat");
        } catch (err) {
            setErrorMessage(err.message || "Unable to login");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
            <div className="w-full max-w-md rounded-3xl bg-white p-8 shadow-lg border border-slate-200">
                <h1 className="text-3xl font-bold text-slate-900 mb-4">Login</h1>
                <p className="text-sm text-slate-500 mb-8">
                    Sign in with your email and password to access FlickerX chat.
                </p>
                <form className="space-y-5" onSubmit={handleSubmit}>
                    <label className="block">
                        <span className="text-sm font-medium text-slate-700">Email</span>
                        <input
                            type="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                            placeholder="you@example.com"
                            required
                        />
                    </label>
                    <label className="block">
                        <span className="text-sm font-medium text-slate-700">Password</span>
                        <input
                            type="password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                            placeholder="Enter your password"
                            required
                        />
                    </label>
                    {errorMessage ? (
                        <div className="rounded-2xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                            {errorMessage}
                        </div>
                    ) : null}
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full rounded-2xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                    >
                        {isLoading ? "Logging in..." : "Log in"}
                    </button>
                </form>
                <p className="mt-6 text-center text-sm text-slate-500">
                    Don&apos;t have an account? You can use any credentials for demo access.
                </p>
                <div className="mt-4 text-center text-sm">
                    <Link to="/register" className="text-blue-600 hover:underline">
                        Create a new account
                    </Link>
                </div>
                <div className="mt-4 text-center text-sm">
                    <Link to="/" className="text-blue-600 hover:underline">
                        Back to home
                    </Link>
                </div>
            </div>
        </div>
    );
}
