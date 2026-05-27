// Changed: extracted upload logic from inline route handler to a controller
import cloudinary from "../config/cloudinary.js";

export const handleUpload = async (req, res) => {
    try {
        const file = req.file;

        if (!file) {
            return res.status(400).json({ error: "No file uploaded" });
        }

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
        const publicId = result.public_id;

        // Send response immediately
        res.json({ url: imageUrl });

        // Changed: kept async cleanup, but this is best-effort
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
        // Changed: don't leak internal error details to the client
        res.status(500).json({ error: "Upload failed" });
    }
};
