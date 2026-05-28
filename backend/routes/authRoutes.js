import express from "express";
import { login, register, getProfile, updateProfile, refreshToken, logout } from "../controllers/authController.js";
import { requireAuth } from "../middleware/authMiddleware.js";

const router = express.Router();
router.post("/register", register);
router.post("/login", login);
router.post("/refresh", refreshToken);
router.post("/logout", logout);
router.get("/me", requireAuth, getProfile);
router.put("/me", requireAuth, updateProfile);

export default router;
