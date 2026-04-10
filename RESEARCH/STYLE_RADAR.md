# Style Radar

Style radar is Brotherizer's curated signal layer.

It is not a magic black box and it is not a giant external intelligence system.

It is a small, explicit store of style signals that helps the runtime decide what kinds of formatting, texture, and internet-native moves are appropriate.

## What it does

Style radar helps Brotherizer reason about:

- reflective vs casual energy
- clean bio/profile surfaces
- reply vs thread vs note behavior
- platform-native formatting moves
- compact reaction language

## Inputs

The public seed source lives in:

- [`configs/style_radar_seed_signals.json`](../configs/style_radar_seed_signals.json)

## Runtime role

During payload building, Brotherizer can query style radar signals based on:

- language
- intended bucket

Those signals then inform rewrite conditioning alongside:

- donor snippets
- mode profile
- surface mode
- formatting pack

## What it is not

Style radar is not:

- a live crawler
- a hidden social graph
- a trained classifier with opaque provenance

It is curated signal scaffolding. Useful, but intentionally bounded.
