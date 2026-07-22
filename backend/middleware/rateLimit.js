import rateLimit, { ipKeyGenerator } from "express-rate-limit";

const chatMax = Number(process.env.RATE_LIMIT_CHAT_MAX) || 5;
const authMax = Number(process.env.RATE_LIMIT_AUTH_MAX) || 10;
const windowMs = (Number(process.env.RATE_LIMIT_WINDOW_MS) || 60) * 1000;

export const chatRateLimit = rateLimit({
    windowMs,
    max: chatMax,
    keyGenerator: (req) => req.user?.id ?? ipKeyGenerator(req),
    message: {
        error: "Too many requests. Please slow down."
    },
    standardHeaders: true,
    legacyHeaders: false,
});

export const authRateLimit = rateLimit({
    windowMs,
    max: authMax,
    message: {
        error: "Too many requests. Please slow down."
    },
    standardHeaders: true,
    legacyHeaders: false,
});