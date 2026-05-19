import rateLimit from "express-rate-limit";

export const chatRateLimit = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 5, 
    message: {
        error: "Too many requests. Please slow down."
    },
    standardHeaders: true,
    legacyHeaders: false,
});