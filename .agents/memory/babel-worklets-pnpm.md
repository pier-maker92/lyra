---
name: react-native-worklets babel/generator resolution
description: Why pinning @babel/core via pnpm override breaks Expo Metro bundling, and the packageExtensions fix
---

# react-native-worklets needs @babel/generator declared explicitly

`react-native-worklets`' babel plugin (pulled in by `babel-preset-expo`) does an
**undeclared** `require('@babel/generator')` and relies on it being hoisted to
`node_modules/.pnpm/node_modules/@babel/generator`.

**Symptom:** Metro fails to bundle `expo-router/entry` with `Cannot find module '@babel/generator'`.
In an autoscale deploy this surfaces as the mobile static build (`artifacts/mobile/scripts/build.js`)
returning HTTP 500 → the whole publish fails. Locally it breaks the `artifacts/mobile: expo` workflow.

**Cause:** A pnpm `override` that pins `@babel/core` (e.g. `^7.29.6`, added for security
GHSA remediation) splits the dependency tree into multiple `@babel/core` / `@babel/generator`
versions. With a version conflict, pnpm stops hoisting `@babel/generator`, so the undeclared
require can't resolve.

**Fix (robust, deterministic):** add a `packageExtensions` entry in `pnpm-workspace.yaml`
declaring `@babel/generator` as a direct dependency of `react-native-worklets`:

```yaml
packageExtensions:
  react-native-worklets:
    dependencies:
      "@babel/generator": "^7.29.6"
```

Then `pnpm install`. Confirm the lockfile snapshot for
`react-native-worklets@0.5.1(@babel/core@...)` now lists `'@babel/generator'`, and that a
`packageExtensionsChecksum` line exists in `pnpm-lock.yaml`. This survives a clean/frozen deploy
install — it no longer depends on hoisting.

**Why:** declaring the dep removes reliance on pnpm hoisting (the fragile part), while keeping
the `@babel/core` security override intact.

**How to apply:** whenever a pnpm override over a Babel package breaks Expo/Metro bundling with a
"Cannot find module '@babel/...'" thrown from a plugin that doesn't declare it, prefer
`packageExtensions` on the offending package over removing the security override or relying on
hoist patterns.
