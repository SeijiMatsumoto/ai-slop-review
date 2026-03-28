# 09 — Data Pipeline (Python)

**Categories:** Overcomplicated abstraction (premature DRY)

1. **Extreme over-engineering for a simple task** — The `clean_user_data` function at the bottom does: filter active users, lowercase some fields, rename 3 keys. This could be ~15 lines of straightforward code. Instead it's 140+ lines with: an ABC, 3 strategy classes, an Enum, a dataclass config, a registry pattern, and a pipeline executor.
2. **`MapStrategy` drops fields not in the mapping** — Line 83-87 only includes fields present in `field_mapping`, silently dropping all other fields. The "remap_fields" step in the usage example loses any field not explicitly mapped (like `id`, `created_at`, etc.).
3. **`VALIDATE` and `ENRICH` types registered in Enum but never implemented** — The `TransformationType` enum has `VALIDATE` and `ENRICH` variants, but no strategies are registered for them. They'll silently skip via the `strategy is None` check.
4. **Class-level mutable `_strategies` dict on `StrategyRegistry`** — Not a bug per se, but the registry is a class-level dict used as a singleton with classmethods, when a simple module-level dict would suffice.
