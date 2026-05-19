// Changed: delegate OpenRouter interaction to the centralized service
// `getChatResponse` which implements retries and response validation.
import { getChatResponse } from "../services/openrouterService.js";

export const handleChat = async (req, res) => {
    try {
        const { message, fileUrl } = req.body;

        // Use the service which constructs messages consistently and retries
        const reply = await getChatResponse(message, fileUrl);

        if (!reply) {
            // Upstream did not return a reply in the expected shape
            return res.status(502).json({ error: "Upstream service error" });
        }

        res.json({ reply });
    } catch (err) {
        console.error("Chat failed:", err);
        res.status(500).json({ error: "Chat failed" });
    }
};