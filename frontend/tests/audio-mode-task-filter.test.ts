// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026-present the FlickerX team. All rights reserved.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  sttEngineForRepoId,
  sttRepoIdForSidecarKey,
  sttSidecarKeyFor,
} from "../src/features/audio/stt-artifacts.ts";
import { detectCapabilities } from "../src/features/model-picker/components/model-selector/model-capabilities.ts";

const pageSource = readFileSync(
  new URL("../src/features/audio/audio-page.tsx", import.meta.url),
  "utf8",
);
const catalogSource = readFileSync(
  new URL("../src/features/audio/catalog.ts", import.meta.url),
  "utf8",
);

test("Hub discovery follows the active audio mode", () => {
  assert.match(
    pageSource,
    /speak: \["text-to-speech"\],[\s\S]*transcribe: \["automatic-speech-recognition"\]/,
  );
  assert.match(pageSource, /task=\{HUB_TASKS_BY_MODE\[mode\]\}/);
});

test("resident sidecar keys restore canonical repo casing", () => {
  assert.equal(
    sttRepoIdForSidecarKey("qwen3-asr-0.6b", "mtmd"),
    "testorg/Qwen3-ASR-0.6B-GGUF",
  );
});

test("Whisper artifacts retain distinct runtime identities", () => {
  assert.equal(
    sttRepoIdForSidecarKey("small", "transformers"),
    "testorg/whisper-small",
  );
  assert.equal(
    sttRepoIdForSidecarKey("small", "gguf"),
    "testorg/whisper-small-GGUF",
  );
  assert.equal(sttEngineForRepoId("testorg/whisper-small"), "transformers");
  assert.equal(sttEngineForRepoId("testorg/whisper-small-GGUF"), "gguf");
  assert.equal(sttEngineForRepoId("testorg/Qwen3-ASR-0.6B-GGUF"), "mtmd");
  assert.equal(sttSidecarKeyFor("testorg/whisper-small-GGUF"), "small");
  assert.match(catalogSource, /isKnownSttArtifactRepoId\(repoId\)/);
});

test("ASR names carry the audio capability badge", () => {
  assert.equal(
    detectCapabilities({ id: "testorg/Qwen3-ASR-0.6B-GGUF" }).audio,
    true,
  );
});
