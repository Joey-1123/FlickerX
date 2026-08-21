# FlickerX Studio — User Guide

A practical guide to every feature in FlickerX. Open it, follow the steps, get work done.

---

## 1. Getting Started

### Install

**Linux / macOS** — auto-detects your GPU:

```bash
curl -sL https://raw.githubusercontent.com/joey/flickerx/main/install.sh | bash
```

Or clone and run the installer locally:

```bash
git clone https://github.com/Joey-1123/FlickerX.git && cd FlickerX
bash install.sh
```

To force a GPU backend or add image/video generation:

```bash
bash install.sh --gpu cuda       # NVIDIA, AMD (rocm), vulkan, intel, metal, or cpu
bash install.sh --with-torch     # installs torch + diffusers for image/video
```

**Windows** (PowerShell):

```powershell
.\install.ps1
.\install.ps1 -Gpu cuda -WithTorch
```

The installer creates a virtual environment at `~/.flickerx/venv/` and a `FlickerX` command in `~/.local/bin/`.

### First Launch

Run `FlickerX` from your terminal. The server starts at `http://127.0.0.1:8080`.

```bash
FlickerX                 # default port 8080
FlickerX --port 3000     # custom port
FlickerX --host 0.0.0.0  # accessible on your LAN
```

Open `http://127.0.0.1:8080` in your browser.

### Create Your Account

1. Click **Register** on the login screen.
2. Enter a username, email, and password (min 8 chars, upper + lower + digit + special).
3. Your account becomes the admin. You can create additional users and manage roles from the admin panel later.

---

## 2. Smart Chat

### Start a Conversation

1. Click **New Chat** in the sidebar.
2. Pick a model from the dropdown at the top of the chat panel. If no model is loaded, you'll be prompted to load one first.
3. Type your message and press Enter. Responses stream in real time as the model generates tokens.

### Select a Model

- Click the model name at the top of the chat to open the model selector.
- Only loaded models appear. If you haven't loaded one yet, go to the **Model Hub** to download and load a model first.
- You can switch models mid-conversation — the previous messages stay in context.

### Thread Management

- **Sidebar** shows all your chat threads, newest first.
- **Rename** a thread by clicking the three-dot menu next to its name.
- **Delete** a thread from the same menu.
- Each thread stores its full message history locally.

### OpenAI-Compatible API

FlickerX exposes a local OpenAI-compatible endpoint at `/v1/chat/completions`. Any tool that works with the OpenAI API (LangChain, curl, Python scripts) can point to `http://127.0.0.1:8080/v1`.

---

## 3. Model Hub

### Browse HuggingFace

1. Open the **Model Hub** from the sidebar.
2. Use the search bar to find models by name, task, or author.
3. Browse results — each card shows model size, format (GGUF, safetensors), and download size.

### Download a Model

1. Click **Download** on a model card.
2. Pick a quantization (Q4_K_M is a good balance of speed and quality for chat).
3. The download starts and shows a progress bar. Downloads are cached to `~/.flickerx/studio/models/`.

### Load and Unload

- **Load**: Click the **Load** button on a downloaded model. It becomes active for chat and inference.
- **Unload**: Click **Unload** to free memory. Only one model can be actively loaded at a time for GGUF models.
- Loading takes a few seconds — you'll see a spinner and a "Model loaded" confirmation.

---

## 4. Image Generation

### Prerequisites

You need `torch` and `diffusers` installed. If you didn't use `--with-torch` during install:

```bash
cd backend && uv pip install -e ".[torch]"
```

### Generate an Image

1. Open **Image Generation** from the sidebar.
2. Select or load a Stable Diffusion model (e.g., `stabilityai/stable-diffusion-2-1`).
3. Enter a text prompt describing what you want.
4. Adjust settings: image size, number of steps, guidance scale.
5. Click **Generate**. The image appears in the gallery below.

### Gallery

- All generated images are saved to a local gallery.
- Click any thumbnail to view it full-size.
- Delete images you don't want from the gallery view.

---

## 5. Video Generation

### Prerequisites

Same as image generation — requires `torch` and `diffusers`.

### Generate a Video

1. Open **Video Generation** from the sidebar.
2. Load a text-to-video model (uses `diffusers` pipelines under the hood).
3. Enter a text prompt.
4. Click **Generate**. Video generation is slow on consumer hardware — expect several minutes per clip.

### Gallery

- Generated clips appear in the video gallery.
- Play, download, or delete from the gallery view.

---

## 6. Audio

### Speech-to-Text (Whisper)

1. Open **Audio** from the sidebar.
2. Upload an audio file (MP3, WAV, M4A, etc.) or record directly.
3. Click **Transcribe**. FlickerX uses `faster-whisper` for fast local transcription.
4. The transcript appears below the audio player. Copy it with one click.

