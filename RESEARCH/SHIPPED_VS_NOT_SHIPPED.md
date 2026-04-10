# Shipped vs Not Shipped

This page exists because the question comes up naturally:

“Did you remove the research system?”

Short answer:

- **the public research substrate ships**
- **the private acquisition layer does not**

## What ships publicly

- donor packs
- corpus DB builders
- style radar seed definitions and DB builder
- optional embedding index generation
- retrieval selectors
- formatting / internet-symbol packs
- the runtime that consumes all of the above

## What does not ship publicly

- private acquisition lanes
- secret-bearing integrations
- internal scraping / collection machinery
- internal-only ops context

## Why this split exists

Because the public repo should teach users how Brotherizer works without turning GitHub into an accidental data-exhaust dump.

That is the line.
