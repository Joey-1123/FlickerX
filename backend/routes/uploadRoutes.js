import express from "express";
import upload from "../middleware/upload.js";
import cloudinary from "../config/cloudinary.js";

const router = express.Router();

// Route to handle file uploads
router.post("/", upload.single("file"), async (req, res) => {
    try {
        const file = req.file;

        if (!file) {
            return res.status(400).json({ error: "No file uploaded" });
        }

        // 1. Upload to Cloudinary
        const result = await new Promise((resolve, reject) => {
            const stream = cloudinary.uploader.upload_stream(
                { resource_type: "auto" },
                (error, result) => {
                    if (error) reject(error);
                    else resolve(result);
                }
            );

            stream.end(file.buffer);
        });

        const imageUrl = result.secure_url;
        const publicId = result.public_id; // ⭐ IMPORTANT

        // 2. (OPTIONAL) Use the image (AI, processing, etc.)
        // const aiResponse = await someAIfunction(imageUrl);

        // 3. DELETE IMAGE 🧨
        // 4. Send response FIRST
        res.json({
            url: imageUrl,
        });

        // 5. Then delete after delay
        setTimeout(async () => {
            try {
                await cloudinary.uploader.destroy(publicId);
            } catch (err) {
                console.error("Delete error:", err);
            }
        }, 5000);

    } catch (err) {
        res.status(500).json({
            error: err.message || "Upload failed",
            details: err
        });
    }
});

export default router;