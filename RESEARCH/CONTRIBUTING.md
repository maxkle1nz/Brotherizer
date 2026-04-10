# Contributing to Brotherizer

The most valuable things you can add here are usually not new endpoints. They are solid donor packs. That is where the repo needs help most:

- fresh languages
- better coverage across registers
- clean, pro-sounding voices
- punchier surfaces for replies, captions, notes

## Where to focus

### 1. New languages

If you have a clean donor pack for a language we barely cover, that is one of the strongest contributions you can make.

### 2. Leveling up existing ones

Even in languages we already cover, quality beats raw row count.

### 3. Style radar tweaks

If you spot a real behavior the runtime is missing, style radar is the right place to add it.

## How to contribute

1. Build or grow a sanitized donor pack.
2. Run it through the sanitization checklist.
3. Rebuild the corpus DB on your machine.
4. Rebuild embeddings if you want (optional).
5. Test a handful of rewrites.
6. open the PR with a short note on what is new: language, register, or signal set

## Before you PR

Hit all these:

- text-only pack
- no identity-bearing material left
- zero local DB files committed
- no secrets
- clear description of the language/register
- corpus DB rebuilds cleanly from the pack locally
- embedding rebuild tested if semantic retrieval is part of the contribution
- spot-checked rewrites for drift

## Rules

- one language per pack
- text only
- strip identity metadata
- no keys
- no unvetted scraped dumps
- no detector-dodging framing
- do not commit `.db` files unless a maintainer explicitly asks for them

## What we need

Brotherizer needs more databases in more languages. If you can help build that carefully, you are making the whole system more usable.
