# What Ships and What Doesn't

This page exists because people ask the question naturally:

"Did you remove the research system?"

Short answer:

- **the public research substrate ships**
- **the private acquisition layer does not**

## What ships publicly

- donor packs
- corpus DB builders
- style radar seed definitions and the DB builder that goes with them
- optional embedding index generation
- retrieval selectors
- formatting and internet-symbol packs
- the runtime that consumes all of it

## What stays internal

- private acquisition lanes
- secret-bearing integrations
- internal scraping and collection machinery
- internal-only ops context

## Why the split

The public repo should teach you how Brotherizer works without turning GitHub into an accidental data-exhaust dump.

That is the line.
