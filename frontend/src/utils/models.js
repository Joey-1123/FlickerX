export const MODELS = {
    vision: [
        { id: "qwen/qwen-2.5-vl-72b-instruct", name: "Qwen 2.5 VL 72B" },
        { id: "openai/gpt-4o", name: "GPT-4o", premium: true },
        { id: "anthropic/claude-3.5-sonnet", name: "Claude 3.5 Sonnet", premium: true },
        { id: "google/gemini-2.0-flash-001", name: "Gemini 2.0 Flash", premium: true },
    ],
    coding: [
        { id: "moonshotai/kimi-k2", name: "Kimi K2" },
        { id: "deepseek/deepseek-chat", name: "DeepSeek V3" },
        { id: "qwen/qwen-2.5-72b-instruct", name: "Qwen 2.5 72B" },
    ],
    textonly: [
        { id: "meta-llama/llama-3.3-70b-instruct", name: "Llama 3.3 70B" },
        { id: "google/gemma-2-27b-it", name: "Gemma 2 27B" },
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
