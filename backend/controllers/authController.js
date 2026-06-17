// Changed: replaced manual validation with zod schemas
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { randomBytes } from "crypto";
import { z } from "zod";
import { findUserByEmail, findUserById, createUser, updateUser, findUserByRefreshToken, readUsers, deleteUserById, findUserByResetToken } from "../services/userService.js";
import { generateRefreshToken } from "../services/tokenService.js";

const jwtSecret = process.env.JWT_SECRET;
const accessTokenExpiresIn = "15m";
const refreshTokenExpiresIn = 60 * 60 * 24 * 30; // 30 days in seconds
const saltRounds = Number(process.env.BCRYPT_SALT_ROUNDS) || 12;

if (!jwtSecret) {
    throw new Error("JWT_SECRET must be defined in the environment.");
}

const normalizeEmail = (email) => String(email).trim().toLowerCase();

const registerSchema = z.object({
    email: z.string().email("Please provide a valid email address."),
    password: z.string().min(8, "Password must be at least 8 characters."),
    name: z.string().trim().optional(),
    agreeTerms: z.boolean().refine((v) => v === true, "You must accept the Terms of Service."),
    agreePrivacy: z.boolean().refine((v) => v === true, "You must accept the Privacy Policy."),
    agreeCookies: z.boolean().refine((v) => v === true, "You must accept the Cookies Policy."),
});

const loginSchema = z.object({
    email: z.string().email("Please provide a valid email address."),
    password: z.string().min(1, "Password is required."),
});

const buildSafeUser = (user) => ({
    id: user.id,
    email: user.email,
    name: user.name,
    role: user.role || "user",
    systemPrompt: user.systemPrompt || "",
});

// Changed: fetches full user from DB so systemPrompt is included
export const getProfile = async (req, res) => {
    if (!req.user) {
        return res.status(401).json({ error: "Unauthorized" });
    }
    try {
        const user = await findUserById(req.user.id);
        if (!user) {
            return res.status(404).json({ error: "User not found" });
        }
        return res.json({ user: buildSafeUser(user) });
    } catch (err) {
        console.error("Get profile failed:", err);
        return res.status(500).json({ error: "Unable to fetch profile." });
    }
};

// Changed: allows updating systemPrompt and other profile fields
const updateProfileSchema = z.object({
    name: z.string().trim().optional(),
    systemPrompt: z.string().optional(),
});

export const updateProfile = async (req, res) => {
    if (!req.user) {
        return res.status(401).json({ error: "Unauthorized" });
    }

    const parsed = updateProfileSchema.safeParse(req.body);
    if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0].message });
    }

    try {
        const updates = {};
        if (parsed.data.name !== undefined) updates.name = parsed.data.name;
        if (parsed.data.systemPrompt !== undefined) updates.systemPrompt = parsed.data.systemPrompt;

        const updated = await updateUser(req.user.id, updates);
        if (!updated) {
            return res.status(404).json({ error: "User not found" });
        }
        return res.json({ user: buildSafeUser(updated) });
    } catch (err) {
        console.error("Update profile failed:", err);
        return res.status(500).json({ error: "Unable to update profile." });
    }
};

export const register = async (req, res) => {
    const parsed = registerSchema.safeParse(req.body);
    if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0].message });
    }
    const { email, password, name, agreeTerms, agreePrivacy, agreeCookies } = parsed.data;
    const normalizedEmail = normalizeEmail(email);

    try {
        const existingUser = await findUserByEmail(normalizedEmail);
        if (existingUser) {
            return res.status(409).json({ error: "A user with that email already exists." });
        }

        const passwordHash = await bcrypt.hash(password, saltRounds);
        const newUser = await createUser({
            email: normalizedEmail,
            name: name || normalizedEmail.split("@")[0],
            passwordHash,
            agreeTerms,
            agreePrivacy,
            agreeCookies,
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
    const parsed = loginSchema.safeParse(req.body);
    if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0].message });
    }
    const { email, password } = parsed.data;
    const normalizedEmail = normalizeEmail(email);

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

        const needsAcceptance = !user.agreeTerms || !user.agreePrivacy || !user.agreeCookies;
        return res.json({ token, user: buildSafeUser(user), needsAcceptance });
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

export const deleteAccount = async (req, res) => {
    try {
        await deleteUserById(req.user.id);
        res.clearCookie("refreshToken", {
            httpOnly: true,
            sameSite: "lax",
            secure: process.env.NODE_ENV === "production",
        });
        return res.status(204).send();
    } catch (err) {
        console.error("Delete account failed:", err);
        return res.status(500).json({ error: "Unable to delete account." });
    }
};

export const forgotPassword = async (req, res) => {
    const emailSchema = z.object({ email: z.string().email() });
    const parsed = emailSchema.safeParse(req.body);
    if (!parsed.success) {
        return res.status(400).json({ error: "Please provide a valid email." });
    }

    try {
        const user = await findUserByEmail(parsed.data.email);
        if (!user) {
            return res.json({ message: "If that email exists, a reset link has been sent." });
        }

        const resetToken = randomBytes(32).toString("hex");
        const resetTokenExpiry = Date.now() + 3600000; // 1 hour

        await updateUser(user.id, { resetToken, resetTokenExpiry });

        const resetUrl = `${process.env.FRONTEND_ORIGIN || "http://localhost:5173"}/reset-password?token=${resetToken}`;
        console.log(`Password reset link for ${user.email}: ${resetUrl}`);

        return res.json({ message: "If that email exists, a reset link has been sent." });
    } catch (err) {
        console.error("Forgot password failed:", err);
        return res.status(500).json({ error: "Unable to process request." });
    }
};

export const resetPassword = async (req, res) => {
    const schema = z.object({
        token: z.string().min(1),
        password: z.string().min(8, "Password must be at least 8 characters."),
    });
    const parsed = schema.safeParse(req.body);
    if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0].message });
    }

    try {
        const user = await findUserByResetToken(parsed.data.token);
        if (!user) {
            return res.status(400).json({ error: "Invalid or expired reset token." });
        }

        const passwordHash = await bcrypt.hash(parsed.data.password, saltRounds);
        await updateUser(user.id, { passwordHash, resetToken: null, resetTokenExpiry: null });

        return res.json({ message: "Password has been reset successfully." });
    } catch (err) {
        console.error("Reset password failed:", err);
        return res.status(500).json({ error: "Unable to reset password." });
    }
};

const acceptSchema = z.object({
    agreeTerms: z.boolean().refine((v) => v === true, "Must accept Terms of Service."),
    agreePrivacy: z.boolean().refine((v) => v === true, "Must accept Privacy Policy."),
    agreeCookies: z.boolean().refine((v) => v === true, "Must accept Cookies Policy."),
});

export const acceptPolicies = async (req, res) => {
    if (!req.user) {
        return res.status(401).json({ error: "Unauthorized" });
    }

    const parsed = acceptSchema.safeParse(req.body);
    if (!parsed.success) {
        return res.status(400).json({ error: parsed.error.errors[0].message });
    }

    try {
        await updateUser(req.user.id, {
            ...parsed.data,
            agreedAt: new Date().toISOString(),
        });
        return res.json({ message: "Policies accepted." });
    } catch (err) {
        console.error("Accept policies failed:", err);
        return res.status(500).json({ error: "Unable to save acceptance." });
    }
};
