import express from "express";
import { login, register, getProfile, updateProfile, refreshToken, logout, deleteAccount, forgotPassword, resetPassword, acceptPolicies } from "../controllers/authController.js";
import { requireAuth } from "../middleware/authMiddleware.js";
import { authRateLimit } from "../middleware/rateLimit.js";

const router = express.Router();
router.post("/register", authRateLimit, register);
router.post("/login", authRateLimit, login);
router.post("/refresh", refreshToken);
router.post("/logout", logout);
router.get("/me", requireAuth, getProfile);
router.put("/me", requireAuth, updateProfile);
router.delete("/me", requireAuth, deleteAccount);
router.post("/forgot-password", authRateLimit, forgotPassword);
router.post("/reset-password", authRateLimit, resetPassword);
router.post("/accept-policies", requireAuth, acceptPolicies);

export default router;
