# Modes and Surfaces

Brotherizer routes rewrites through **modes** (voice family) and **surfaces** (delivery context).

You can think of them as two different dials. One decides how the line should sound. The other decides where that line needs to work.

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

Each mode is a voice family. It is not a full publishing format on its own.

## Surface modes

Brotherizer currently understands:

- `reply`
- `post`
- `thread`
- `bio`
- `caption`
- `note`

Surface tells Brotherizer what kind of output it is shaping. A reply and a bio can use the same voice, but they usually should not land the same way.

## Why both matter

Mode and surface solve different problems.

`casual_us_human_mode` tells Brotherizer what kind of person the line should sound like.

`reply` tells Brotherizer where that line is going to live.

One controls voice. The other controls delivery. You usually need both.

## Practical examples

These pairings make the split easier to see:

- `casual_us_human_mode + reply`
  - short, direct, more text-message-native
- `en_reflective_human_mode + note`
  - more breathable, less compressed, more inward
- `british_professional_human_mode + bio`
  - cleaner and more restrained
- `ptbr_twitter_mode + caption`
  - more internet-native, but still controlled

## A good rule of thumb

Use **mode** for the voice.

Use **surface** for the stage.

If the rewrite sounds right but still feels wrong for where it is being posted, check the surface first.
