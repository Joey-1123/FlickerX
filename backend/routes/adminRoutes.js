import express from "express";
import { getAllUsers } from "../controllers/adminController.js";
import { requireAuth, requireAdmin } from "../middleware/authMiddleware.js";

const router = express.Router();
router.get("/users", requireAuth, requireAdmin, getAllUsers);

export default router;
