# Transcriber Pipecat Documentation

## Overview

Transcriber Pipecat is a Python package for real-time audio transcription built on top of the Pipecat framework. It provides an easy-to-use interface for integrating speech-to-text capabilities into conversational AI applications.

## Architecture

The package consists of the following main components:

### Core Components

1. **TranscriberPipecat**: The main class that handles audio transcription
2. **Audio Processing**: Handles audio input from various sources
3. **Transcription Engine**: Processes audio and converts it to text
4. **Pipecat Integration**: Integrates with the Pipecat framework for conversational AI

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Basic Installation

```bash
pip install -r requirements.txt
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Usage

### Basic Example

```python
import asyncio
from transcriber_pipecat import TranscriberPipecat

async def main():
    # Initialize the transcriber
    transcriber = TranscriberPipecat(
        model="base",
        language="en"
    )
    
    # Start transcription
    await transcriber.start()
    
    # Your application logic here
    await asyncio.sleep(10)
    
    # Stop transcription
    await transcriber.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Usage with Callbacks

```python
from transcriber_pipecat import TranscriberPipecat

def handle_transcription(text: str):
    print(f"Received: {text}")

transcriber = TranscriberPipecat(
    model="base",
    language="en",
    on_transcription=handle_transcription
)
```

## Configuration

### Environment Variables

You can configure the transcriber using environment variables:

- `TRANSCRIBER_MODEL`: Whisper model to use (default: "base")
- `TRANSCRIBER_LANGUAGE`: Language code (default: auto-detect)
- `TRANSCRIBER_LOG_LEVEL`: Logging level (default: "INFO")

### Configuration File

Create a `.env` file in your project root:

```
TRANSCRIBER_MODEL=base
TRANSCRIBER_LANGUAGE=en
TRANSCRIBER_LOG_LEVEL=INFO
```

## API Reference

### TranscriberPipecat

The main class for audio transcription.

#### Constructor

```python
TranscriberPipecat(
    model: str = "base",
    language: Optional[str] = None,
    on_transcription: Optional[Callable[[str], None]] = None
)
```

**Parameters:**
- `model`: Whisper model size (tiny, base, small, medium, large)
- `language`: Optional language code for transcription
- `on_transcription`: Callback function for transcription results

#### Methods

##### `async start()`

Start the transcription service.

##### `async stop()`

Stop the transcription service.

##### `transcribe_audio(audio_data: bytes) -> str`

Transcribe audio data synchronously.

**Parameters:**
- `audio_data`: Raw audio bytes to transcribe

**Returns:**
- Transcribed text as a string

##### `is_running` (property)

Check if the transcriber is currently running.

**Returns:**
- `True` if running, `False` otherwise

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/vnaranjom-eng/Transcriber.git
cd Transcriber

# Install dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black transcriber_pipecat/
```

### Linting

```bash
flake8 transcriber_pipecat/
mypy transcriber_pipecat/
```

## Supported Models

The package supports the following Whisper models:

- **tiny**: Fastest, lowest accuracy
- **base**: Good balance of speed and accuracy (default)
- **small**: Better accuracy, slower
- **medium**: High accuracy, slow
- **large**: Highest accuracy, slowest

## Troubleshooting

### Common Issues

1. **Audio input not detected**: Ensure your microphone is properly connected and permissions are granted
2. **Slow transcription**: Try using a smaller model (e.g., "tiny" or "base")
3. **Import errors**: Make sure all dependencies are installed

### Getting Help

For issues and questions, please open an issue on the GitHub repository.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on the Pipecat framework
- Uses OpenAI Whisper for speech recognition
