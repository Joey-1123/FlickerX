// SPDX-License-Identifier: AGPL-3.0-only
// Copyright 2026-present the FlickerX AI Inc. team. All rights reserved. See /studio/LICENSE.AGPL-3.0

import type { HfSortKey } from "@/features/hub/hooks/use-hub-model-search";
import {
  NewReleasesIcon,
  SlidersHorizontalIcon,
  SparklesIcon,
} from "@hugeicons/core-free-icons";
import type { IconSvgElement } from "@hugeicons/react";
import type { ModelFormatFilter } from "../types";

export type ChannelId =
  | "flickerx-trending"
  | "flickerx-latest"
  | "flickerx-safetensors";

export interface ChannelPreset {
  id: ChannelId;
  label: string;
  icon: IconSvgElement;
  hint: string;
  owner?: string;
  tags?: readonly string[];
  query?: string;
  idSuffix?: string;
  format: ModelFormatFilter;
  sort: HfSortKey;
  finetunableOnly?: boolean;
}

export const CHANNEL_PRESETS: readonly ChannelPreset[] = [
  {
    id: "flickerx-trending",
    label: "Trending",
    icon: SparklesIcon,
    hint: "Most trending models on the Hub.",
    format: "gguf",
    sort: "trendingScore",
  },
  {
    id: "flickerx-latest",
    label: "Latest",
    icon: NewReleasesIcon,
    hint: "Latest models on the Hub.",
    format: "all",
    sort: "createdAt",
  },
  {
    id: "flickerx-safetensors",
    label: "Fine-tune ready",
    icon: SlidersHorizontalIcon,
    hint: "Checkpoints ready to fine-tune.",
    format: "checkpoint",
    sort: "lastModified",
    finetunableOnly: true,
  },
];

export function findChannel(id: ChannelId | null): ChannelPreset | null {
  if (!id) return null;
  return CHANNEL_PRESETS.find((preset) => preset.id === id) ?? null;
}

export type HubSection = "trending" | "latest" | "finetune";

export const SECTION_TO_CHANNEL: Record<HubSection, ChannelId> = {
  trending: "flickerx-trending",
  latest: "flickerx-latest",
  finetune: "flickerx-safetensors",
};

export const CHANNEL_TO_SECTION: Record<ChannelId, HubSection> = {
  "flickerx-trending": "trending",
  "flickerx-latest": "latest",
  "flickerx-safetensors": "finetune",
};

export const HUB_SECTION_TITLE: Record<HubSection, string> = {
  trending: "Trending Now",
  latest: "Latest Models",
  finetune: "Fine-tune Ready",
};
