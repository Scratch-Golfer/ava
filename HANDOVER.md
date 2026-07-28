Cafe Voice Ordering AI — MVP Build Brief
Goal

Turn the existing working prototype (voice ordering + face-triggered greeting, described in HANDOVER.md) into an MVP: a polished mobile-web or tablet application with a proper UI, replacing the current Terminal-plus-browser-tabs setup.

Current state

See attached HANDOVER.md and codebase. In short: Python + Pipecat pipeline (mic → Deepgram STT → Claude → Deepgram TTS → speaker), OpenCV face detection for proactive greeting, order state and menu logic, a crude polling-based status file feeding two separate throwaway HTML pages (a status light, an order list). Payment is stubbed.

Scope for this pass — IN
A single, unified mobile-web/tablet UI replacing status_display.html + order_display.html, built properly (React or similar, not static polling pages) — see Design spec below.
Real-time listening/talking state shown via a voice visualization, driven by actual audio amplitude/VAD state, not a static icon.
Live order build-up — items appear in the UI as they're added by the voice agent, with the running total always visible.
Camera embedded in the same UI for the presence-triggered greeting (already working in Python — needs surfacing/reflecting in the new UI, e.g. a subtle "customer detected" state).
Clean architecture for connecting a real POS later — don't wire a specific POS yet, but don't hardcode assumptions that would block it (i.e. keep payment.py-equivalent as a swappable interface).
A separate vendor/admin page, behind login, for managing the menu: add/edit/delete products, set name, price, category, and an illustration/image per item. This replaces menu.py's hardcoded Python dict as the source of truth — the voice agent's system prompt and tool schema should read from whatever store the vendor UI edits (a small database, e.g. SQLite/Postgres, not a flat file), so an edit in the vendor panel is reflected in the live menu without a code deploy.
Seed data: pre-populate the menu with a realistic full London cafe drinks menu (see menu.py in the existing codebase for a starting list of ~16 drinks with UK pricing) plus a simple illustration/icon per drink (placeholder icon set is fine for MVP — vendor can replace via the panel).
Deployment: get this hosted on a real URL rather than running locally — Netlify is the intended target (repo-based deploys). Structure the app so frontend and any backend/API can deploy there (or backend on a small separate host if Netlify alone can't run the Python voice pipeline — flag this tradeoff and propose an approach rather than assuming).
Scope for this pass — OUT (do not attempt)
Camera-steered audio / beamforming toward the active speaker. Research-grade, not MVP work. Presence detection only, as already built.
Real payment integration. Keep it stubbed/mocked for this pass.
Multi-customer / concurrent session handling. Single active order at a time is fine for the MVP.
Any specific POS integration. Design for swappability, don't build a specific one yet.
Multi-vendor/multi-tenant support. One vendor login, one menu, one "cafe" for this MVP — don't build organisation/account switching.
Custom illustration artwork. Placeholder/generic icons are fine; don't spend effort on bespoke illustration for MVP.
Design spec (UI)

Direction: dark, modern, data-forward — closer to Whoop's app than a typical POS screen. Specifics:

Palette: near-black background (not pure black), a single accent colour used sparingly and with intensity/opacity shifts to indicate state, rather than multiple traffic-light colours.
Signature element: a voice visualization anchoring the top of the screen — reacts to real audio amplitude. Distinct states: idle (slow ambient pulse), listening (reacts to mic input), talking (reacts to TTS output). This is the one place to spend visual ambition; keep everything else restrained.
Typography: a confident display face for the total/price (tabular numerals), a clean neutral face for order line items. Avoid generic default system fonts if it can be avoided.
Layout: voice visualization in the top third; order items build downward beneath it as they're added, each with a subtle entrance animation; running total pinned and always visible (e.g. sticky bottom bar).
Motion: restrained everywhere except the voice visualization — one orchestrated signature moment, not scattered effects.
Responsive down to mobile width; visible focus states; respect reduced-motion preferences.
Vendor/admin panel
Simple auth (email/password is fine for MVP — no need for SSO/OAuth).
CRUD screen for menu items: name, category, size/price variants, optional milk/extras pricing, image upload or icon picker.
Changes take effect for the voice agent without a redeploy (agent reads menu from the same store the panel writes to).
Visually distinct from the customer-facing screen — this is a back-office tool, doesn't need the same design polish, clarity over style.
Constraints
Keep the existing Python voice pipeline (Pipecat/Deepgram/Claude) as the backend — this pass is about the UI/frontend and how it connects to that backend (likely via websockets replacing the current file-polling status.json mechanism — feel free to redesign this transport layer, the current one was a prototype shortcut, not a design decision to preserve).
Target platform: works well as a tablet-mounted web app at a cafe counter; mobile-responsive is a bonus, not the primary target.
Menu storage moves from menu.py's hardcoded dict to a real database the vendor panel and voice agent both read/write.
Definition of done
 Single running application (not separate HTML files) showing voice state + live order in one coherent UI.
 Voice visualization responds to real audio state within a couple hundred ms of actual mic/speaker activity (no visible lag).
 Order items appear within ~1s of the add_item tool call completing.
 Runs on both a laptop browser and a tablet browser without visual breakage.
 payment.py-equivalent remains cleanly swappable — a reviewer should be able to see where a real POS integration would plug in without needing to touch the UI layer.
 Vendor can log in, edit an item's price or add a new drink, and see that change reflected in the live customer-facing menu without a code deploy.
 Menu is pre-seeded with a realistic ~15-20 item London cafe drinks menu with placeholder illustrations and UK pricing.
 App is deployed and reachable at a real URL, not just running locally.
Suggested approach for the agent
Read HANDOVER.md and the existing codebase fully before proposing an architecture.
Propose the new frontend↔backend transport (websockets recommended) and get sign-off before building — this is a bigger change than it looks and worth agreeing first.
Build the voice visualization and static layout first, with mocked data, and check in before wiring it to the real backend.
Wire to the real backend, test end to end.
Do not modify menu.py, payment.py's external interface, or the Pipecat pipeline logic in agent.py beyond what's needed to expose state over the new transport layer.
