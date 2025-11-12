import asyncio
import json
import websockets

async def subscribe_to_orderbook(token_id):
    # ✅ Correct WebSocket endpoint for real-time data
    uri = "wss://rtds.polymarket.com/ws"

    async with websockets.connect(uri) as ws:
        # ✅ Proper RTDS subscribe format
        sub_msg = json.dumps({
            "type": "subscribe",
            "channel": "orderbook",
            "asset_id": token_id
        })
        await ws.send(sub_msg)
        print(f"📡 Subscribed to RTDS orderbook for token {token_id}\n")

        # ✅ Listen indefinitely for updates
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)

                # RTDS sends various event types
                if "channel" in data and data["channel"] == "orderbook":
                    orderbook = data.get("data", {})
                    print(json.dumps(orderbook, indent=2))

            except websockets.exceptions.ConnectionClosed:
                print("⚠️ Connection closed by server. Reconnecting in 3s...")
                await asyncio.sleep(3)
                return await subscribe_to_orderbook(token_id)
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(2)

if __name__ == "__main__":
    token_id = input("Enter token_id: ").strip()
    asyncio.run(subscribe_to_orderbook(token_id))
