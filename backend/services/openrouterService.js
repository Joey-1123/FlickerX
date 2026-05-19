import axios from "axios";

// This service interacts with the OpenRouter API to get chat responses based on user messages and optional image URLs.
export const getChatResponse = async (message, imageUrl) => {
  const messages = [
    {
      role: "user",
      content: imageUrl
        ? [
          { type: "text", text: message || "Describe this image" },
          { type: "image_url", image_url: { url: imageUrl } }
        ]
        : [{ type: "text", text: message }]
    }
  ];

  // Make a POST request to the OpenRouter API with the constructed messages and necessary headers.
  const response = await axios.post(
    "https://openrouter.ai/api/v1/chat/completions",
    {
      model: "openai/gpt-4o-mini",
      messages,
    },
    {
      headers: {
        Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
        "Content-Type": "application/json"
      }
    }
  );

  return response.data.choices[0].message.content;
};

