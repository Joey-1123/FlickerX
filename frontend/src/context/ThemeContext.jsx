import { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext(null);

const ACCENT_KEY = "accentColor";
export const ACCENT_COLORS = {
    blue: { hex: "#3b82f6", ring: "ring-blue-500", bg: "bg-blue-600", hover: "hover:bg-blue-700" },
    purple: { hex: "#8b5cf6", ring: "ring-purple-500", bg: "bg-purple-600", hover: "hover:bg-purple-700" },
    green: { hex: "#22c55e", ring: "ring-green-500", bg: "bg-green-600", hover: "hover:bg-green-700" },
    orange: { hex: "#f97316", ring: "ring-orange-500", bg: "bg-orange-600", hover: "hover:bg-orange-700" },
    pink: { hex: "#ec4899", ring: "ring-pink-500", bg: "bg-pink-600", hover: "hover:bg-pink-700" },
    teal: { hex: "#14b8a6", ring: "ring-teal-500", bg: "bg-teal-600", hover: "hover:bg-teal-700" },
};
const ACCENTS = Object.keys(ACCENT_COLORS);

export function ThemeProvider({ children }) {
    const [dark, setDark] = useState(() => localStorage.getItem("theme") === "dark");
    const [accent, setAccent] = useState(() => localStorage.getItem(ACCENT_KEY) || "blue");

    useEffect(() => {
        document.documentElement.classList.toggle("dark", dark);
        localStorage.setItem("theme", dark ? "dark" : "light");
    }, [dark]);

    useEffect(() => {
        const color = ACCENT_COLORS[accent]?.hex || "#3b82f6";
        document.documentElement.style.setProperty("--accent-hex", color);
        localStorage.setItem(ACCENT_KEY, accent);
    }, [accent]);

    const toggle = () => setDark((v) => !v);

    return (
        <ThemeContext.Provider value={{ dark, toggle, accent, setAccent, ACCENTS, colors: ACCENT_COLORS }}>
            {children}
        </ThemeContext.Provider>
    );
}

export const useTheme = () => {
    const ctx = useContext(ThemeContext);
    if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
    return ctx;
};
