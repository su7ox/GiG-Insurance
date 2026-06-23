import httpx, asyncio


async def main():
    payload = {
        "From": "whatsapp:+919111111111",
        "Body": "it was raining heavily today couldn't deliver",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "http://localhost:8000/webhook/whatsapp",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        print(r.text)


asyncio.run(main())
