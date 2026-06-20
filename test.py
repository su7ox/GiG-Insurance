import httpx
import asyncio

BASE = "http://localhost:8000/webhook/whatsapp"
PHONE = "919111111111"

async def send(msg_type="text", text=None, button_id=None, button_title=None):
    if msg_type == "text":
        payload = {"entry": [{"changes": [{"value": {"messages": [{"from": PHONE, "type": "text", "text": {"body": text}}]}}]}]}
    else:
        payload = {"entry": [{"changes": [{"value": {"messages": [{"from": PHONE, "type": "interactive", "interactive": {"type": "button_reply", "button_reply": {"id": button_id, "title": button_title}}}]}}]}]}
    async with httpx.AsyncClient() as client:
        r = await client.post(BASE, json=payload)
        print(f"→ {r.json()}")

async def main():
    print("Step 1 — New worker hits webhook")
    await send(text="hi")

    print("\nStep 2 — Selects Zepto")
    await send(msg_type="interactive", button_id="platform_zepto", button_title="Zepto")

    print("\nStep 3 — Submits Partner ID")
    await send(text="ZPT001")

    print("\nStep 4 — Enter OTP (check server logs for OTP value)")
    otp = input("Enter OTP from server logs: ")
    await send(text=otp)

asyncio.run(main())