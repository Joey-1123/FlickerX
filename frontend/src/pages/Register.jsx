import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Register() {
    const { isAuthenticated, register } = useAuth();
    const navigate = useNavigate();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [agreeTerms, setAgreeTerms] = useState(false);
    const [agreePrivacy, setAgreePrivacy] = useState(false);
    const [agreeCookies, setAgreeCookies] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const allAgreed = agreeTerms && agreePrivacy && agreeCookies;

    useEffect(() => {
        if (isAuthenticated) {
            navigate("/chat");
        }
    }, [isAuthenticated, navigate]);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setErrorMessage("");
        if (!allAgreed) {
            setErrorMessage("You must accept all policies to create an account.");
            return;
        }
        setIsLoading(true);

        try {
            await register(email, password, name, { agreeTerms, agreePrivacy, agreeCookies });
            navigate("/chat");
        } catch (err) {
            setErrorMessage(err.message || "Unable to register");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
            <div className="w-full max-w-md rounded-3xl bg-white p-6 sm:p-8 shadow-lg border border-slate-200">
                <h1 className="text-3xl font-bold text-slate-900 mb-4">Create an account</h1>
                <p className="text-sm text-slate-500 mb-8">
                    Register to securely access FlickerX chat and file intelligence.
                </p>
                <form className="space-y-5" onSubmit={handleSubmit}>
                    <label className="block">
                        <span className="text-sm font-medium text-slate-700">Full name</span>
                        <input
                            type="text"
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            className="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-100"
                            placeholder="Jane Doe"
                            required
                        />
                    </label>
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
                            placeholder="At least 8 characters"
                            minLength={8}
                            required
                        />
                    </label>
                    {/* Agreements */}
                    <div className="space-y-3 border-t border-slate-200 pt-4 mt-2">
                        <p className="text-xs font-medium text-slate-600">By creating an account, you agree to:</p>
                        <label className="flex items-start gap-2 cursor-pointer">
                            <input type="checkbox" checked={agreeTerms} onChange={(e) => setAgreeTerms(e.target.checked)} className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                            <span className="text-xs text-slate-600">
                                <Link to="/policies" target="_blank" className="text-blue-600 hover:underline">Terms of Service</Link>
                            </span>
                        </label>
                        <label className="flex items-start gap-2 cursor-pointer">
                            <input type="checkbox" checked={agreePrivacy} onChange={(e) => setAgreePrivacy(e.target.checked)} className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                            <span className="text-xs text-slate-600">
                                <Link to="/policies" target="_blank" className="text-blue-600 hover:underline">Privacy Policy</Link>
                            </span>
                        </label>
                        <label className="flex items-start gap-2 cursor-pointer">
                            <input type="checkbox" checked={agreeCookies} onChange={(e) => setAgreeCookies(e.target.checked)} className="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                            <span className="text-xs text-slate-600">
                                <Link to="/policies" target="_blank" className="text-blue-600 hover:underline">Cookies Policy</Link>
                            </span>
                        </label>
                    </div>

                    {errorMessage ? (
                        <div className="rounded-2xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                            {errorMessage}
                        </div>
                    ) : null}
                    <button
                        type="submit"
                        disabled={isLoading || !allAgreed}
                        className="w-full rounded-2xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                    >
                        {isLoading ? "Creating account..." : "Register"}
                    </button>
                </form>
                <p className="mt-6 text-center text-sm text-slate-500">
                    Already have an account?
                </p>
                <div className="mt-4 text-center text-sm">
                    <Link to="/login" className="text-blue-600 hover:underline">
                        Log in instead
                    </Link>
                </div>
            </div>
        </div>
    );
}
