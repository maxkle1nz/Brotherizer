# Contributing

The most useful contributions to Brotherizer are often not new endpoints.

They are better donor packs.

Especially:

- new languages
- better register coverage
- cleaner professional voices
- stronger reply / caption / note surfaces

## High-value contribution lanes

### 1. New language packs

If you can contribute a clean donor pack in a language the repo barely covers, that is gold.

### 2. Better existing packs

Even in covered languages, pack quality matters more than raw row count.

### 3. Style radar expansion

If you can articulate a real surface behavior the runtime should know about, style radar is the right place to contribute it.

## Contribution workflow

1. create or extend a sanitized donor pack
2. run the pack through the sanitization checklist
3. rebuild the corpus DB locally
4. optionally rebuild embeddings
5. test a few rewrites
6. open a PR with a clear explanation of the language/register added

## Acceptance checklist

Before opening a PR, check all of these:

- the pack is text-only
- identity-bearing metadata is gone
- no local DB files are being committed
- no secrets are present
- the language/register being added is clearly described
- the corpus DB can be rebuilt locally from the submitted pack
- optional embedding rebuild was tested if your contribution depends on semantic retrieval
- a few rewrites were manually checked for obvious drift

## Contribution rules

- one language per pack
- text only
- no identity-bearing metadata
- no keys
- no raw dumps of unreviewed scraped material
- no detector-evasion framing
- do not commit generated `.db` artifacts unless a maintainer explicitly asks for them

## What we want from contributors

Brotherizer needs more databases in more languages.

If you can help build that carefully, you are not adding fluff. You are expanding the real usable surface of the product.
