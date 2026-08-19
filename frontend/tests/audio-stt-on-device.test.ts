// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026-present the FlickerX team. All rights reserved.

import assert from "node:assert/strict";
import test from "node:test";

import { sttDownloadedArtifacts } from "../src/features/audio/audio-page-policy.ts";
import {
  sttEngineForRepoId,
  sttRepoIdForSidecarKey,
} from "../src/features/audio/stt-artifacts.ts";

const repoIdForSidecarKey = (
  key: string,
  engine: "transformers" | "gguf" | "mtmd",
) => {
  const repos: Record<string, string> =
    engine === "gguf"
      ? {
          tiny: "testorg/whisper-tiny-GGUF",
          base: "testorg/whisper-base-GGUF",
          small: "testorg/whisper-small-GGUF",
        }
      : {
          tiny: "testorg/whisper-tiny",
          base: "testorg/whisper-base",
          small: "testorg/whisper-small",
          "qwen3-asr-0.6b": "testorg/Qwen3-ASR-0.6B-GGUF",
        };
  return repos[key] ?? key;
};

test("STT On Device inventory follows all sidecar download engines", () => {
  assert.deepEqual(
    sttDownloadedArtifacts(
      {
        transformers: {
          downloaded_models: ["small", "org/custom-whisper"],
        },
        gguf: { downloaded_models: ["small"] },
        mtmd: { downloaded_models: ["qwen3-asr-0.6b"] },
      },
      repoIdForSidecarKey,
    ),
    [
      {
        repoId: "testorg/whisper-small",
        sidecarKey: "small",
        engine: "transformers",
      },
      {
        repoId: "org/custom-whisper",
        sidecarKey: "org/custom-whisper",
        engine: "transformers",
      },
      {
        repoId: "testorg/whisper-small-GGUF",
        sidecarKey: "small",
        engine: "gguf",
      },
      {
        repoId: "testorg/Qwen3-ASR-0.6B-GGUF",
        sidecarKey: "qwen3-asr-0.6b",
        engine: "mtmd",
      },
    ],
  );
});

test("legacy top-level downloads are retained without duplicate rows", () => {
  assert.deepEqual(
    sttDownloadedArtifacts(
      {
        downloaded_models: ["tiny"],
        transformers: { downloaded_models: ["tiny", "base"] },
      },
      repoIdForSidecarKey,
    ),
    [
      {
        repoId: "testorg/whisper-tiny",
        sidecarKey: "tiny",
        engine: "transformers",
      },
      {
        repoId: "testorg/whisper-base",
        sidecarKey: "base",
        engine: "transformers",
      },
    ],
  );
});

test("only exact curated Qwen artifacts use the finite MTMD runtime", () => {
  assert.equal(sttEngineForRepoId("testorg/Qwen3-ASR-0.6B-GGUF"), "mtmd");
  assert.equal(sttEngineForRepoId("Qwen/Qwen3-ASR-0.6B"), "transformers");
  assert.equal(sttEngineForRepoId("community/Qwen3-ASR-finetune"), "transformers");
  assert.equal(
    sttRepoIdForSidecarKey("qwen3-asr-0.6b", "mtmd"),
    "testorg/Qwen3-ASR-0.6B-GGUF",
  );
});
