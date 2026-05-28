import { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext(null);

const ACCENT_KEY = "accentColor";
const ACCENTS = ["blue", "purple", "green", "orange", "pink", "teal"];

export function ThemeProvider({ children }) {
    const [dark, setDark] = useState(() => localStorage.getItem("theme") === "dark");
    const [accent, setAccent] = useState(() => localStorage.getItem(ACCENT_KEY) || "blue");

    useEffect(() => {
        document.documentElement.classList.toggle("dark", dark);
        localStorage.setItem("theme", dark ? "dark" : "light");
    }, [dark]);

    // apply accent color as a CSS variable on the root
    useEffect(() => {
        document.documentElement.style.setProperty("--accent-color", accent);
        localStorage.setItem(ACCENT_KEY, accent);
    }, [accent]);

    const toggle = () => setDark((v) => !v);

    return (
        <ThemeContext.Provider value={{ dark, toggle, accent, setAccent, ACCENTS }}>
            {children}
        </ThemeContext.Provider>
    );
}

export const useTheme = () => useContext(ThemeContext);
