// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026-present the FlickerX team. All rights reserved.

// Rows drop the "testorg/" prefix but keep every other owner, which is what
// tells the two apart.

import assert from "node:assert/strict";
import test from "node:test";
import {
  isFlickerXOwner,
  splitRepoLabel,
} from "../src/features/model-picker/components/model-selector/row-meta.ts";

test("flickerx is the owner whose prefix rows hide", () => {
  assert.equal(
    isFlickerXOwner(splitRepoLabel("testorg/gemma-4-26b").owner),
    true,
  );
  // Case as the Hub listing returns it.
  assert.equal(isFlickerXOwner("FlickerX"), true);
  assert.equal(isFlickerXOwner("flickerxai"), true);
});

test("other owners keep their prefix", () => {
  assert.equal(isFlickerXOwner(splitRepoLabel("Qwen/Qwen3-8B").owner), false);
  assert.equal(isFlickerXOwner("flickerx-community"), false);
  // A bare model name has no owner to hide.
  assert.equal(isFlickerXOwner(splitRepoLabel("gemma-4-26b").owner), false);
});
