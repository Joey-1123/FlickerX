import { getChatResponse } from "../services/openrouterService.js";

export const handleChat = async (req, res) => {
    try {
        const { message, fileUrl } = req.body;

        let content;

        if (fileUrl) {
            content = [
                {
                    type: "text",
                    text: message || "Describe this image",
                },
                {
                    type: "image_url",
                    image_url: {
                        url: fileUrl,
                    },
                },
            ];
        } else {
            content = message;
        }

        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
                Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                model: "openai/gpt-4o-mini",
                messages: [
                    {
                        role: "user",
                        content,
                    },
                ],
            }),
        });

        const data = await response.json();

        res.json({
            reply: data.choices[0].message.content,
        });
    } catch (err) {
        res.status(500).json({ error: "Chat failed" });
    }
};