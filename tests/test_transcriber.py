"""
Unit tests for the TranscriberPipecat class.
"""

import pytest
import asyncio
from transcriber_pipecat import TranscriberPipecat


class TestTranscriberPipecat:
    """Test cases for TranscriberPipecat class."""
    
    def test_initialization(self):
        """Test that TranscriberPipecat can be initialized."""
        transcriber = TranscriberPipecat(model="base", language="en")
        assert transcriber.model == "base"
        assert transcriber.language == "en"
        assert not transcriber.is_running
    
    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        transcriber = TranscriberPipecat()
        assert transcriber.model == "base"
        assert transcriber.language is None
        assert not transcriber.is_running
    
    def test_is_running_property(self):
        """Test the is_running property."""
        transcriber = TranscriberPipecat()
        assert transcriber.is_running is False
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping the transcriber."""
        transcriber = TranscriberPipecat()
        
        # Start transcription in the background
        task = asyncio.create_task(transcriber.start())
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        
        # Check it's running
        assert transcriber.is_running is True
        
        # Stop transcription
        await transcriber.stop()
        
        # Wait for the task to complete
        await task
        
        # Check it's stopped
        assert transcriber.is_running is False
    
    def test_transcribe_audio(self):
        """Test audio transcription method."""
        transcriber = TranscriberPipecat()
        
        # Test with dummy audio data
        audio_data = b"dummy audio data"
        result = transcriber.transcribe_audio(audio_data)
        
        # Currently returns empty string (placeholder implementation)
        assert isinstance(result, str)
    
    def test_with_callback(self):
        """Test initialization with a callback function."""
        callback_called = False
        
        def test_callback(text: str):
            nonlocal callback_called
            callback_called = True
        
        transcriber = TranscriberPipecat(on_transcription=test_callback)
        assert transcriber.on_transcription is not None
