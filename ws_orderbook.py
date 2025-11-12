import asyncio
import json
import websockets

async def subscribe_to_orderbook(token_id):
    uri = "wss://rtds.polymarket.com/v1/ws"  # ✅ Correct RTDS v1 endpoint

    async with websockets.connect(uri) as ws:
        sub_msg = json.dumps({
            "type": "subscribe",
            "channel": "orderbook",
            "asset_id": token_id
        })
        await ws.send(sub_msg)
        print(f"📡 Connected to RTDS live orderbook for {token_id}")

        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                if "channel" in data and data["channel"] == "orderbook":
                    print(json.dumps(data, indent=2))
            except websockets.exceptions.ConnectionClosed as e:
                print(f"⚠️ Connection closed: {e}. Reconnecting...")
                await asyncio.sleep(2)
                return await subscribe_to_orderbook(token_id)
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    token_id = input("Enter token_id: ").strip()
    asyncio.run(subscribe_to_orderbook(token_id))
