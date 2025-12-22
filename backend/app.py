import asyncio
import base64
import contextlib
import json
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from backend.pipecat_session import PipecatSession, SessionConfig


load_dotenv()

app = FastAPI(title="Pipecat Deepgram + OpenAI Backend", version="0.1.0")

# Serve the frontend (zero-build static files)
_FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/frontend", StaticFiles(directory=_FRONTEND_DIR, html=False), name="frontend")


@app.get("/")
def index():
    # Serve the frontend entrypoint directly.
    if os.path.isdir(_FRONTEND_DIR):
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))
    return JSONResponse({"ok": True, "frontend": "/frontend/index.html"})


@app.get("/healthz")
def healthz():
    return JSONResponse({"ok": True})


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()

    cfg = SessionConfig(
        deepgram_api_key=_env("DEEPGRAM_API_KEY", "") or "",
        openai_model=_env("OPENAI_MODEL", "gpt-4.1") or "gpt-4.1",
        deepgram_model=_env("DG_MODEL", "nova-3-general") or "nova-3-general",
        deepgram_language=_env("DG_LANGUAGE", "es") or "es",
        system_prompt=_env("SYSTEM_PROMPT", "Eres un asistente útil y conciso.") or "",
        sample_rate=int(_env("AUDIO_IN_SAMPLE_RATE", "16000") or "16000"),
        channels=int(_env("AUDIO_IN_CHANNELS", "1") or "1"),
    )

    session = PipecatSession(config=cfg, websocket=ws)
    runner_task: Optional[asyncio.Task] = None

    try:
        await ws.send_text(json.dumps({"type": "ready"}))

        while True:
            msg = await ws.receive()

            if "text" in msg and msg["text"] is not None:
                data = json.loads(msg["text"])
                mtype = data.get("type")

                if mtype == "start":
                    await session.configure(
                        openai_model=data.get("openai_model"),
                        deepgram_model=data.get("deepgram_model"),
                        deepgram_language=data.get("deepgram_language"),
                        system_prompt=data.get("system_prompt"),
                        sample_rate=data.get("sample_rate"),
                        channels=data.get("channels"),
                    )
                    if runner_task is None:
                        runner_task = asyncio.create_task(
                            session.run(), name="pipecat-session-runner"
                        )
                    await ws.send_text(json.dumps({"type": "started"}))

                elif mtype == "audio":
                    # base64 PCM16LE
                    b64 = data.get("data", "")
                    raw = base64.b64decode(b64) if b64 else b""
                    if runner_task is None:
                        runner_task = asyncio.create_task(
                            session.run(), name="pipecat-session-runner"
                        )
                    await session.send_audio(raw)

                elif mtype == "text":
                    if runner_task is None:
                        runner_task = asyncio.create_task(
                            session.run(), name="pipecat-session-runner"
                        )
                    await session.send_text(str(data.get("text", "")))

                elif mtype == "end":
                    await session.end()
                    break

                else:
                    await ws.send_text(
                        json.dumps({"type": "error", "message": f"Unknown message type: {mtype}"})
                    )

            elif "bytes" in msg and msg["bytes"] is not None:
                # Binary message = raw PCM16LE chunk
                if runner_task is None:
                    runner_task = asyncio.create_task(
                        session.run(), name="pipecat-session-runner"
                    )
                await session.send_audio(msg["bytes"])

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
    finally:
        await session.end()
        if runner_task is not None:
            runner_task.cancel()
            with contextlib.suppress(Exception):
                await runner_task
