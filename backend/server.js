import dotenv from "dotenv";
dotenv.config();
import chatRoutes from "./routes/chatRoutes.js";
import express from "express";
import cors from "cors";
import uploadRoutes from "./routes/uploadRoutes.js";
// This is the main server file for the backend of the FlickerX application. It sets up the Express server, configures middleware, and defines routes for handling chat interactions and image uploads.

const app = express();

// Configure CORS to allow requests from the frontend running on localhost:5173, enabling credentials for cookie handling.
app.use(cors({
  origin: "http://localhost:5173",
  credentials: true
}));

app.use(express.json());

app.use("/api/chat", chatRoutes);

app.use("/api/upload", uploadRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});