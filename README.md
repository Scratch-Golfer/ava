# Cafe voice ordering prototype

Local mic + speaker -> Deepgram Nova (STT) -> Claude (order-taking brain,
with tool calls) -> Deepgram Aura-2 (TTS). Payment is stubbed in
`payment.py` so you can test the whole conversation end to end with zero
real hardware or money.

## Setup (macOS)

```
brew install portaudio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with:
- `ANTHROPIC_API_KEY` — console.anthropic.com
- `DEEPGRAM_API_KEY` — console.deepgram.com (free $200 credit on signup,
  covers both STT and TTS usage)
- `DEEPGRAM_TTS_VOICE` — leave as `aura-2-thalia-en` or pick another from
  Deepgram's voice list (developers.deepgram.com/docs/tts-models)

## Run

```
python agent.py
```

Speak into your Mac's mic. The agent will ask what you'd like, clarify size
and milk where needed, read back the order and total, then "charge" a fake
payment (see `[payment]` lines in the console) and log a success.

## Files

- `menu.py` — the menu, prices, and the `OrderState` cart logic. Edit this
  to add drinks, sizes, or change prices.
- `payment.py` — stubbed card charge. Swap the body of `charge()` for a real
  Stripe Terminal SDK call once you're ready to test with a real reader.
- `agent.py` — wires everything into a Pipecat pipeline. The three tools
  (`add_item`, `get_order_summary`, `take_payment`) are what Claude calls
  during the conversation to actually build and complete the order.

## Next steps once this works

- Swap the local mic for a ReSpeaker 4-Mic array for real background-noise
  rejection.
- Swap `payment.py`'s stub for Stripe's Terminal SDK simulated reader, then
  a real Stripe Reader M2.
- Add a `print_ticket` tool that writes the completed order to a receipt
  printer or screen.
