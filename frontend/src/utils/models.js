export const MODELS = {
    vision: [
        { id: "meta-llama/llama-4-maverick:free", name: "Llama 4 Maverick" },
        { id: "openai/gpt-4o", name: "GPT-4o", premium: true },
        { id: "anthropic/claude-3.5-sonnet", name: "Claude 3.5 Sonnet", premium: true },
        { id: "google/gemini-2.0-flash-001", name: "Gemini 2.0 Flash", premium: true },
    ],
    coding: [
        { id: "deepseek/deepseek-chat-v3-0324:free", name: "DeepSeek V3" },
        { id: "qwen/qwen3-coder:free", name: "Qwen3 Coder" },
    ],
    textonly: [
        { id: "meta-llama/llama-3.3-70b-instruct:free", name: "Llama 3.3 70B" },
        { id: "google/gemma-3-27b-it:free", name: "Gemma 3 27B" },
    ],
};

export const ALL_MODELS = Object.values(MODELS).flat();
export const PREMIUM_MODEL_IDS = new Set(ALL_MODELS.filter((m) => m.premium).map((m) => m.id));
export const VISION_MODELS = new Set(MODELS.vision.map((m) => m.id));

export const SECTION_LABELS = {
    vision: "Vision (image support)",
    coding: "Coding",
    textonly: "Text Only",
};
