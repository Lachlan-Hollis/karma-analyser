import os
import asyncio

from elevenlabs import ElevenLabs


class VoiceAnalyser:
    def __init__(self):
        self.elevenlabs = ElevenLabs(api_key=os.environ["ELEVENLABS_KEY"])
        self.stop_event = asyncio.Event()
