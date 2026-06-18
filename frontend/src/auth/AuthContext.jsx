import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { login as loginRequest, register as registerRequest, refreshAuth, logout as logoutRequest, acceptPolicies as acceptPoliciesRequest } from "../services/auth";

const AuthContext = createContext(null);

const parseJwt = (token) => {
    if (!token) return null;
    try {
        const payload = token.split(".")[1];
        return JSON.parse(atob(payload));
    } catch {
        return null;
    }
};

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => localStorage.getItem("authToken"));
    const [user, setUser] = useState(() => {
        const stored = localStorage.getItem("authUser");
        return stored ? JSON.parse(stored) : parseJwt(localStorage.getItem("authToken"));
    });
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const initializeAuth = async () => {
            const storedToken = localStorage.getItem("authToken");
            if (storedToken) {
                const payload = parseJwt(storedToken);
                if (payload && payload.exp * 1000 > Date.now()) {
                    setToken(storedToken);
                    setUser((prev) => prev || payload);
                    setLoading(false);
                    return;
                }
                // token expired – fall through to refresh
            }

            try {
                const data = await refreshAuth();
                setToken(data.token);
                setUser(data.user || parseJwt(data.token));
            } catch (_err) {
                setToken(null);
                setUser(null);
            } finally {
                setLoading(false);
            }
        };

        initializeAuth();
    }, []);

    useEffect(() => {
        if (token) {
            localStorage.setItem("authToken", token);
            setUser((prev) => prev || parseJwt(token));
        } else {
            localStorage.removeItem("authToken");
            localStorage.removeItem("authUser");
            setUser(null);
        }
    }, [token]);

    useEffect(() => {
        if (user) {
            localStorage.setItem("authUser", JSON.stringify(user));
        }
    }, [user]);

    const login = async (email, password) => {
        setError(null);
        const data = await loginRequest(email, password);
        setToken(data.token);
        setUser(data.user || parseJwt(data.token));
        return data;
    };

    const register = async (email, password, name, agreements = {}) => {
        setError(null);
        const data = await registerRequest(email, password, name, agreements);
        setToken(data.token);
        setUser(data.user || parseJwt(data.token));
        return data;
    };

    const acceptPolicies = async (agreements) => {
        const data = await acceptPoliciesRequest(token, agreements);
        return data;
    };

    const logout = async () => {
        try {
            await logoutRequest();
        } catch (err) {
            console.warn("Logout request failed", err);
        }
        setToken(null);
        setUser(null);
    };

    // Changed: auto logout after 2 minutes of inactivity
    const logoutRef = useRef(logout);
    logoutRef.current = logout;

    useEffect(() => {
        if (!token) return;

        let timeout;
        const reset = () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => logoutRef.current(), 30 * 60 * 1000);
        };

        const events = ["mousemove", "keydown", "click", "scroll", "touchstart"];
        events.forEach((e) => window.addEventListener(e, reset));
        reset();

        return () => {
            clearTimeout(timeout);
            events.forEach((e) => window.removeEventListener(e, reset));
        };
    }, [token]);

    const value = useMemo(
        () => ({ token, user, isAuthenticated: !!token, login, register, logout, acceptPolicies, loading, error }),
        [token, user, loading, error]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within AuthProvider");
    }
    return context;
};
