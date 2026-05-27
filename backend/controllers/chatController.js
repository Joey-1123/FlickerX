// Changed: accept model from frontend; added streaming endpoint
import { getChatResponse, streamChat } from "../services/openrouterService.js";

export const handleChat = async (req, res) => {
    try {
        const { messages, message, fileUrl, model, userApiKey } = req.body;

        const chatMessages = Array.isArray(messages) && messages.length > 0
            ? structuredClone(messages)
            : [{ role: "user", content: message || "" }];

        const reply = await getChatResponse(chatMessages, fileUrl, model, userApiKey);

        if (!reply) {
            return res.status(502).json({ error: "Upstream service error" });
        }

        res.json({ reply });
    } catch (err) {
        // Changed: return the actual error message so the user knows why it failed
        const message = err?.message || "Chat failed";
        console.error("Chat failed:", message);
        res.status(500).json({ error: message });
    }
};

export const handleChatStream = async (req, res) => {
    try {
        const { messages, message, fileUrl, model, userApiKey } = req.body;

        const chatMessages = Array.isArray(messages) && messages.length > 0
            ? structuredClone(messages)
            : [{ role: "user", content: message || "" }];

        res.setHeader("Content-Type", "text/event-stream");
        res.setHeader("Cache-Control", "no-cache");
        res.setHeader("Connection", "keep-alive");
        res.flushHeaders();

        let fullContent = "";

        await streamChat(chatMessages, fileUrl, model, (delta) => {
            const content = delta?.choices?.[0]?.delta?.content || "";
            if (content) {
                fullContent += content;
                res.write(`data: ${JSON.stringify({ content })}\n\n`);
            }
        }, userApiKey);

        res.write(`data: ${JSON.stringify({ done: true, fullContent })}\n\n`);
        res.end();
    } catch (err) {
        const message = err?.message || "Stream chat failed";
        console.error("Stream chat failed:", message);
        if (!res.headersSent) {
            res.status(500).json({ error: message });
        } else {
            res.write(`data: ${JSON.stringify({ error: message })}\n\n`);
            res.end();
        }
    }
};
