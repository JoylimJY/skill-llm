## Memory Contract

This skill follows `memory-governor`.

Typical outputs:

- [memory type] -> [target class]
- [memory type] -> [target class]

Current adapter examples:

- [target class] -> [current path or downstream system]

Constraints:

- This skill does not define its own global memory rules.
- This skill should not bypass `memory-governor` promotion or exclusion rules.
- If an optional adapter is missing, use the current fallback behavior instead of inventing a new global rule.
