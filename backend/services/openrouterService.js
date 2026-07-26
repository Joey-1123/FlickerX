import axios from "axios";

const OPENROUTER_BASE = process.env.OPENROUTER_BASE || "https://openrouter.ai/api/v1/chat/completions";
const HTTP_TIMEOUT = Number(process.env.OPENROUTER_TIMEOUT_MS) || 10000;
const STREAM_TIMEOUT = Number(process.env.OPENROUTER_STREAM_TIMEOUT_MS) || 30000;

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
  return { model: model || "google/gemma-4-31b-it:free", messages: msgs, ...(stream ? { stream: true } : {}) };
};

// Accept optional userApiKey — use it if provided, otherwise fall back to app key
const headers = (userApiKey) => ({
  Authorization: `Bearer ${userApiKey || process.env.OPENROUTER_API_KEY}`,
  "Content-Type": "application/json",
});

// Fallback order for free models when one is rate-limited
const FREE_FALLBACKS = [
  "google/gemma-4-31b-it:free",
  "nvidia/nemotron-3-super-120b-a12b:free",
  "poolside/laguna-m.1:free",
  "inclusionai/ling-3.0-flash:free",
  "openai/gpt-oss-20b:free",
];

// Extract retry-after seconds from a 429 error response
const getRetryAfter = (err) => {
  try {
    const meta = err?.response?.data?.error?.metadata;
    return meta?.retry_after_seconds || meta?.retry_after_seconds_raw || null;
  } catch {
    return null;
  }
};

// Read error body from a stream/JSON response
const readErrorBody = async (err) => {
  try {
    if (!err?.response?.data) return null;
    if (typeof err.response.data === "string") return err.response.data;
    if (err.response.data instanceof Buffer) return err.response.data.toString();
    if (typeof err.response.data === "object" && !Array.isArray(err.response.data)) {
      return JSON.stringify(err.response.data);
    }
    // likely a stream — consume it
    return await new Promise((r) => {
      let b = "";
      err.response.data.on("data", (c) => { b += c.toString(); });
      err.response.data.on("end", () => r(b));
      err.response.data.on("error", () => r(""));
    });
  } catch { return null; }
};

const normalizeError = (err) => {
    const body = err._body;
    const msg = body || err?.response?.data?.error?.message || err?.message || "";
    if (err?.response?.status === 401) {
        return new Error("Invalid API key. Check your OpenRouter key or set one with /key set <your-key>.");
    }
    if (err?.response?.status === 404) {
        return new Error("Model not found — it may have been removed or renamed.");
    }
    if (/image|vision|multimodal/i.test(msg) && !/timeout|network/i.test(msg)) {
        return new Error(`This model does not support image inputs. Select a vision-capable model (GPT-4o, Claude, Gemini) or remove the image.`);
    }
    if (err?.response?.status === 429) {
      const wait = getRetryAfter(err);
      const hint = wait ? ` Rate limit resets in ${wait}s.` : "";
      return new Error(`Too many requests — the free tier is busy.${hint} Try again shortly, or use /key set <your-key> for higher limits.`);
    }
    return err;
};

// Try each fallback model in order until one works (for non-rate-limit errors)
const tryWithFallback = async (payload, headers, timeout, onChunk, userApiKey) => {
  const models = FREE_FALLBACKS.includes(payload.model)
    ? [payload.model, ...FREE_FALLBACKS.filter((m) => m !== payload.model)]
    : [payload.model];

  // For rate limits, retry the original model with proper backoff
  const rateLimitRetries = 5;
  let lastError;

  // First, try original model with long backoff for rate limits
  const originalModel = payload.model;
  for (let attempt = 0; attempt < rateLimitRetries; attempt++) {
    try {
      const response = await axios.post(
        OPENROUTER_BASE,
        { ...payload, model: originalModel },
{ headers, ...(onChunk ? { responseType: "stream", timeout: STREAM_TIMEOUT } : { timeout }) }
      );

      if (onChunk) {
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
              try { onChunk(JSON.parse(data)); }
              catch (e) { console.warn("Malformed SSE chunk:", e.message, data); }
            }
          });
          response.data.on("end", resolve);
          response.data.on("error", (err) => reject(normalizeError(err)));
        });
      }

      const choices = response?.data?.choices;
      if (!choices || !Array.isArray(choices) || choices.length === 0) {
        throw new Error("Unexpected OpenRouter response shape");
      }
      return choices[0]?.message?.content;
    } catch (err) {
      lastError = err;
      const body = await readErrorBody(err);
      if (body) err._body = body;

      if (err?.response?.status === 429) {
        const wait = Math.max(getRetryAfter(err) || 5, 5);
        console.warn(`Rate limited on ${originalModel}, attempt ${attempt + 1}/${rateLimitRetries}, waiting ${wait}s...`);
        if (attempt < rateLimitRetries - 1) {
          await new Promise((r) => setTimeout(r, wait * 1000));
          continue;
        }
        console.warn("Exhausted rate-limit retries, trying fallback models...");
        for (const fb of models.filter((m) => m !== originalModel)) {
          try {
            const fbResponse = await axios.post(
              OPENROUTER_BASE,
              { ...payload, model: fb },
              { headers, ...(onChunk ? { responseType: "stream", timeout: STREAM_TIMEOUT } : { timeout }) }
            );

            if (onChunk) {
              return new Promise((resolve, reject) => {
                let buffer = "";
                fbResponse.data.on("data", (chunk) => {
                  buffer += chunk.toString();
                  const lines = buffer.split("\n");
                  buffer = lines.pop() || "";
                  for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed || !trimmed.startsWith("data: ")) continue;
                    const data = trimmed.slice(6);
                    if (data === "[DONE]") continue;
                    try { onChunk(JSON.parse(data)); }
                    catch (e) { console.warn("Malformed SSE chunk:", e.message, data); }
                  }
                });
                fbResponse.data.on("end", resolve);
                fbResponse.data.on("error", (err) => reject(normalizeError(err)));
              });
            }

            const choices = fbResponse?.data?.choices;
            if (choices?.[0]?.message?.content) return choices[0].message.content;
          } catch { /* fallback failed too, continue */ }
        }
        throw normalizeError(lastError);
      }

      // non-rate-limit error — try fallbacks
      if (!onChunk) {
        for (const fb of models.filter((m) => m !== originalModel)) {
          try {
            const fbResponse = await axios.post(
              OPENROUTER_BASE,
              { ...payload, model: fb },
              { headers, timeout }
            );
            const choices = fbResponse?.data?.choices;
            if (choices?.[0]?.message?.content) return choices[0].message.content;
          } catch { /* skip */ }
        }
      }

      throw normalizeError(err);
    }
  }
};

export const getChatResponse = async (messages, fileUrl, model, userApiKey) => {
  const payload = buildPayload(messages, fileUrl, model, false);
  return tryWithFallback(payload, headers(userApiKey), HTTP_TIMEOUT, null, userApiKey);
};

export const streamChat = async (messages, fileUrl, model, onChunk, userApiKey) => {
  const payload = buildPayload(messages, fileUrl, model, true);
  return tryWithFallback(payload, headers(userApiKey), STREAM_TIMEOUT, onChunk, userApiKey);
};
