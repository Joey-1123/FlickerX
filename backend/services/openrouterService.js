import axios from "axios";

// Changed: accept `model` parameter so frontend can pick the AI model.
// If a `fileUrl` is provided, the last user message becomes multi-part.
const buildPayload = (messages, fileUrl, model, stream) => {
  const msgs = structuredClone(messages);
  if (fileUrl && msgs.length > 0) {
    const last = msgs[msgs.length - 1];
    if (last.role === "user") {
      last.content = [
        { type: "text", text: typeof last.content === "string" ? last.content : "Describe this image" },
        { type: "image_url", image_url: { url: fileUrl } },
      ];
    }
  }
  return { model: model || "qwen/qwen-2.5-72b-instruct", messages: msgs, ...(stream ? { stream: true } : {}) };
};

// Accept optional userApiKey — use it if provided, otherwise fall back to app key
const headers = (userApiKey) => ({
  Authorization: `Bearer ${userApiKey || process.env.OPENROUTER_API_KEY}`,
  "Content-Type": "application/json",
});

// Changed: normalizes OpenRouter errors into user-friendly messages
const normalizeError = (err) => {
    const msg = err?.response?.data?.error?.message || err?.message || "";
    if (/image|vision|multimodal/i.test(msg) && !/timeout|network/i.test(msg)) {
        return new Error(`This model does not support image inputs. Select a vision-capable model (GPT-4o, Claude, Gemini) or remove the image.`);
    }
    return err;
};

export const getChatResponse = async (messages, fileUrl, model, userApiKey) => {
  const payload = buildPayload(messages, fileUrl, model, false);
  const maxAttempts = 3;
  let attempt = 0;

  while (attempt < maxAttempts) {
    try {
      const response = await axios.post(
        "https://openrouter.ai/api/v1/chat/completions",
        payload,
        { headers: headers(userApiKey), timeout: 10000 }
      );

      const choices = response?.data?.choices;
      if (!choices || !Array.isArray(choices) || choices.length === 0) {
        throw new Error("Unexpected OpenRouter response shape");
      }

      return choices[0]?.message?.content;
    } catch (err) {
      attempt += 1;
      const isLast = attempt >= maxAttempts;
      console.warn(`OpenRouter attempt ${attempt} failed:`, err?.message || err);
      if (isLast) throw normalizeError(err);
      await new Promise((r) => setTimeout(r, 200 * Math.pow(2, attempt)));
    }
  }
};

// Changed: streaming support — calls `onChunk(rawJson)` for each SSE delta
export const streamChat = async (messages, fileUrl, model, onChunk, userApiKey) => {
  const payload = buildPayload(messages, fileUrl, model, true);

  const maxAttempts = 3;
  let attempt = 0;

  while (attempt < maxAttempts) {
    try {
      const response = await axios.post(
        "https://openrouter.ai/api/v1/chat/completions",
        payload,
        { headers: headers(userApiKey), responseType: "stream", timeout: 30000 }
      );

      return new Promise((resolve, reject) => {
        let buffer = "";

        response.data.on("data", (chunk) => {
          buffer += chunk.toString();
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith("data: ")) continue;
            const data = trimmed.slice(6);
            if (data === "[DONE]") continue;
            try {
              onChunk(JSON.parse(data));
            }         catch (e) { console.warn("Malformed SSE chunk:", e.message, data); }
          }
        });

        response.data.on("end", resolve);
        response.data.on("error", (err) => reject(normalizeError(err)));
      });
    } catch (err) {
      attempt += 1;
      const isLast = attempt >= maxAttempts;

      // try to read the error body from the stream response
      let detail = err?.message;
      try {
        if (err?.response?.data) {
          const body = await new Promise((r) => {
            let b = "";
            err.response.data.on("data", (c) => { b += c.toString(); });
            err.response.data.on("end", () => r(b));
            err.response.data.on("error", () => r(""));
          });
          if (body) detail = body;
        }
      } catch (_) { /* ignore */ }

      console.warn(`OpenRouter stream attempt ${attempt} failed:`, detail);
      if (isLast) throw normalizeError(Object.assign(err, { message: detail }));
      await new Promise((r) => setTimeout(r, 200 * Math.pow(2, attempt)));
    }
  }
};
