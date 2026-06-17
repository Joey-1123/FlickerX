export const MODELS = {
    vision: [
        { id: "nex-agi/nex-n2-pro:free", name: "Nex N2 Pro" },
        { id: "google/gemma-4-31b-it:free", name: "Gemma 4 31B" },
        { id: "openai/gpt-4o", name: "GPT-4o", premium: true },
        { id: "anthropic/claude-3.5-sonnet", name: "Claude 3.5 Sonnet", premium: true },
    ],
    coding: [
        { id: "qwen/qwen3-coder:free", name: "Qwen3 Coder" },
        { id: "nvidia/nemotron-3-super-120b-a12b:free", name: "Nemotron 3 Super" },
        { id: "poolside/laguna-m.1:free", name: "Laguna M.1" },
    ],
    textonly: [
        { id: "meta-llama/llama-3.3-70b-instruct:free", name: "Llama 3.3 70B" },
        { id: "openai/gpt-oss-120b:free", name: "GPT-OSS 120B" },
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
