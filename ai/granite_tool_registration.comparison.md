# Granite Runtime Registration Comparison

## Files Compared ##
- Strict: ai/granite_tool_registration.runtime.strict.json
- Ultra-strict (no references): ai/granite_tool_registration.runtime.ultrastrict.json

## Payload Metrics ##

| Metric | Strict | Ultra-strict |
|---|---:|---:|
| Size (bytes) | 169,837 | 115,980 |
| Size (KiB) | 165.86 | 113.26 |
| Relative size (ultra/strict) | 0.68x |  |
| Tool count | 6 | 6 |
| "$ref" count | 241 | 0 |
| "$defs" count | 5 | 0 |
| "additionalProperties": false count | 131 | 80 |

## Compatibility Tradeoffs ##

- Strict
  - Pros: Cleaner schema architecture, centralized reuse, easier maintenance.
  - Pros: Better for validators with solid Draft 2020-12 support.
  - Cons: Requires support for local references and definitions.
  - Risk: Some hosted LLM tool validators partially implement JSON Schema and may ignore or fail on references.

- Ultra-strict
  - Pros: No "$ref" and no "$defs"; highest compatibility with limited validators.
  - Pros: Fully self-contained tool parameter schemas per function.
  - Pros: In this repository, the generated payload is smaller than strict.
  - Cons: More duplication inlined at parameter level; future schema updates require regenerating this artifact.

## Recommendation ##

- Use ultra-strict for production runtime registration when targeting heterogeneous model gateways or constrained validators.
- Keep strict as the maintainable source artifact for schema evolution and CI validation.
- Regenerate ultra-strict from strict whenever RaceState fields change.

## Decision Rule ##

- If your runtime supports "$ref" and "$defs" reliably: use strict.
- If runtime behavior is inconsistent or unknown: use ultra-strict.
