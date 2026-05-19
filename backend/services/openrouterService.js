import axios from "axios";

// Changed: add basic retry/backoff and response-shape validation.
// `getChatResponse` constructs messages consistently, attempts retries on
// transient errors, and returns the validated `message.content` string.
export const getChatResponse = async (message, imageUrl) => {
  const messages = [
    {
      role: "user",
      content: imageUrl
        ? [
            { type: "text", text: message || "Describe this image" },
            { type: "image_url", image_url: { url: imageUrl } },
          ]
        : [{ type: "text", text: message }],
    },
  ];

  const payload = {
    model: "openai/gpt-4o-mini",
    messages,
  };

  const maxAttempts = 3;
  let attempt = 0;

  while (attempt < maxAttempts) {
    try {
      const response = await axios.post(
        "https://openrouter.ai/api/v1/chat/completions",
        payload,
        {
          headers: {
            Authorization: `Bearer ${process.env.OPENROUTER_API_KEY}`,
            "Content-Type": "application/json",
          },
          timeout: 10000,
        }
      );

      // Validate structure before accessing nested fields
      const choices = response?.data?.choices;
      if (!choices || !Array.isArray(choices) || choices.length === 0) {
        throw new Error("Unexpected OpenRouter response shape");
      }

      const content = choices[0]?.message?.content;
      return content;
    } catch (err) {
      attempt += 1;
      const isLast = attempt >= maxAttempts;
      console.warn(`OpenRouter attempt ${attempt} failed:`, err?.message || err);
      if (isLast) throw err;
      // Exponential backoff
      await new Promise((r) => setTimeout(r, 200 * Math.pow(2, attempt)));
    }
  }
};

