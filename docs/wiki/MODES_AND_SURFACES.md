# Modes and Surfaces

Brotherizer routes rewrites through two concepts:

- **modes** for voice family
- **surfaces** for delivery context

## Modes

Current shipped modes:

- `british_banter_mode`
- `worldwide_ironic_mode`
- `en_reflective_human_mode`
- `en_professional_human_mode`
- `british_professional_human_mode`
- `casual_us_human_mode`
- `ptbr_twitter_mode`
- `ptbr_narrative_human_mode`
- `ptbr_professional_human_mode`
- `seriously_english_mode`
- `seriously_ptbr_mode`

These are defined in [`configs/brotherizer_modes.json`](../../configs/brotherizer_modes.json).

## Surface modes

Brotherizer currently understands:

- `reply`
- `post`
- `thread`
- `bio`
- `caption`
- `note`

## Why both matter

Mode and surface solve different problems.

`casual_us_human_mode` tells Brotherizer what kind of person the line should sound like.

`reply` tells Brotherizer where that line is going to live.

Those are not the same thing.

## Practical examples

- `casual_us_human_mode + reply`
  - short, direct, more text-message-native
- `en_reflective_human_mode + note`
  - more breathable, less compressed, more inward
- `british_professional_human_mode + bio`
  - cleaner and more restrained
- `ptbr_twitter_mode + caption`
  - more internet-native, but still controlled

## A good rule of thumb

Use **mode** to describe the voice.

Use **surface** to describe the stage.
