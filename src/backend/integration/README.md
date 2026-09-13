# Integration Contracts

This directory contains the shared integration contracts between the four AssetSentinel team modules.

## Purpose

Each team member owns a separate backend module:

| Module | Owner | Location |
|---|---|---|
| Backend Infrastructure | Member 1 | `src/backend/member1_backend/` |
| ML Pipeline | Member 2 | `src/backend/member2_ml/` |
| Readiness & Decision Engines | Member 3 | `src/backend/member3_readiness/` |
| React Frontend | Member 4 | `src/frontend/` |

Integration contracts define the exact data shapes that cross module boundaries — for example, the Evidence Object that Member 3 receives from Member 2, or the API response shapes that Member 4 renders.

## Contents (to be added during implementation)

- `contracts/` — JSON schema files, Pydantic model stubs, or TypeScript interface definitions shared across modules
- API response shapes (published by Member 1 on Day 1)
- Evidence Object schema (shared between Member 2 output and Member 3 input)
- Readiness Result schema (shared between Member 3 output and Member 4 rendering)

## Rule

No member should implement business logic in this directory.
This directory is for contracts and interface definitions only.
