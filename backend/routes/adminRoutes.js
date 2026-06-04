import express from "express";
import { getAllUsers, deleteUser, changeUserRole } from "../controllers/adminController.js";
import { requireAuth, requireAdmin } from "../middleware/authMiddleware.js";

const router = express.Router();
router.get("/users", requireAuth, requireAdmin, getAllUsers);
router.delete("/users/:id", requireAuth, requireAdmin, deleteUser);
router.patch("/users/:id/role", requireAuth, requireAdmin, changeUserRole);

export default router;
