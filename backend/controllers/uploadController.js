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

    } catch (err) {
        return res.status(500).json({ error: "Upload failed" });
    }
};
