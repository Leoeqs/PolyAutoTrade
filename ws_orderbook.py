import asyncio
import json
import websockets

async def subscribe_to_orderbook(token_id):
    uri = "wss://clob.polymarket.com/ws"
    async with websockets.connect(uri) as ws:
        # Subscribe to the token orderbook
        sub_msg = json.dumps({
            "type": "subscribe",
            "channel": "book",
            "asset_id": token_id
        })
        await ws.send(sub_msg)
        print(f"📡 Subscribed to live updates for token {token_id}")

        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if "data" in data:
                print(json.dumps(data["data"], indent=2))

if __name__ == "__main__":
    token_id = input("Enter token_id: ").strip()
    asyncio.run(subscribe_to_orderbook(token_id))

