---
name: Replit preview access (DNS/VPN, Expo web URL)
description: Why a Replit preview can show gray / ERR_NAME_NOT_RESOLVED, and how to give a user a reachable URL.
---

# Replit preview access troubleshooting

If the in-workspace preview (canvas iframe, "Simulate on iOS") shows a gray/broken
frame, an invalid-certificate error, or the user gets `ERR_NAME_NOT_RESOLVED` when
opening the app URL, it is almost always **environment-side, not a code bug.**

## Diagnosis order
1. Confirm the app is actually serving: `curl localhost:80/` and
   `curl https://$REPLIT_DEV_DOMAIN/` from the container (200 = fine). My
   `app_preview` screenshots also run inside Replit's network, so they prove the
   app works but NOT that the user can reach it.
2. If both `*.repl.co` AND `*.replit.dev` fail to resolve in the user's browser,
   the cause is the **user's DNS/network**: an active **VPN**, ISP/family DNS,
   corporate firewall, or an ad-blocker (Pi-hole/NextDNS). Fix on their side:
   disable VPN, switch DNS to 1.1.1.1 / 8.8.8.8, or test on phone mobile data.
   **Confirmed instance:** user's VPN blocked resolution; disabling it fixed it.

## Reachable URL for an Expo app
- Expo dev uses `router = "expo-domain"`, but the Metro **web** build is also served
  at the **main domain root** through the shared proxy. The reachable public URL is
  `https://$REPLIT_DEV_DOMAIN/` — i.e. the plain `<id>.<cluster>.replit.dev` host.
- Do NOT hand the user the `*.expo.<cluster>.replit.dev` host — that expo subdomain
  is internal and not publicly resolvable (gives ERR_NAME_NOT_RESOLVED).
- `.repl.co` is the legacy preview-wrapper domain; it can be down/unresolvable.
  Always point users at `.replit.dev`, never `.repl.co`.

## Editor/canvas preview for Expo (in-workspace device frame)
- The in-editor preview embeds a wrapper at `<id>.<cluster>.repl.co/__replco/workspace_iframe.html`.
- With `router = "expo-domain"` in the mobile artifact.toml, the wrapper uses the
  `*.expo.<cluster>.repl.co` subdomain, which can be DOWN (curl from container -> 000)
  even when the plain `*.<cluster>.repl.co` wrapper is alive (200) and the main
  `*.<cluster>.replit.dev` serves fine.
- Fix that worked: remove the `router = "expo-domain"` line via
  verifyAndReplaceArtifactToml (cannot change `kind` — that's rejected), then restart
  the expo workflow + presentArtifact. The editor preview then routes through the
  working non-expo `.repl.co` wrapper / main domain.
- Removing expo-domain routing trades away the native Expo Go tunnel for a working
  in-editor web preview. Re-add it if native device testing is needed.
