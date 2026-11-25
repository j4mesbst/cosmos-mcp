---
name: superpowers
description: Verify UI changes with a failing test first when useful, systematic debugging, and fresh evidence before claiming completion.
license: MIT
---

# Superpowers verification for Cosmos

1. Capture or reproduce a specific failure. Use [systematic debugging](reference/systematic-debugging.md) to trace the cause before editing.
2. Where a behavior can regress, use [test-driven development](reference/test-driven-development.md) to drive a focused patch.
3. Run the smallest targeted check, then any relevant existing checks. Capture the changed UI and inspect the result.
4. Apply [verification before completion](reference/verification.md). State what ran and what evidence is still missing. Use the project's existing tools and approval process.
