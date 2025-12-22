# Transcriber (Pipecat + Deepgram realtime + OpenAI LLM)

Backend en Python que:

- recibe **audio en tiempo real** por WebSocket (PCM16LE)
- transcribe con **Deepgram** usando **Pipecat**
- manda el texto al **LLM de OpenAI** usando **Pipecat**
- devuelve por WebSocket la transcripción y la respuesta del LLM (en streaming)

## Requisitos

- Python 3.12+
- API keys:
  - `DEEPGRAM_API_KEY`
  - `OPENAI_API_KEY`

## Instalación

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
```

Completa tus keys en `.env`.

## Ejecutar

```bash
python3 -m backend.run
```

Healthcheck: `GET /healthz`

## WebSocket: `GET /ws`

### Entrada (cliente → server)

- **Binario**: cada frame binario es un chunk de audio **PCM16LE** a `sample_rate=16000` y `channels=1` (por defecto).
- **JSON**:
  - `{"type":"start", "sample_rate":16000, "channels":1, "deepgram_language":"es", "deepgram_model":"nova-3-general", "openai_model":"gpt-4.1", "system_prompt":"..." }`
  - `{"type":"audio","data":"<base64 PCM16LE>"}`
  - `{"type":"text","text":"hola"}` (inyecta texto como si fuera una transcripción final)
  - `{"type":"end"}`

### Salida (server → cliente)

- `{"type":"ready"}`
- `{"type":"started"}`
- `{"type":"stt_interim","text":"...","timestamp":"...","language":"es"}`
- `{"type":"stt_final","text":"...","timestamp":"...","language":"es"}`
- `{"type":"llm_start"}`
- `{"type":"llm_delta","text":"..."}` (tokens/chunks)
- `{"type":"llm_end"}`
- `{"type":"error","message":"...","fatal":false}`

## Notas de audio

Este backend asume **PCM 16-bit little-endian** (sin WAV header). Si tu input es WAV/MP3/Opus, conviértelo a PCM16LE antes de enviarlo.

## Demo rápida (sin audio)

Con el server corriendo, podés probar el flujo LLM inyectando texto:

```bash
python3 scripts/ws_text_demo.py
```
