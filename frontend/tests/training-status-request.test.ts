// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026-present the FlickerX team. All rights reserved.

import assert from "node:assert/strict";
import test from "node:test";

import {
  isTrainingStatusRequestCurrent,
  trainingStatusRequestKey,
} from "../src/features/training/lib/training-status-request.ts";

test("status request identity changes across every runtime lease boundary", () => {
  const initial = trainingStatusRequestKey({
    jobId: "job-a",
    resetGeneration: 3,
    startRequestId: null,
  });

  assert.notEqual(
    trainingStatusRequestKey({
      jobId: "job-b",
      resetGeneration: 3,
      startRequestId: null,
    }),
    initial,
  );
  assert.notEqual(
    trainingStatusRequestKey({
      jobId: "job-a",
      resetGeneration: 4,
      startRequestId: null,
    }),
    initial,
  );
  assert.notEqual(
    trainingStatusRequestKey({
      jobId: "job-a",
      resetGeneration: 3,
      startRequestId: "start-a",
    }),
    initial,
  );
  assert.equal(
    isTrainingStatusRequestCurrent(initial, {
      jobId: "job-a",
      resetGeneration: 3,
      startRequestId: null,
    }),
    true,
  );
  assert.equal(
    isTrainingStatusRequestCurrent(initial, {
      jobId: "job-a",
      resetGeneration: 3,
      startRequestId: "start-a",
    }),
    false,
  );
});
