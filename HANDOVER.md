Cafe Voice Ordering AI ��� Handover Notes
Cafe Voice Ordering AI — Handover Notes
Status: working local prototype, single machine, single customer at a time. Built iteratively
over a few sessions with heavy use of Claude for both the code and live debugging. Handing
over for a proper engineering pass — productionising, multi-session handling, real payment,
better audio hardware.
1. The idea, briefly
Voice AI that stands in for a barista taking a drink order at a cafe counter: greets the customer,
takes their order by voice (asks clarifying questions like size/milk), reads back the order and
total, and “charges” a card (currently stubbed). A webcam triggers the greeting proactively
when someone walks up, and a local webpage shows a live status light plus the customer’s
order as it’s built.
Longer-term intent (not yet built): real payment via a POS’s own API (Square/SumUp/Epos Now
— these have open developer APIs; Toast/Zettle/ TouchBistro are much more restricted), push
completed orders into a POS’s Orders API rather than a standalone ticket, handle multiple
customers back-to-back all day, and eventually explore camera-steered audio (beamforming
toward whoever’s talking) for noisy real-world cafes.
2. Architecture
┌─────────────────────┐
Webcam ─────────► │ greeter.py │──── LLMRunFrame (proactive
│ (OpenCV face det.) │ greeting trigger)
└─────────────────────┘
│
▼ writes face_detected
┌─────────────────────┐
│ status.json │ (shared state file) │
└─────────────────────┘
│◄─── polled every 300-400ms
Mic ──► Pipecat pipeline ───┴──────────────────────────────► Speaker
(VAD → STT → Claude+tools → TTS)
▲
│
▼
│ writes talking / order_items / order_total
Browser tabs, polling status.json via
1
status_server.py (localhost:8765):
- status_display.html (orange/green/pulsing light)
- order_display.html (itemised order + total)
Pipeline (agent.py), left to right: mic → VAD (Silero) → Deepgram STT → Claude
(Anthropic, with tool calls) → Deepgram TTS (Aura-2) → speaker, all orchestrated
by Pipecat (v1.6.0), running as a single local audio transport (no telephony/WebRTC — this is
literally just the Mac’s mic and speaker).
Why Pipecat: handles the genuinely hard real-time bits (turn-taking, VAD, interruption/barge-
in, streaming STT→LLM→TTS) so we didn’t have to hand-roll them. Worth knowing the frame-
work moves fast — some class names below were confirmed against the actual installed version
(1.6.0), not assumed from docs, because the public API has shifted release to release.
Why Deepgram for both STT and TTS: originally used ElevenLabs for TTS, switched to
Deepgram’s own Aura-2 so the whole voice stack (rather than just STT) is one vendor/one API
key. Slight quality tradeoff vs ElevenLabs’ more expressive voices, gained simplicity.
State management (important, and a known limitation): there is a single global Or-
derState instance (order = OrderState() in agent.py) and a single global status.json file.
This is fine for one till running one conversation at a time. It is not multi-session safe — there’s
no notion of “which customer” anywhere. If this needs to serve concurrent customers/tills, this
is the first thing to redesign (probably: one OrderState + PipelineTask per session, keyed by
till ID, and status.json becoming per-till or replaced with a proper pub/sub like websockets
instead of file-polling).
3. Files
File What it does
agent.py Entry point. Builds the Pipecat pipeline,
defines the three LLM tools (add_item,
get_order_summary, take_payment), the
system prompt, and wires the greeter +
status observer in.
menu.py Menu data (drinks/sizes/prices) and
OrderState — the cart logic (add item,
compute total, summarize). Pure Python, no
dependencies on Pipecat.
payment.py Stubbed. charge(amount) just sleeps 1.5s
and returns success. This is the main “not
real yet” piece — see §5.
greeter.py Runs OpenCV Haar-cascade face detection on
a background thread (blocking camera I/O
can’t run on the asyncio loop). On a face
appearing after a configurable absence
window, pushes an LLMRunFrame so Claude
speaks first. Takes a should_greet()
callback so it won’t re-trigger mid-order (see
§6, bug history).
haarcascade_frontalface_default.xml Face detector model file greeter.py loads.
Shipped directly rather than relying on
OpenCV’s bundled copy — see §6,
opencv-python 5.0 note.
2
File What it does
status.py Tiny JSON-file-backed shared state
(face_detected, talking, order_items,
order_total, order_state), written by
greeter.py and agent.py, read by the
browser pages below. Thread-lock-guarded;
this is a deliberately simple mechanism, not
something to scale as-is.
status_server.py A ThreadingHTTPServer (stdlib, no extra
dependency) serving the project directory on
localhost:8765, so the HTML pages can
fetch('/status.json').
status_display.html Big circle: orange = idle, green = face
detected, pulsing = bot talking. Polls
status.json every 300ms.
order_display.html Customer-facing order screen: itemised list +
running total, “payment complete” banner.
Polls status.json every 400ms. Intended for
a tablet/second screen at the counter.
requirements.txt pipecat-
ai[deepgram,anthropic,silero,local]==1.6.0,
python-dotenv, opencv-python<5 (see §6
for why pinned).
.env (not included, gitignored) ANTHROPIC_API_KEY, DEEPGRAM_API_KEY,
DEEPGRAM_TTS_VOICE.
All code in this handover folder is the exact current state, verified to compile together
(python -m py_compile on every file) immediately before writing this doc.
4. Setup
brew install portaudio # macOS system dependency for local audio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env # fill in ANTHROPIC_API_KEY, DEEPGRAM_API_KEY
python agent.py
Grant camera + microphone permission to Terminal in System Settings → Privacy & Security
ahead of time — the camera check runs on a background thread, so macOS can’t reliably show
the permission prompt itself at runtime (this bit us once — see §6).
Open http://localhost:8765/status_display.html and http://localhost:8765/order_display.html
in a browser to see the light and the order screen.
5. What’s genuinely not built yet (the honest gap list)
• Real payment. payment.py is a stub. Plan discussed: rather than bolting on Stripe
directly, prefer whatever POS the target cafe already runs (Square, SumUp, Epos Now,
Clover, Lightspeed all have open, self-serve developer APIs — Toast, Zettle, TouchBistro
3
are much more gated/partner-only). If going directly to Stripe instead: Stripe Terminal’s
reader-driven flow works over plain REST calls from Python for smart standalone readers
(e.g. BBPOS WisePOS E / Stripe Reader M2) — no separate mobile app needed, since the
reader is internet-connected, not USB-tethered to a phone SDK.
• Multi-customer / all-day operation. Single global order state, no session concept, no
crash-recovery/auto-restart. Needs redesign, not just a patch (see §2).
• Printed/POS ticket. Not built. Discussed as a print_ticket tool or pushing into a POS’s
Orders API once one is chosen.
• Noise robustness / real hardware. Currently the MacBook’s own mic+speaker, which
has no acoustic echo cancellation — this caused a real bug (see §6) where the bot
heard its own TTS output and interrupted itself. A proper deployment needs either a mic
array with built-in AEC (ReSpeaker-class hardware) or headphones (not viable for a real
customer-facing kiosk). This is probably the single biggest real-world reliability risk in the
current design.
• Camera-steered audio (beamforming toward the active speaker). Discussed at
length as the “proper” fix for noisy environments, not attempted — current camera use
is only for presence detection, nothing audio-related.
• Any real POS/order-system integration. Nothing pushes anywhere outside this app
currently.
6. Bugs hit during prototyping (useful context, not just history)
• TTS reading markdown literally (“star star” spoken aloud) — Claude was writing
**bold** in replies; text-to-speech has no concept of markdown. Fixed via an ex-
plicit system-prompt instruction: no markdown, plain spoken sentences only. Worth
remembering for any future prompt changes — it’s easy to reintroduce.
• Self-interruption / echo loop — the bot’s own voice, played through the laptop speaker,
was picked up by the laptop mic and mistakenly transcribed as the customer talking, caus-
ing it to repeatedly interrupt itself. Root cause: no AEC between the Mac’s speaker and
mic. Fixed for testing purposes with headphones (and separately, discovered Bluetooth
headsets can reintroduce a similar issue via their call-mode audio path — wired output
+ built-in mic input worked best). Not a real fix for production — needs proper AEC
hardware.
• Over-sensitive VAD causing false interruptions — brief noises (breaths, back-
ground sound) were being treated as the customer starting to talk. Tuned via VAD-
Params(confidence=0.7, start_secs=0.3, stop_secs=0.6) in agent.py—
Pipecat’s Silero VAD defaults are more sensitive than this out of the box.
• Double-greeting mid-order — the face-presence greeter would occasionally re-fire dur-
ing an active order if detection flickered (person shifted position) for long enough to sat-
isfy the “absence” timer. Fixed by adding a should_greet() callback to PersonGreeter,
wired in agent.py as lambda: len(order.items) == 0 — i.e. only allow a proactive
greeting if there’s no order in progress.
• opencv-python 5.0.0 missing cv2.CascadeClassifier — the current major OpenCV
release appears to have broken/incomplete Python bindings for face detection on at least
some platforms. Pinned to opencv-python<5 in requirements, which reliably has Cas-
cadeClassifier. Worth re-checking whether this is fixed in a later 5.x point release be-
fore assuming it’s still broken.
• macOS camera permission prompt failing silently — because camera access hap-
pens on a background thread (greeter.py), macOS can’t show its usual “Allow camera
access?” dialog, and OpenCV just fails to open the device instead of prompting. Fixed by
manually granting Terminal camera access in System Settings ahead of time, rather than
relying on the runtime prompt.
4
• Deepgram Aura voice family mismatch — Aura-2 doesn’t have an Irish voice; “Angus”
is an Aura 1 voice (aura-angus-en, no -2-). Easy to get wrong since most other voices
used are Aura-2.
7. Suggested first things to tackle
Roughly in the order they’d matter for turning this into something a real cafe could pilot:
1. Pick a target POS and build against its real API (Square is the best-documented
option if there’s no existing preference) — this unblocks both real payment and a real
ticket/kitchen flow in one go.
2. Redesign state for multi-session — even just “one order, completed, reset, ready for
next customer” done properly (this prototype’s payment-then-4-second-sleep-then-reset
is a hack, not a real session boundary).
3. Solve AEC properly — either dedicated mic-array hardware, or a software AEC library if
sticking with commodity mic+speaker for longer.
4. Add tests — none exist yet. menu.py’s OrderState is pure logic and trivially testable;
the Pipecat pipeline itself is harder to test automatically and probably needs a recorded-
audio-based integration test rather than unit tests.
