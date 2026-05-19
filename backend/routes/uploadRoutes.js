import express from "express";
import upload from "../middleware/upload.js";
import cloudinary from "../config/cloudinary.js";
import { requireAuth } from "../middleware/authMiddleware.js";
import { chatRateLimit } from "../middleware/rateLimit.js";

const router = express.Router();

// Changed: Protect upload endpoint with auth + rate limiting. Multer already
// enforces size/type limits in `upload` middleware.
router.post("/", requireAuth, chatRateLimit, upload.single("file"), async (req, res) => {
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

        // 3. Send response FIRST (don't wait for deletes)
        res.json({ url: imageUrl });

        // 4. Attempt to delete the uploaded image asynchronously. We keep
        // this behavior but log failures; consider a cleanup job for reliability.
        setTimeout(async () => {
            try {
                if (publicId) {
                    await cloudinary.uploader.destroy(publicId);
                }
            } catch (err) {
                console.error("Cloudinary delete error:", err);
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