import jwt from "jsonwebtoken";

const jwtSecret = process.env.JWT_SECRET;
const jwtAlgorithms = (process.env.JWT_ALGORITHM || "HS256").split(",");

if (!jwtSecret) {
    throw new Error("JWT_SECRET must be defined in the environment.");
}

export const requireAuth = (req, res, next) => {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
        return res.status(401).json({ error: "Authorization token missing." });
    }

    const [scheme, token] = authHeader.split(" ");
    if (scheme !== "Bearer" || !token) {
        return res.status(401).json({ error: "Invalid authorization header." });
    }

    try {
        const decoded = jwt.verify(token, jwtSecret, { algorithms: jwtAlgorithms });
        req.user = decoded;
        return next();
    } catch (err) {
        console.error("JWT verification failed:", err.message);
        return res.status(401).json({ error: "Invalid or expired token." });
    }
};

export const requireAdmin = (req, res, next) => {
    if (!req.user) {
        return res.status(401).json({ error: "Unauthorized." });
    }

    if (req.user.role !== "admin") {
        return res.status(403).json({ error: "Admin access required." });
    }

    return next();
};
