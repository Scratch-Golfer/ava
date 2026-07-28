"""Stubbed payment 'terminal'.

For the prototype this just simulates a card charge. When you're ready to go
real, replace the body of charge() with a call to the Stripe Terminal SDK's
simulated reader first, then a real Stripe Reader M2 once that's proven out.
The rest of the app (menu.py, agent.py) never needs to change.
"""

import asyncio


async def charge(amount: float) -> dict:
    """Pretend to charge a card for `amount` GBP. Always succeeds, after a
    short delay to mimic a real tap-to-pay interaction."""
    print(f"[payment] Charging £{amount:.2f}...")
    await asyncio.sleep(1.5)
    print("[payment] Payment successful (simulated).")
    return {"status": "success", "amount": amount}
