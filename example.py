"""
Example usage of TranscriberPipecat.

This script demonstrates how to use the transcriber_pipecat package
for real-time audio transcription.
"""

import asyncio
from transcriber_pipecat import TranscriberPipecat
from loguru import logger


def on_transcription_received(text: str):
    """
    Callback function that receives transcription results.
    
    Args:
        text: The transcribed text
    """
    print(f"Transcription: {text}")


async def main():
    """
    Main function demonstrating transcriber usage.
    """
    # Initialize the transcriber
    transcriber = TranscriberPipecat(
        model="base",
        language="en",
        on_transcription=on_transcription_received
    )
    
    logger.info("Starting transcriber example...")
    
    try:
        # Start transcription in the background
        task = asyncio.create_task(transcriber.start())
        
        # Let it run for a bit (in real usage, this would run indefinitely)
        await asyncio.sleep(5)
        
        # Stop the transcriber
        await transcriber.stop()
        
        # Wait for the task to complete
        await task
        
    except KeyboardInterrupt:
        logger.info("Received interrupt, stopping...")
        await transcriber.stop()
    except Exception as e:
        logger.error(f"Error in example: {e}")
        raise
    
    logger.info("Example completed")


if __name__ == "__main__":
    asyncio.run(main())
