import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
    const { isAuthenticated, login, acceptPolicies } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");
    const [showAcceptance, setShowAcceptance] = useState(false);
    const [agreeTerms, setAgreeTerms] = useState(false);
    const [agreePrivacy, setAgreePrivacy] = useState(false);
    const [agreeCookies, setAgreeCookies] = useState(false);
    const [accepting, setAccepting] = useState(false);

    const allAgreed = agreeTerms && agreePrivacy && agreeCookies;

    useEffect(() => {
        if (isAuthenticated && !showAcceptance) {
            navigate("/chat");
        }
    }, [isAuthenticated, showAcceptance, navigate]);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setErrorMessage("");
        setIsLoading(true);

        try {
            const data = await login(email, password);
            if (data.needsAcceptance) {
                setShowAcceptance(true);
            } else {
                navigate("/chat");
            }
        } catch (err) {
            setErrorMessage(err.message || "Unable to login");
        } finally {
            setIsLoading(false);
        }
    };

    const handleAccept = async () => {
        if (!allAgreed) return;
        setAccepting(true);
        try {
            await acceptPolicies({ agreeTerms, agreePrivacy, agreeCookies });
            setShowAcceptance(false);
            navigate("/chat");
        } catch (err) {
            setErrorMessage(err.message || "Failed to save acceptance.");
        } finally {
            setAccepting(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-gray-950 flex items-center justify-center px-4 py-10">
            <div className="w-full max-w-md rounded-3xl bg-white dark:bg-gray-900 p-6 sm:p-8 shadow-lg border border-slate-200 dark:border-gray-800">
                {!showAcceptance ? (
                    <>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-gray-100 mb-4">Login</h1>
                <p className="text-sm text-slate-500 dark:text-gray-400 mb-8">
                    Sign in with your email and password to access FlickerX chat.
                </p>
                <form className="space-y-5" onSubmit={handleSubmit}>
                    <label className="block">
                        <span className="text-sm font-medium text-slate-700 dark:text-gray-300">Email</span>
                        <input
                            type="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            className="mt-2 w-full rounded-2xl border border-slate-200 dark:border-gray-700 px-4 py-3 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 dark:bg-gray-800 dark:text-gray-100"
                            placeholder="you@example.com"
                            required
                        />
                    </label>
                    <label className="block">
                        <span className="text-sm font-medium text-slate-700 dark:text-gray-300">Password</span>
                        <input
                            type="password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            className="mt-2 w-full rounded-2xl border border-slate-200 dark:border-gray-700 px-4 py-3 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100 dark:bg-gray-800 dark:text-gray-100"
                            placeholder="Enter your password"
                            required
                        />
                        <Link to="/forgot-password" className="mt-1 text-xs text-blue-600 hover:underline inline-block">
                            Forgot password?
                        </Link>
                    </label>
                    {errorMessage ? (
                        <div className="rounded-2xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 px-4 py-3 text-sm text-red-700 dark:text-red-400">
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
                    </>
                ) : (
                    <div className="space-y-4">
                        <h1 className="text-2xl font-bold text-slate-900 dark:text-gray-100">Accept Policies</h1>
                        <p className="text-sm text-slate-500 dark:text-gray-400">
                            Please accept our updated policies to continue using FlickerX.
                        </p>
                        <div className="space-y-3">
                            <label className="flex items-start gap-2 cursor-pointer">
                                <input type="checkbox" checked={agreeTerms} onChange={(e) => setAgreeTerms(e.target.checked)} className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                                <span className="text-xs text-slate-600 dark:text-gray-300">
                                    I accept the <Link to="/policies" target="_blank" className="text-blue-600 hover:underline">Terms of Service</Link>
                                </span>
                            </label>
                            <label className="flex items-start gap-2 cursor-pointer">
                                <input type="checkbox" checked={agreePrivacy} onChange={(e) => setAgreePrivacy(e.target.checked)} className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                                <span className="text-xs text-slate-600 dark:text-gray-300">
                                    I accept the <Link to="/policies" target="_blank" className="text-blue-600 hover:underline">Privacy Policy</Link>
                                </span>
                            </label>
                            <label className="flex items-start gap-2 cursor-pointer">
                                <input type="checkbox" checked={agreeCookies} onChange={(e) => setAgreeCookies(e.target.checked)} className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                                <span className="text-xs text-slate-600 dark:text-gray-300">
                                    I accept the <Link to="/policies" target="_blank" className="text-blue-600 hover:underline">Cookies Policy</Link>
                                </span>
                            </label>
                        </div>
                        {errorMessage ? (
                            <div className="rounded-2xl bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 px-4 py-3 text-sm text-red-700 dark:text-red-400">{errorMessage}</div>
                        ) : null}
                        <button
                            onClick={handleAccept}
                            disabled={accepting || !allAgreed}
                            className="w-full rounded-2xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                        >
                            {accepting ? "Saving..." : "Accept & Continue"}
                        </button>
                    </div>
                )}
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