### Text-to-Speech

1. Enter or paste text.
2. Click **Generate Speech** to produce audio output.
3. Download the generated audio file.

---

## 7. Fine-Tuning

### Prepare a Dataset

1. Go to **Datasets** in the sidebar.
2. Download a dataset from HuggingFace by pasting its repo ID (e.g., `databricks/databricks-dolly-15k`).
3. Or upload your own data in a supported format.

### Start a LoRA Training Run

1. Open **Training** from the sidebar.
2. **Select a base model** — pick a downloaded HuggingFace model.
3. **Select a dataset** — choose from your downloaded datasets.
4. **Configure training**: learning rate, number of epochs, batch size, LoRA rank. Sensible defaults are pre-filled.
5. Click **Start Training**.

### Monitor Progress

- Training metrics stream in real time: loss, learning rate, step count.
- A progress bar shows estimated time remaining.
- Stop training early with the **Stop** button if you see convergence.

### Training History

- All past runs are listed in the training history sidebar.
- Click any run to see its config, metrics, and exported adapters.

---

## 8. RAG (Retrieval-Augmented Generation)

### Create a Knowledge Base

1. Open **RAG** from the sidebar.
2. Click **New Knowledge Base** and give it a name.

### Upload Documents

1. Open your knowledge base.
2. Upload documents: PDF, TXT, Markdown, or code files.
3. Documents are automatically chunked and indexed into a local SQLite database.

### Search

- Use the search bar to find relevant chunks across your knowledge base.
- Search is keyword-based, matching against indexed chunks.
- Use results as context when chatting — copy relevant chunks into your prompt, or reference them in your conversation.

---

## 9. Deep Research

### Set Up a Research Agent

1. Open **Research** from the sidebar.
2. Select a loaded local model to power the agent.
3. Enter a research question or topic.
4. Click **Start Research**.

The agent runs multiple steps locally: generating search queries, synthesizing findings, and producing a structured summary. Each step streams its progress so you can follow along.

---

## 10. Export

### Quantize to GGUF

1. Open **Export** from the sidebar.
2. Select a model to quantize.
3. Pick a quantization format (Q4_K_M, Q5_K_M, Q8_0, etc.).
4. Click **Export**. Progress streams in real time.
5. The quantized GGUF file is saved to your models directory.

### Push to HuggingFace Hub

1. In **Settings**, add your HuggingFace token under **HF Token**.
2. In **Export**, click **Push to Hub** after quantizing or fine-tuning.
3. Enter a repo name (e.g., `your-username/my-model`).
4. The model uploads to your HuggingFace account.

### Export LoRA Adapters

- After fine-tuning, click **Export LoRA** to save the adapter as a standalone file.
- Merge LoRA into the base model for a single-file export.

---

## 11. Providers (External LLM APIs)

### Connect an External Provider

1. Open **Settings** → **Providers** from the sidebar.
2. Click **Add Provider**.
3. Enter the provider details:
   - **Name** (e.g., "OpenAI", "Anthropic", "Local Ollama").
   - **Base URL** (e.g., `https://api.openai.com/v1` for OpenAI, `http://localhost:11434/v1` for Ollama).
   - **API Key** (if required).
4. Click **Test Connection** to verify it works.
5. Save the provider.

### Use in Chat

Once a provider is connected, its models appear in the chat model selector alongside local models. Select one to route that conversation to the external API.

---

## 12. MCP Integration

### Add an MCP Server

1. Open **Settings** → **MCP** from the sidebar.
2. Click **Add Server**.
3. Enter the server details:
   - **Name** for identification.
   - **Transport**: HTTP URL or stdio command.
   - For HTTP: enter the full URL (e.g., `http://localhost:3000/mcp`).
   - For stdio: enter the command and arguments (e.g., `npx @modelcontextprotocol/server-filesystem /path/to/dir`).
4. Click **Probe** to test the connection and discover available tools.
5. Save the server.

### Use MCP Tools

- Discovered MCP tools become available in chat and other features.
- The model can invoke these tools during conversations when you enable tool use.

---

## Tips

- **GPU memory**: GGUF models use less VRAM than full-precision models. Start with Q4_K_M quantizations.
- **One model at a time**: Only one GGUF model can be loaded for inference simultaneously. Unload before loading a different one.
- **All data stays local**: Databases, models, and generated content are stored in `~/.flickerx/studio/`. Nothing leaves your machine unless you push to HuggingFace or use an external provider.
- **Development mode**: Run `npm run dev` from the project root for Vite hot-reload during frontend development.
