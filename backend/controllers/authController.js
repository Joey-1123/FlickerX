import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { findUserByEmail, createUser, updateUser, findUserByRefreshToken } from "../services/userService.js";
import { generateRefreshToken } from "../services/tokenService.js";

const jwtSecret = process.env.JWT_SECRET;
const accessTokenExpiresIn = "15m";
const refreshTokenExpiresIn = 60 * 60 * 24 * 30; // 30 days in seconds
const saltRounds = Number(process.env.BCRYPT_SALT_ROUNDS) || 12;

if (!jwtSecret) {
    throw new Error("JWT_SECRET must be defined in the environment.");
}

const normalizeEmail = (email) => String(email).trim().toLowerCase();

const validateEmail = (email) => {
    const normalized = normalizeEmail(email);
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalized);
};

const buildSafeUser = (user) => ({
    id: user.id,
    email: user.email,
    name: user.name,
    role: user.role || "user",
});

export const getProfile = async (req, res) => {
    if (!req.user) {
        return res.status(401).json({ error: "Unauthorized" });
    }
    return res.json({ user: req.user });
};

export const register = async (req, res) => {
    const { email, password, name } = req.body;
    const normalizedEmail = normalizeEmail(email || "");

    if (!normalizedEmail || !password) {
        return res.status(400).json({ error: "Email and password are required." });
    }

    if (!validateEmail(normalizedEmail)) {
        return res.status(400).json({ error: "Please provide a valid email address." });
    }

    if (password.length < 8) {
        return res.status(400).json({ error: "Password must be at least 8 characters." });
    }

    try {
        const existingUser = await findUserByEmail(normalizedEmail);
        if (existingUser) {
            return res.status(409).json({ error: "A user with that email already exists." });
        }

        const passwordHash = await bcrypt.hash(password, saltRounds);
        const newUser = await createUser({
            email: normalizedEmail,
            name: name?.trim() || normalizedEmail.split("@")[0],
            passwordHash,
        });

        const token = jwt.sign(buildSafeUser(newUser), jwtSecret, { expiresIn: accessTokenExpiresIn });
        const refreshToken = generateRefreshToken();
        await updateUser(newUser.id, { refreshToken });

        res.cookie("refreshToken", refreshToken, {
            httpOnly: true,
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
            maxAge: refreshTokenExpiresIn * 1000,
        });

        return res.status(201).json({ token, user: buildSafeUser(newUser) });
    } catch (err) {
        console.error("Register failed:", err);
        return res.status(500).json({ error: "Unable to create user." });
    }
};

export const login = async (req, res) => {
    const { email, password } = req.body;
    const normalizedEmail = normalizeEmail(email || "");

    if (!normalizedEmail || !password) {
        return res.status(400).json({ error: "Email and password are required." });
    }

    try {
        const user = await findUserByEmail(normalizedEmail);
        if (!user) {
            return res.status(401).json({ error: "Invalid email or password." });
        }

        const isMatch = await bcrypt.compare(password, user.passwordHash);
        if (!isMatch) {
            return res.status(401).json({ error: "Invalid email or password." });
        }

        const token = jwt.sign(buildSafeUser(user), jwtSecret, { expiresIn: accessTokenExpiresIn });
        const refreshToken = generateRefreshToken();
        await updateUser(user.id, { refreshToken });

        res.cookie("refreshToken", refreshToken, {
            httpOnly: true,
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
            maxAge: refreshTokenExpiresIn * 1000,
        });

        return res.json({ token, user: buildSafeUser(user) });
    } catch (err) {
        console.error("Login failed:", err);
        return res.status(500).json({ error: "Unable to authenticate user." });
    }
};

export const refreshToken = async (req, res) => {
    const { refreshToken } = req.cookies || {};

    if (!refreshToken) {
        return res.status(401).json({ error: "Refresh token missing." });
    }

    try {
        const user = await findUserByRefreshToken(refreshToken);
        if (!user) {
            return res.status(401).json({ error: "Refresh token invalid." });
        }

        const token = jwt.sign(buildSafeUser(user), jwtSecret, { expiresIn: accessTokenExpiresIn });
        const newRefreshToken = generateRefreshToken();
        await updateUser(user.id, { refreshToken: newRefreshToken });

        res.cookie("refreshToken", newRefreshToken, {
            httpOnly: true,
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
            maxAge: refreshTokenExpiresIn * 1000,
        });

        return res.json({ token, user: buildSafeUser(user) });
    } catch (err) {
        console.error("Refresh failed:", err);
        return res.status(500).json({ error: "Unable to refresh token." });
    }
};

export const logout = async (req, res) => {
    const { refreshToken } = req.cookies || {};

    if (refreshToken) {
        const user = await findUserByRefreshToken(refreshToken);
        if (user) {
            await updateUser(user.id, { refreshToken: null });
        }
    }

    res.clearCookie("refreshToken", {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
    });

    return res.status(204).send();
};
