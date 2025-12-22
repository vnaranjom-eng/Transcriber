import asyncio
import json
from dataclasses import dataclass
from typing import Optional

from deepgram import LiveOptions
from fastapi import WebSocket
from loguru import logger

from pipecat.frames.frames import (
    EndFrame,
    ErrorFrame,
    InputAudioRawFrame,
    InterimTranscriptionFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    TranscriptionFrame,
)
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.utils.time import time_now_iso8601


@dataclass
class SessionConfig:
    deepgram_api_key: str
    deepgram_model: str = "nova-3-general"
    deepgram_language: str = "es"
    openai_model: str = "gpt-4.1"
    system_prompt: str = "Eres un asistente útil y conciso."
    sample_rate: int = 16000
    channels: int = 1


class WebsocketSink(FrameProcessor):
    def __init__(self, *, websocket: WebSocket):
        super().__init__(enable_direct_mode=True, name="WebsocketSink")
        self._ws = websocket

    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if direction != FrameDirection.DOWNSTREAM:
            return

        try:
            if isinstance(frame, InterimTranscriptionFrame):
                await self._ws.send_text(
                    json.dumps(
                        {
                            "type": "stt_interim",
                            "text": frame.text,
                            "timestamp": frame.timestamp,
                            "language": str(frame.language) if frame.language else None,
                        }
                    )
                )
            elif isinstance(frame, TranscriptionFrame):
                await self._ws.send_text(
                    json.dumps(
                        {
                            "type": "stt_final",
                            "text": frame.text,
                            "timestamp": frame.timestamp,
                            "language": str(frame.language) if frame.language else None,
                        }
                    )
                )
            elif isinstance(frame, LLMFullResponseStartFrame):
                await self._ws.send_text(json.dumps({"type": "llm_start"}))
            elif isinstance(frame, LLMTextFrame):
                await self._ws.send_text(json.dumps({"type": "llm_delta", "text": frame.text}))
            elif isinstance(frame, LLMFullResponseEndFrame):
                await self._ws.send_text(json.dumps({"type": "llm_end"}))
            elif isinstance(frame, ErrorFrame):
                await self._ws.send_text(
                    json.dumps({"type": "error", "message": frame.error, "fatal": frame.fatal})
                )
        except Exception as e:
            # Don't crash the pipeline if the websocket is gone.
            logger.debug(f"WebsocketSink send failed: {e}")


class PipecatSession:
    def __init__(self, *, config: SessionConfig, websocket: WebSocket):
        self._cfg = config
        self._ws = websocket

        self._lock = asyncio.Lock()
        self._runner_task: Optional[asyncio.Task] = None
        self._runner: Optional[PipelineRunner] = None
        self._task: Optional[PipelineTask] = None
        self._ended = False

    async def configure(
        self,
        *,
        openai_model: Optional[str] = None,
        deepgram_model: Optional[str] = None,
        deepgram_language: Optional[str] = None,
        system_prompt: Optional[str] = None,
        sample_rate: Optional[int] = None,
        channels: Optional[int] = None,
    ):
        async with self._lock:
            if self._runner_task is not None:
                # Keep it simple: require configuration before streaming starts.
                await self._ws.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "message": "configure() must be called before streaming starts",
                        }
                    )
                )
                return

            if openai_model:
                self._cfg.openai_model = openai_model
            if deepgram_model:
                self._cfg.deepgram_model = deepgram_model
            if deepgram_language:
                self._cfg.deepgram_language = deepgram_language
            if system_prompt is not None:
                self._cfg.system_prompt = system_prompt
            if sample_rate:
                self._cfg.sample_rate = int(sample_rate)
            if channels:
                self._cfg.channels = int(channels)

    async def run(self):
        # Lazy-start: run() blocks until pipeline ends; callers usually create_task(self.run()).
        await self._ensure_started()
        assert self._runner_task is not None
        await self._runner_task

    async def _ensure_started(self):
        async with self._lock:
            if self._runner_task is not None:
                return
            if self._ended:
                return

            if not self._cfg.deepgram_api_key:
                raise RuntimeError("Missing DEEPGRAM_API_KEY")

            live_options = LiveOptions(
                encoding="linear16",
                channels=self._cfg.channels,
                sample_rate=self._cfg.sample_rate,
                language=self._cfg.deepgram_language,
                model=self._cfg.deepgram_model,
                interim_results=True,
                smart_format=True,
                punctuate=True,
                vad_events=False,
            )

            stt = DeepgramSTTService(api_key=self._cfg.deepgram_api_key, live_options=live_options)

            llm = OpenAILLMService(model=self._cfg.openai_model)

            context = OpenAILLMContext(
                messages=[{"role": "system", "content": self._cfg.system_prompt}]
                if self._cfg.system_prompt
                else []
            )
            aggregators = llm.create_context_aggregator(context)

            sink = WebsocketSink(websocket=self._ws)

            # Pipeline: audio -> deepgram stt -> user ctx -> openai llm -> assistant ctx -> ws sink
            from pipecat.pipeline.pipeline import Pipeline

            pipeline = Pipeline(
                processors=[
                    stt,
                    aggregators.user(),
                    llm,
                    aggregators.assistant(),
                    sink,
                ]
            )

            self._task = PipelineTask(
                pipeline,
                params=PipelineParams(
                    audio_in_sample_rate=self._cfg.sample_rate,
                ),
            )
            self._runner = PipelineRunner(handle_sigint=False, handle_sigterm=False)
            self._runner_task = asyncio.create_task(self._runner.run(self._task), name="pipecat-run")

    async def send_audio(self, pcm16le: bytes):
        if self._ended:
            return
        if not pcm16le:
            return
        await self._ensure_started()
        assert self._task is not None
        frame = InputAudioRawFrame(
            audio=pcm16le,
            sample_rate=self._cfg.sample_rate,
            num_channels=self._cfg.channels,
        )
        frame.transport_source = "ws"
        await self._task.queue_frame(frame)

    async def send_text(self, text: str):
        if self._ended:
            return
        if not text.strip():
            return
        await self._ensure_started()
        assert self._task is not None
        frame = TranscriptionFrame(
            text.strip(),
            "ws",
            time_now_iso8601(),
        )
        frame.transport_source = "ws"
        await self._task.queue_frame(frame)

    async def end(self):
        async with self._lock:
            if self._ended:
                return
            self._ended = True

        if self._task is not None:
            await self._task.queue_frame(EndFrame())

