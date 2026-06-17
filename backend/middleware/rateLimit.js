import rateLimit, { ipKeyGenerator } from "express-rate-limit";

// Changed: key on authenticated user ID instead of IP so one user's requests
// don't block others behind the same IP.
export const chatRateLimit = rateLimit({
    windowMs: 60 * 1000,
    max: 5,
    keyGenerator: (req) => req.user?.id ?? ipKeyGenerator(req),
    message: {
        error: "Too many requests. Please slow down."
    },
    standardHeaders: true,
    legacyHeaders: false,
});

export const authRateLimit = rateLimit({
    windowMs: 60 * 1000,
    max: 10,
    message: {
        error: "Too many requests. Please slow down."
    },
    standardHeaders: true,
    legacyHeaders: false,
});