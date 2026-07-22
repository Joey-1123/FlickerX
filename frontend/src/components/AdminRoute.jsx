import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function AdminRoute({ children }) {
    const { isAuthenticated, loading, user } = useAuth();

    if (loading) {
        return <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950"><div className="rounded-3xl bg-white dark:bg-gray-900 p-8 shadow-lg border border-slate-200 dark:border-gray-800 text-gray-900 dark:text-gray-100">Loading...</div></div>;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    if (user?.role !== "admin") {
        return <Navigate to="/" replace />;
    }

    return children;
}
