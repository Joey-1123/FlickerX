import express from "express";
import { handleChat } from "../controllers/chatController.js";
import { requireAuth } from "../middleware/authMiddleware.js";
import { chatRateLimit } from "../middleware/rateLimit.js";

const router = express.Router();

// Test route to check if the API is working
router.get("/", (req, res) => {
  res.send(`
    <h1>FlickerX - Backend</h1>
    <p>API is running</p>
  `);
});

// Apply authentication and rate limiting middleware to the chat route
router.post("/", requireAuth, chatRateLimit, handleChat);

export default router;