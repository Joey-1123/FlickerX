// Changed: route uses extracted controller instead of inline handler
import express from "express";
import upload from "../middleware/upload.js";
import { requireAuth } from "../middleware/authMiddleware.js";
import { chatRateLimit } from "../middleware/rateLimit.js";
import { handleUpload } from "../controllers/uploadController.js";

const router = express.Router();

router.post("/", requireAuth, chatRateLimit, upload.single("file"), handleUpload);

export default router;