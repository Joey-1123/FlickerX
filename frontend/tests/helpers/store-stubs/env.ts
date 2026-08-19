// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026-present the FlickerX team. All rights reserved.

/** Minimal settable platform store. */
let deviceType: string | null = null;

export const usePlatformStore = {
  getState: () => ({ deviceType }),
  setState: (next: { deviceType: string | null }) => {
    deviceType = next.deviceType;
  },
};
