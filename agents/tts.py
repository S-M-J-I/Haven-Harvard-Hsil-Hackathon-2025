from openai.helpers import LocalAudioPlayer
from openai import AsyncOpenAI


async_client = AsyncOpenAI()


class TTSAgent:
    def __init__(self, model="gpt-4o-mini-tts", voice="coral", user_demographics=None):
        self.model = model
        self.voice = voice

    async def process_tts_interaction(self, therapeutic_response, tone_analysis):
        print("\nGenerating and playing audio response...")
        try:
            async with async_client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=therapeutic_response,
                instructions=tone_analysis,
                response_format="pcm",
            ) as response:
                await LocalAudioPlayer().play(response)
                print("Audio playback completed.")
        except Exception as e:
            print(f"Error with TTS playback: {str(e)}")
