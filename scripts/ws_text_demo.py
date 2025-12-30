import asyncio
import json

import websockets


async def main():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri, max_size=16 * 1024 * 1024) as ws:
        print("connected")

        # optional: configure
        await ws.send(
            json.dumps(
                {
                    "type": "start",
                    "deepgram_language": "es",
                    "openai_model": "gpt-4.1",
                    "system_prompt": "Responde en español, breve.",
                }
            )
        )

        # inject a text turn (no audio needed)
        await ws.send(json.dumps({"type": "text", "text": "Hola, ¿quién eres?"}))

        while True:
            msg = await ws.recv()
            print(msg)
            data = json.loads(msg)
            if data.get("type") == "llm_end":
                break


if __name__ == "__main__":
    asyncio.run(main())

