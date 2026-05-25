import "dotenv/config";
import helmet from "helmet";
import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import chatRoutes from "./routes/chatRoutes.js";
import authRoutes from "./routes/authRoutes.js";
import uploadRoutes from "./routes/uploadRoutes.js";
import adminRoutes from "./routes/adminRoutes.js";

const app = express();

// Configure CORS to allow requests from the frontend running on localhost:5173, enabling credentials for cookie handling.
// Changed: read allowed origin from env and include Authorization in allowed headers
app.use(
  cors({
    origin: process.env.FRONTEND_ORIGIN || "http://localhost:5173",
    credentials: true,
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization", "Cookie"],
  })
);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

app.use("/api/auth", authRoutes);
app.use("/api/admin", adminRoutes);
app.use("/api/chat", chatRoutes);
app.use("/api/upload", uploadRoutes);

app.use((req, res) => {
  res.status(404).json({ error: "Route not found." });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});