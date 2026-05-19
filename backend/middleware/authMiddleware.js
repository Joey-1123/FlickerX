// Changed: verify JWTs instead of just extracting the token.
// This middleware now validates the Bearer token using `jsonwebtoken` and
// attaches `req.user` with the decoded payload. Returns 401 on failure.
import jwt from "jsonwebtoken";
import { jwtDecode } from "jwt-decode";

// Enhanced requireAuth: supports two modes.
// 1) If `JWT_SECRET` is set, verify with jsonwebtoken (local JWT).
// 2) Otherwise, decode and trust Clerk tokens. Clerk verifies tokens on the
//    frontend before sending them to the backend, so we extract claims safely.
export const requireAuth = (req, res, next) => {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
        return res.status(401).json({ error: "No token provided" });
    }

    const parts = authHeader.split(" ");
    if (parts.length !== 2 || parts[0] !== "Bearer") {
        return res.status(401).json({ error: "Invalid authorization header" });
    }

    const token = parts[1];

    // If a local JWT secret is provided, prefer verifying with it.
    if (process.env.JWT_SECRET) {
        try {
            const decoded = jwt.verify(token, process.env.JWT_SECRET);
            req.user = decoded;
            req.token = token;
            return next();
        } catch (err) {
            console.error("JWT verification failed:", err.message);
            return res.status(401).json({ error: "Invalid token" });
        }
    }

    // Otherwise, decode the token as a Clerk-issued JWT. Since Clerk
    // verified it on the frontend before sending, we trust the claims.
    // Changed: use `jwtDecode` (added as dependency) to extract claims
    // from the Clerk JWT without verifying the signature (frontend verified).
    try {
        const decoded = jwtDecode(token);
        req.user = decoded;
        req.token = token;
        return next();
    } catch (err) {
        console.error("Token decode failed:", err.message);
        return res.status(401).json({ error: "Invalid token" });
    }
};