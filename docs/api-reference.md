# FlickerX API Reference

> 18 routers · ~220 endpoints · All routes prefixed unless noted.

---

## Table of Contents

- [Auth](#auth) — `/api/auth/*`
- [Chat](#chat) — `/api/chat/*`
- [Models](#models) — `/api/models/*`
- [Hub](#hub) — `/api/hub/*`
- [Inference (LLM)](#inference-llm) — `/api/inference/*`
- [Images](#images) — `/api/inference/images/*`
- [Video](#video) — `/api/inference/video/*`
- [Audio](#audio) — `/api/inference/audio/*`
- [Training](#training) — `/api/train/*`
- [Datasets](#datasets) — `/api/hub/datasets/*`
- [RAG](#rag) — `/api/rag/*`
- [Research](#research) — `/api/chat/research-runs/*`
- [Export](#export) — `/api/export/*`
- [Providers](#providers) — `/api/providers/*`
- [Prompts](#prompts) — `/api/prompts/*`
- [MCP](#mcp) — `/api/mcp/servers/*`
- [Settings](#settings) — `/api/settings/*`
- [System](#system) — `/api/system/*`

---

## Auth

`backend/routers/auth.py` — `/api/auth/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/status` | No | Check if system is initialized | — | `{initialized, requires_password_change}` |
| POST | `/register` | No | Register first user | `{username, password}` | `{access_token, refresh_token, must_change_password}` |
| POST | `/login` | No | Login with username/email + password | `{username, password}` | `{access_token, refresh_token, must_change_password}` |
| POST | `/refresh` | No | Exchange refresh token for new pair | `{refresh_token}` | `{access_token, refresh_token, must_change_password}` |
| POST | `/logout` | Yes | Revoke all refresh tokens for user | — | `{ok}` |
| POST | `/change-password` | Yes | Change password (invalidates sessions) | `{current_password, new_password}` | `{access_token, refresh_token, must_change_password}` |
| GET | `/me` | Yes | Get current user profile | — | `{id, username, email, role, systemPrompt, created_at}` |
| PUT | `/me` | Yes | Update profile (system prompt, name) | `{systemPrompt?, name?}` | `{ok}` |
| DELETE | `/me` | Yes | Delete own account | — | `{ok}` |
| POST | `/forgot-password` | No | Request password reset (returns token for dev) | `{email}` | `{ok, message, debug_token}` |
| POST | `/reset-password` | No | Reset password with token | `{token, new_password}` | `{ok}` |
| POST | `/accept-policies` | Yes | Mark policies as accepted | — | `{ok}` |
| GET | `/admin/users` | Yes (admin) | List all users | — | `{users: [{id, username, email, role, created_at}]}` |
| DELETE | `/admin/users/{id}` | Yes (admin) | Delete a user | — | `{ok}` |
| PATCH | `/admin/users/{id}/role` | Yes (admin) | Change user role | `{role}` | `{ok}` |
| POST | `/upload` | Yes | Upload file (image/pdf) | Raw body | `{url, id, filename}` |
| GET | `/uploads/{filename}` | No | Serve uploaded file | — | FileResponse |
| GET | `/api-keys` | Yes | List API keys | — | `{api_keys: [{id, name, key_prefix, expires_at, created_at}]}` |
| POST | `/api-keys` | Yes | Create API key | `{name, expires_in_days?}` | `{key, api_key}` |
| DELETE | `/api-keys/{key_id}` | Yes | Revoke API key | — | `{ok}` |

---

## Chat

`backend/routers/chat.py` — `/api/chat/*`

### Completions

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/chat/completions` | No | OpenAI-compatible chat completions (SSE streaming) | `{model, messages, stream?, temperature?, top_p?, max_tokens?, top_k?, stop?}` | Chat completion or SSE stream |

### Threads

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/threads` | No | List threads (filter: `model_type`, `pair_id`, `project_id`, `include_archived`) | — | `{threads: [...]}` |
| GET | `/threads/{id}` | No | Get thread by ID | — | Thread object |
| POST | `/threads` | No | Create or upsert thread | `{id?, title?, model?, model_type?, pair_id?, project_id?, folder_id?, pinned?, bookmarked?, archived?}` | Thread object |
| PATCH | `/threads/{id}` | No | Update thread fields | `{title?, model?, model_type?, pair_id?, project_id?, folder_id?, pinned?, bookmarked?, archived?}` | Thread object |
| DELETE | `/threads` | No | Delete threads by IDs | `{ids: [string], delete_files?}` | `{deletedThreadIds, sandboxes_kept}` |
| POST | `/threads/{id}/fork` | No | Fork a thread | `{}` | `{thread, messages, containerSnapshotWarning}` |

### Messages

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/threads/{id}/messages` | No | List messages in thread | — | `{messages: [...]}` |
| GET | `/threads/{id}/messages/{msg_id}` | No | Get single message | — | Message object |
| PUT | `/threads/{id}/messages/{msg_id}` | No | Upsert a message | `{role, content?, model?, tool_calls?, tool_call_id?, name?, reasoning?, extra_content?}` | Message object |
| PUT | `/threads/{id}/messages` | No | Sync messages (batch upsert) | `{messages: [...], pruneMissing?}` | `{messages: [...]}` |
| POST | `/messages:batch` | No | Batch list messages across threads | `{threadIds: [string]}` | `{messagesByThreadId: {}}` |

### Folders

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/folders` | No | List folders | — | `{folders: [...]}` |
| POST | `/folders` | No | Create/update folder | `{id?, name, parent_id?}` | Folder object |
| DELETE | `/folders/{id}` | No | Delete folder | — | `{ok}` |

### Projects

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/projects` | No | List projects | — | `{projects: [...]}` |
| GET | `/projects/{id}` | No | Get project | — | Project object |
| POST | `/projects` | No | Create/update project | `{id?, name, description?, archived?}` | Project object |
| PATCH | `/projects/{id}` | No | Partial update project | `{name?, description?, archived?}` | Project object |
| DELETE | `/projects/{id}` | No | Delete project | — | Project object |

### Attachments

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/attachments` | No | List attachments (pagination: `offset`, `limit`) | — | `{attachments, nextOffset}` |
| GET | `/attachments/{msg_id}/{att_id}/file` | No | Download attachment blob | — | Binary response |
| DELETE | `/attachments/{msg_id}/{att_id}` | No | Delete attachment | — | `{ok}` |

### Misc

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/count` | No | Count total threads | — | `{count}` |
| DELETE | `/` | No | Clear chats (by IDs or all) | `{ids?, operationId?}` | `{deletedThreadIds, sandboxes_kept}` |
| GET | `/export` | No | Export all chat data | — | `{exportedAt, version, threadCount, projects, threads, messages}` |
| GET | `/settings` | No | Get chat settings | — | `{settings: {}}` |
| PUT | `/settings` | No | Save chat settings | `{settings: {}}` | `{settings: {}}` |

### Research stubs

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/research-runs` | No | Create research run (stub) | `{}` | `{id, status}` |
| GET | `/research-runs/{id}` | No | Get research run (stub) | — | `{id, status}` |
| GET | `/research-runs/active` | No | Active research runs | — | `{runs, hasRun}` |

---

## Models

`backend/routers/models.py` — `/api/models/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/list` | No | List all local models | — | `{models, default_models}` |
| GET | `/local` | No | List local models with directory info | — | `{models_dir, hf_cache_dir, lmstudio_dirs, models}` |
| GET | `/config/defaults` | No | Default config for LLM/image/video/audio | — | `{llm, image, video, audio}` |
| GET | `/config/llm` | No | LLM-specific defaults | — | `{n_ctx, n_batch, n_threads, gpu_layers, ...}` |
| GET | `/config/mlx` | No | MLX config defaults | — | `{max_tokens, temperature, top_p}` |
| GET | `/vram-summary` | No | VRAM usage across GPUs | — | `{total_vram_mb, used_vram_mb, free_vram_mb, gpus}` |
| GET | `/load-times` | No | Model load times | — | `{load_times: {}}` |
| GET | `/model-load-defaults` | No | Default load params | — | `{n_ctx, gpu_layers, n_batch, n_threads}` |
| GET | `/supported-quantizers` | No | List GGUF quantization methods | — | `{quantizers: [{id, name, description}]}` |
| GET | `/supported-methods` | No | List quantization methods (base/imatrix) | — | `{methods: [{id, name}]}` |
| POST | `/load` | Yes | Load a model | `{model_path, n_ctx?, gpu_layers?, n_batch?, n_threads?}` | `{status, model_path, n_ctx, gpu_layers}` |
| POST | `/unload` | Yes | Unload current model | — | `{status}` |
| GET | `/scan-folders` | No | List model scan folders | — | `{folders: [{id, path, name}]}` |
| GET | `/gguf-variants` | No | GGUF variants for a repo | — | `{variants, repo_id}` |
| GET | `/kv-cache-estimate` | No | Estimate KV cache size | — | `{kv_bytes, weights_bytes, native_context}` |
| GET | `/recommended-folders` | No | Recommended model folders | — | `{folders: [string]}` |
| GET | `/browse-folders` | No | Browse filesystem (`path`, `show_hidden`) | — | `{path, entries: [{name, path, is_dir}]}` |
| GET | `/loras` | No | List LoRA adapters | — | `{loras: []}` |
| GET | `/checkpoints` | No | List checkpoints | — | `{outputs_dir, models: []}` |

---

## Hub

`backend/routers/hub.py` — `/api/hub/*`

### Search

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/search` | No | Search HuggingFace models (`q`, `owner`, `limit`) | — | `{results: [{id, author, downloads, likes, tags, pipeline_tag, last_modified}], total}` |
| GET | `/owners` | No | List known model owners | — | `{owners: []}` |

### Cache

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/cached-gguf` | No | List cached GGUF models | — | `{cached: [{repo_id, path, files, total_size}]}` |
| GET | `/cached-models` | No | List all cached models | — | `{cached: [{repo_id, path, size}]}` |
| GET | `/cached-model-catalog` | No | Cached model catalog | — | `{catalog: []}` |

### Downloads

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/download` | Yes | Start model download | `{repo_id, gguf_variant?, hf_token?, files?}` | `{state, accepted, job_key}` |
| POST | `/download/cancel` | Yes | Cancel download | `{repo_id, gguf_variant?, generation?}` | `{job_key, state}` |
| GET | `/download-progress` | No | Download progress (`repo_id`) | — | `{downloaded_bytes, expected_bytes, progress, state}` |
| GET | `/download-status` | No | Download status (`repo_id`, `gguf_variant`) | — | `{state, progress}` |
| GET | `/active-downloads` | No | List active downloads | — | `{downloads: [...]}` |
| GET | `/gguf-download-progress` | No | Alias for download-progress | — | Same as download-progress |
| GET | `/transport-status` | No | Transport mode status | — | `{mode, available}` |

### Local models

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/local` | No | List local models | — | `{models, models_dir}` |
| POST | `/local-model-eject` | Yes | Eject local model | `{}` | `{ok}` |
| POST | `/local-model-rename` | Yes | Rename local model | `{}` | `{ok}` |
| DELETE | `/delete-cached` | Yes | Delete cached model | `{}` | `{ok}` |
| POST | `/delete-impact` | Yes | Estimate delete impact | `{}` | `null` |
| GET | `/orphan-companions` | No | Find orphan companion files | — | `{companions, total_bytes}` |

### Sync / Scan / Misc

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/sync` | Yes | Sync hub | — | `{status}` |
| POST | `/sync/cancel` | Yes | Cancel sync | — | `{ok}` |
| GET | `/scan-folders` | No | List scan folders | — | `{folders}` |
| POST | `/scan-folders` | Yes | Add scan folder | `{path}` | `{id, path, name}` |
| DELETE | `/scan-folders/{id}` | Yes | Remove scan folder | — | `{ok}` |
| GET | `/gguf-metadata` | No | Get GGUF metadata (`repo_id`) | — | `{metadata, repo_id}` |
| GET | `/insights` | No | Hub insights | — | `{recent_searches, popular_models}` |
| GET | `/pinned-models` | No | Pinned models | — | `{pinned: []}` |
| GET | `/recent-searches` | No | Recent searches | — | `{searches: []}` |
| GET | `/transport-pref` | No | Transport preference | — | `{mode}` |
| GET | `/download-paths` | No | Download paths | — | `{paths: [string]}` |
| GET | `/hidden-models` | No | Hidden models | — | `{models: []}` |

---

## Inference (LLM)

`backend/routers/inference.py` — `/api/inference/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/status` | No | Inference status (loaded model, n_ctx, gpu_layers) | — | `{loaded, model_path, model_name, n_ctx, gpu_layers, loaded_at}` |
| GET | `/load-progress` | No | Model load progress | — | `{phase, bytes_loaded, bytes_total, fraction}` |
| GET | `/active-generations` | No | Active generation count | — | `{count, thread_ids, active, parallel_slots}` |
| POST | `/load` | Yes | Load GGUF model via llama-cpp | `{model_path, n_ctx?, gpu_layers?, n_batch?, n_threads?, adapter_path?, chat_template?, flash_attn?, ...}` | `{status, model_path, model_name, n_ctx, gpu_layers}` |
| POST | `/unload` | Yes | Unload current model | `{model_path?}` | `{status}` |
| GET | `/monitor` | No | Monitor entries | — | `{entries, total}` |
| GET | `/monitor/{id}` | No | Get monitor entry | — | `{id, status}` |
| DELETE | `/monitor` | No | Clear monitor | — | `{cleared}` |
| POST | `/tool-confirm` | Yes | Confirm tool call | `{}` | `{resolved}` |
| POST | `/chat/count_tokens` | Yes | Estimate token count | `{model, messages}` | `{input_tokens, model}` |

---

## Images

`backend/routers/images.py` — `/api/inference/images/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/status` | No | Image model status | — | `{loaded, loading, model, model_kind, device}` |
| GET | `/info` | No | Image model capabilities | — | `{loaded, model, model_kind, device, supports_inpainting, ...}` |
| GET | `/load-progress` | No | Load progress | — | `{phase, bytes_downloaded, bytes_total, fraction, error}` |
| GET | `/generate-progress` | No | Generation progress | — | `{active, step, total_steps, fraction, eta_seconds}` |
| POST | `/load` | No | Load Stable Diffusion model | `{model_path?, gguf_filename?, model_kind?, hf_token?, ...}` | `{loaded, loading, model, model_kind, device}` |
| POST | `/download-plan` | No | Estimate download size | `{model_path, ...}` | `{files, total_bytes, cached_bytes}` |
| POST | `/unload` | No | Unload image model | — | `{loaded, loading, model, model_kind, device}` |
| POST | `/generate` | No | Generate image(s) | `{prompt, negative_prompt?, width?, height?, steps?, guidance?, seed?, batch_size?, init_image?, mask_image?, strength?, ...}` | `{images: [{id, url, prompt, width, height, seed, ...}]}` |
| POST | `/generate/cancel` | No | Cancel generation | — | `{cancelled}` |
| GET | `/gallery` | No | List gallery (`offset`, `limit`, `archived`) | — | `{images, has_more}` |
| PATCH | `/gallery/{id}` | No | Update image (pin/archive) | `{pinned?, archived?}` | Image object |
| DELETE | `/gallery/{id}` | No | Delete image | — | `null` |
| DELETE | `/gallery` | No | Clear gallery | — | `null` |
| GET | `/gallery/{id}/file` | No | Serve image file | — | FileResponse (PNG) |

---

## Video

`backend/routers/video.py` — `/api/inference/video/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/status` | No | Video model status | — | `{loaded, loading, model, model_kind, device}` |
| GET | `/load-progress` | No | Load progress | — | `{phase, bytes_downloaded, bytes_total, fraction, error}` |
| GET | `/generate-progress` | No | Generation progress | — | `{active, phase, step, total, eta_seconds, video, error}` |
| POST | `/load` | No | Load text-to-video model | `{model_path?, model_kind?, hf_token?, ...}` | `{loaded, loading, model, model_kind, device}` |
| POST | `/download-plan` | No | Estimate download size | `{model_path, ...}` | `{files, total_bytes, cached_bytes}` |
| POST | `/unload` | No | Unload video model | — | `{loaded, loading, model, model_kind, device}` |
| POST | `/generate` | No | Generate video | `{prompt, negative_prompt?, width?, height?, num_frames?, fps?, steps?, guidance?, seed?, ...}` | `{status, video: {id, url, prompt, width, height, num_frames, fps, duration_s, ...}}` |
| POST | `/generate/cancel` | No | Cancel generation | — | `{cancelled}` |
| GET | `/gallery` | No | List videos (`offset`, `limit`, `archived`) | — | `{videos, has_more}` |
| PATCH | `/gallery/{id}` | No | Update video (pin/archive) | `{pinned?, archived?}` | Video object |
| DELETE | `/gallery/{id}` | No | Delete video + files | — | `null` |
| DELETE | `/gallery` | No | Clear gallery | — | `null` |
| GET | `/gallery/{id}/signed-url` | No | Get video URL | — | `{url}` |
| GET | `/gallery/{id}/file` | No | Serve video GIF | — | FileResponse (GIF) |
| GET | `/gallery/{id}/export` | No | Export video (`format`) | — | `{url, format}` |

---

## Audio

`backend/routers/audio.py` — `/api/inference/audio/*`

### TTS

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/generate` | No | Text-to-speech generation | `{messages: [{role, content}], stream?, temperature?, top_p?, max_tokens?}` | `{model, audio: {data, format, sample_rate}, clip_id}` |

### STT (Speech-to-Text)

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/stt/status` | No | STT model status (`refresh`, `model`) | — | `{available, loaded_model, loading, device, models, ...}` |
| POST | `/stt/validate` | No | Validate model name | `{model}` | `{valid, model}` |
| POST | `/stt/load` | No | Load whisper model | `{model?, engine?}` | `{loaded, model}` |
| POST | `/stt/download` | No | Download STT model | `{model, engine?}` | `{status, model}` |
| POST | `/stt/download/cancel` | No | Cancel download | `{model, engine?}` | `{cancelled}` |
| POST | `/stt/unload` | No | Unload STT model | — | `{unloaded}` |
| POST | `/transcribe/raw` | No | Transcribe audio blob (query: `model`, `language`, `fast`) | Raw audio body | `{text, language}` |

### Gallery

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/gallery` | No | List audio clips (`offset`, `limit`, `before_mtime`) | — | `{audio, has_more, next_before_mtime, next_before_id}` |
| DELETE | `/gallery/{id}` | No | Delete clip | — | `null` |
| DELETE | `/gallery` | No | Clear gallery | — | `{removed}` |

---

## Training

`backend/routers/train.py` — `/api/train/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/start` | No | Start LoRA training | `{model_name?, training_type?, hf_dataset?, local_dataset_path?, lora_rank?, lora_alpha?, learning_rate?, num_epochs?, batch_size?, max_seq_length?, ...}` | `{job_id, status, message}` |
| GET | `/start-requests/{id}` | No | Poll start request status | — | `{status, job_id}` |
| POST | `/start-requests/{id}/acknowledge` | No | Acknowledge start | — | `null` |
| POST | `/start-requests/{id}/cancel` | No | Cancel start | — | `{status, job_id}` |
| POST | `/stop` | No | Stop training (optional save) | `{save?, expected_job_id?}` | `{status, message}` |
| POST | `/reset` | No | Reset training state | `{expected_job_id?}` | `{status}` |
| GET | `/status` | No | Training status + metrics | — | `{job_id, phase, is_training_running, details, metric_history}` |
| GET | `/metrics` | No | Training metrics history | — | `{job_id, loss_history, lr_history, step_history}` |
| GET | `/progress` | No | SSE training progress stream | — | SSE stream |
| GET | `/hardware` | No | GPU utilization for training | — | `{available, backend, devices, gpu_utilization_pct, vram_used_mb, vram_total_mb}` |
| GET | `/runs` | No | List training runs (`limit`, `offset`) | — | `{runs, total}` |
| GET | `/runs/{id}` | No | Get run detail | — | `{run, config, metrics}` |
| DELETE | `/runs/{id}` | No | Delete run (`delete_artifacts?`) | — | `{status, message, artifacts_deleted, ...}` |
| PATCH | `/runs/{id}` | No | Rename run | `{display_name?}` | Run object |

---

## Datasets

`backend/routers/datasets.py` — `/api/hub/datasets/*`

### Format detection

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/check-format` | No | Detect dataset format (CSV/JSONL/JSON) | `{dataset_name, subset?, train_split?, local_path?}` | `{detected_format, columns, preview_samples, total_rows, detected_image_column, ...}` |
| POST | `/ai-assist-mapping` | No | AI-assist column mapping | `{columns, samples}` | `{success, suggested_mapping}` |
| POST | `/local-options` | No | List splits for local dataset | `{dataset_name, local_path?}` | `{splits: [{name, num_examples}]}` |

### Upload / Local

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/upload` | No | Upload dataset file | File upload | `{filename, stored_path}` |
| GET | `/local` | No | List local datasets | — | `{datasets: [{name, path, type}]}` |
| GET | `/cached` | No | List HF cached datasets | — | `{cached: [{repo_id, cache_path}]}` |
| DELETE | `/cached` | No | Delete cached dataset | `{repo_id, cache_path?}` | `null` |

### Downloads

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/active-downloads` | No | Active downloads (`repo_id?`) | — | `{downloads: [...]}` |
| POST | `/download` | No | Start dataset download | `{repo_id, hf_token?, use_xet?, transport_mode?}` | `{status, repo_id}` |
| POST | `/download/cancel` | No | Cancel download | `{repo_id, generation?}` | `{repo_id, state}` |
| GET | `/download-status` | No | Download status (`repo_id`) | — | `{status, repo_id, error}` |
| GET | `/download-progress` | No | Download progress (`repo_id`) | — | `{bytes_downloaded, bytes_total, fraction}` |
| GET | `/transport-status` | No | Transport status | — | `{repo_id, transport, active}` |

---

## RAG

`backend/routers/rag.py` — `/api/rag/*`

### Knowledge Bases

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/knowledge-bases` | No | List knowledge bases | — | `{knowledge_bases: [...]}` |
| POST | `/knowledge-bases` | No | Create KB | `{name, description?}` | `{id, name, description, document_count}` |
| PATCH | `/knowledge-bases/{id}` | No | Update KB | `{name?, description?}` | KB object |
| DELETE | `/knowledge-bases/{id}` | No | Delete KB + docs + chunks | — | `null` |
| GET | `/knowledge-bases/{id}/documents` | No | List documents in KB | — | `{documents: [...]}` |
| POST | `/knowledge-bases/{id}/documents` | No | Upload document to KB | File upload | `{documentId, jobId, filename}` |

### Thread / Project Documents

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/threads/{id}/documents` | No | List thread documents | — | `{documents: [...]}` |
| POST | `/threads/{id}/documents` | No | Upload document to thread | File upload | `{documentId, jobId, filename}` |
| GET | `/projects/{id}/documents` | No | List project documents | — | `{documents: [...]}` |
| POST | `/projects/{id}/documents` | No | Upload document to project | File upload | `{documentId, jobId, filename}` |

### Documents

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/documents` | No | List all documents | — | `{documents: [...]}` |
| DELETE | `/documents/{id}` | No | Delete document + chunks | — | `null` |
| GET | `/documents/{id}/preview-target` | No | Preview document chunks (`chunk_id?`) | — | `{document, chunk_id, content}` |
| GET | `/documents/{id}/file-url` | No | Get document file URL | — | `{url}` |
| GET | `/documents/{id}/file` | No | Serve document file | — | FileResponse |

### Search

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/search` | No | Keyword search across chunks | `{query, kb_id?, limit?}` | `{chunks: [{id, content, filename, kb_id, ...}]}` |

### Jobs

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/jobs/{id}` | No | Get indexing job status | — | `{id, documentId, status, numChunks}` |
| GET | `/jobs/{id}/events` | No | SSE job events | — | SSE stream |

### Linked Folders

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/linked-folders` | No | List linked folders (`scope_type`, `scope_id`) | — | `{linked_folders: [...]}` |
| POST | `/knowledge-bases/{id}/linked-folders` | No | Link folder to KB | `{path, scope_type?, scope_id?}` | `{id, path, scope_type, scope_id, status}` |
| POST | `/projects/{id}/linked-folders` | No | Link folder to project | `{path, scope_type?, scope_id?}` | `{id, path, scope_type, scope_id, status}` |
| DELETE | `/linked-folders/{id}` | No | Delete linked folder | — | `null` |
| POST | `/linked-folders/{id}/sync` | No | Sync linked folder | — | `{status}` |
| POST | `/linked-folders/{id}/rebuild` | No | Rebuild linked folder | — | `{status}` |
| GET | `/linked-folder-jobs/{id}` | No | Get folder sync job | — | `{job_id, status}` |
| GET | `/linked-folder-jobs/{id}/events` | No | SSE folder sync events | — | SSE stream |

---

## Research

`backend/routers/research.py` — `/api/chat/research-runs/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/` | No | Create research run | `{thread_id?, query, plan?, inference_request?, rag_scope?, budgets?, instructions?}` | Full run object |
| GET | `/{id}` | No | Get research run | — | Run object |
| GET | `/active` | No | Active runs (`threadId?`) | — | `{runs, hasRun}` |
| POST | `/{id}/approve` | No | Approve plan, start execution | `{plan_revision?, plan_hash?}` | Run object |
| POST | `/{id}/cancel` | No | Cancel run | — | Run object |
| POST | `/{id}/retry` | No | Retry failed run | — | Run object |
| PUT | `/{id}/plan` | No | Update research plan | `{plan: [...], expected_revision}` | Run object |
| POST | `/{id}/events` | No | SSE research events (`after?`) | — | SSE stream |

---

## Export

`backend/routers/export.py` — `/api/export/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/status` | No | Export status | — | `{current_checkpoint, is_vision, is_peft, is_export_active, active_op_kind, ...}` |
| GET | `/logs` | No | Export logs (`since?`) | — | `{entries, cursor, active}` |
| GET | `/logs/stream` | No | SSE log stream (`since?`) | — | SSE stream |
| POST | `/load-checkpoint` | No | Load checkpoint for export | `{checkpoint_path, max_seq_length?, load_in_4bit?, hf_token?}` | `{success, message, details}` |
| POST | `/export-size` | No | Estimate export size | `{model?}` | `{fp16_bytes, total_params, source}` |
| POST | `/export/merged` | No | Export merged model | `{save_directory?, format_type?, push_to_hub?, repo_id?, hf_token?, private?}` | `{success, message, details}` |
| POST | `/export/base` | No | Export base model | `{save_directory?, push_to_hub?, repo_id?, hf_token?, private?, base_model_id?}` | `{success, message, details}` |
| POST | `/export/gguf` | No | Export as GGUF | `{save_directory?, quantization_method?, push_to_hub?, repo_id?, hf_token?, imatrix?, imatrix_path?}` | `{success, message, details}` |
| POST | `/export/lora` | No | Export LoRA adapter | `{save_directory?, push_to_hub?, repo_id?, hf_token?, private?, gguf?, gguf_outtype?}` | `{success, message, details}` |
| POST | `/cleanup` | No | Clear export logs | — | `{status}` |
| POST | `/cancel` | No | Cancel active export | — | `{status}` |

---

## Providers

`backend/routers/providers.py` — `/api/providers/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/public-key` | No | Public key for client-side encryption | — | `{public_key}` |
| GET | `/registry` | No | List known providers (openai, anthropic, google, groq, ...) | — | `{providers: [{id, name, base_url, requires_key}]}` |
| GET | `/` | No | List saved provider configs | — | `{providers: [{id, provider_id, name, api_key-masked, base_url, models}]}` |
| POST | `/` | No | Create provider config | `{provider_id, name?, api_key?, base_url?, models?}` | Config object (key masked) |
| PUT | `/{id}` | No | Update provider config | `{name?, api_key?, base_url?, models?}` | Config object |
| DELETE | `/{id}` | No | Delete provider config | — | `null` |
| PUT | `/{id}/api-key/migrate` | No | Migrate API key | `{api_key}` | `{migrated}` |
| POST | `/test` | No | Test provider connectivity | `{provider_type, provider_id?, encrypted_api_key?, base_url?, model_id?}` | `{success, message, models_count}` |
| POST | `/models` | No | Fetch model list from provider | `{provider_type, provider_id?, encrypted_api_key?, base_url?}` | `[{id, display_name, context_length, owned_by}]` |

### OAuth (placeholder)

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| POST | `/{id}/oauth/start` | No | Start OAuth flow | — | `{flow_id, url}` |
| GET | `/{id}/oauth/flows/{flow_id}` | No | Get OAuth flow status | — | `{flow_id, status}` |
| POST | `/{id}/oauth/flows/{flow_id}/complete` | No | Complete OAuth | — | `{status, token}` |
| DELETE | `/{id}/oauth/flows/{flow_id}` | No | Cancel OAuth flow | — | `{status}` |
| DELETE | `/{id}/oauth` | No | Disconnect OAuth | — | `{status}` |

---

## Prompts

`backend/routers/prompts.py` — `/api/prompts/*`

### Entries

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/entries` | No | List prompt entries | — | `{entries: [{id, title, content, category, tags}]}` |
| PUT | `/entries/{id}` | No | Create/update entry | `{title, content, category?, tags?}` | Entry object |
| DELETE | `/entries/{id}` | No | Delete entry | — | `null` |
| POST | `/entries/bulk` | No | Bulk save entries | `{entries: [{title, content, category?, tags?}]}` | `{entries: [...]}` |

### Lists

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/lists` | No | List prompt lists | — | `{lists: [{id, name, entries}]}` |
| PUT | `/lists/{id}` | No | Create/update list | `{name, entries: [{...}]}` | List object |
| DELETE | `/lists/{id}` | No | Delete list | — | `null` |
| POST | `/lists/bulk` | No | Bulk save lists | `{lists: [{name, entries}]}` | `{lists: [...]}` |

---

## MCP

`backend/routers/mcp.py` — `/api/mcp/servers/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/` | No | List MCP servers | — | `{servers: [...]}` |
| POST | `/` | No | Create MCP server | `{name, transport?, command?, args?, url?, headers?, env?, enabled?, use_oauth?}` | Server object |
| PUT | `/{id}` | No | Update MCP server | `{name?, transport?, command?, args?, url?, headers?, env?, enabled?}` | Server object |
| DELETE | `/{id}` | No | Delete MCP server | — | `null` |
| POST | `/{id}/refresh` | No | Refresh server tools (probe) | — | `{ok, tool_count, error}` |
| POST | `/test` | No | Test server without saving | `{url?, headers?, transport?, command?, args?, env?, name?, use_oauth?}` | `{ok, tool_count, error}` |
| POST | `/import` | No | Import servers (dedup by URL) | `{servers: [{name, transport, command?, url?, ...}]}` | `{imported, servers}` |

---

## Settings

`backend/routers/settings.py` — `/api/settings/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/read` | Yes | Read a setting (`key` query) | — | `{key, value}` |
| GET | `/list` | Yes | List all settings | — | `{settings: {key: value}}` |
| PUT | `/write` | Yes | Write a setting | `{key, value}` | `{ok}` |
| PUT | `/bulk-write` | Yes | Bulk write settings | `{settings: {key: value}}` | `{ok, count}` |
| GET | `/export` | Yes | Export all settings | — | `{settings: {}, exported_at}` |
| PUT | `/import` | Yes | Import settings | `{settings: {key: value}}` | `{ok, imported}` |
| GET | `/hugging-face-token` | Yes | Get HF token | — | `{token}` |
| PUT | `/hugging-face-token` | Yes | Save HF token | `{token}` | `{ok}` |
| DELETE | `/hugging-face-token` | Yes | Delete HF token | — | `{ok}` |
| GET | `/generation-presets` | Yes | Get image/video generation presets | — | `{presets: {image: {...}, video: {...}}}` |
| PUT | `/generation-presets` | Yes | Save generation presets | `{presets: {...}}` | `{ok}` |
| GET | `/upload-limits` | Yes | Get upload limits | — | `{limits: {max_file_size_mb, max_total_mb, allowed_types}}` |
| GET | `/personalization` | Yes | Get personalization (theme, lang, notifications) | — | `{theme, language, notifications}` |
| PUT | `/personalization` | Yes | Save personalization | `{theme?, language?, notifications?}` | `{saved}` |

---

## System

`backend/routers/system.py` — `/api/system/*`

| Method | Path | Auth | Description | Body | Response |
|--------|------|------|-------------|------|----------|
| GET | `/status` | No | System status | — | `{status, version, platform, python_version}` |
| GET | `/hardware-info` | No | CPU, memory, GPU, disk info | — | `{cpu, memory, gpus, disk}` |
| GET | `/gpu-info` | No | GPU info only | — | `{gpus: [{name, vram_total_mb, vram_used_mb, ...}]}` |
| GET | `/cuda-info` | No | CUDA availability | — | `{available, gpus}` |
| GET | `/disk-info` | No | Disk usage | — | `{total_bytes, used_bytes, free_bytes, percent, path}` |
| GET | `/accelerator-usage` | No | GPU utilization history | — | `{history: [{timestamp, gpus}]}` |
| GET | `/process-metrics` | No | Process metrics (PID, RSS, CPU%) | — | `{pid, rss_bytes, vms_bytes, cpu_percent, num_threads, uptime_seconds}` |
| GET | `/logs` | No | System logs (`since?`, `limit?`) | — | `{logs: [string], sources: [string]}` |
| GET | `/metrics-stream` | No | SSE real-time metrics (CPU, RAM, GPU, disk, net) | — | SSE stream `{cpu_percent, ram_*, gpus, disk_*, net_*, process, timestamp}` |

---

## Notes

- **Auth**: "Yes" means the endpoint requires a valid JWT in `Authorization: Bearer <token>` or a valid API key.
- **Admin endpoints**: `/api/auth/admin/*` additionally require `role: "admin"`.
- **SSE endpoints**: Return `text/event-stream` with `data: {json}\n\n` framing, terminated by `data: [DONE]\n\n`.
- **File uploads**: Use `multipart/form-data` unless raw body is noted.
- **Rate limiting**: Login endpoint enforces 5 failed attempts per user per 60s, 30 per IP.
