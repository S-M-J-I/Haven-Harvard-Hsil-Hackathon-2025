import os
from openai import AsyncOpenAI


class OpenAIManager:

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def transcribe_audio(self, audio_file, model="gpt-4o-transcribe"):
        try:
            file_size = os.path.getsize(audio_file)
            if file_size == 0:
                print(f"Audio file is empty (0 bytes)")
                os.remove(audio_file)
                return None

            print(f"Transcribing audio file ({file_size} bytes)...")

            with open(audio_file, "rb") as audio:
                transcription = await self.client.audio.transcriptions.create(
                    model=model,
                    file=audio
                )
            os.remove(audio_file)

            if not transcription.text.strip():
                print("Warning: Transcription returned empty text")
                return None

            return transcription.text

        except Exception as e:
            print(f"Error transcribing audio: {e}")
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except:
                pass
            return None

    async def detect_emotion(self, user_text, model="gpt-4o"):
        try:
            emotion_prompt = f"""
            Analyze the following user statement and determine their likely emotional state.
            Return only a single word or short phrase (1-3 words) that best describes their emotional state.
            
            User statement: "{user_text}"
            
            Emotional state:
            """

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an emotional analysis system that identifies the likely emotional state of a speaker based on their words."},
                    {"role": "user", "content": emotion_prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )

            emotion = response.choices[0].message.content.strip()
            print(f"Detected emotional state: {emotion}")
            return emotion

        except Exception as e:
            print(f"Error detecting emotion: {e}")
            return "neutral"

    async def get_therapeutic_response(self, conversation_history, model="gpt-4o"):
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=conversation_history,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error getting therapeutic response: {e}")
            return "I'm here to listen. Would you like to tell me more about how you're feeling right now?"

    async def analyze_tone(self, user_text, user_emotion, bot_response, model="gpt-4o"):
        try:
            tone_analysis_prompt = f"""
            Analyze the user's input, emotional state, and the AI's response to determine the most appropriate 
            tone and delivery style for the response. Fill in the template with specific recommendations.
            
            USER INPUT: "{user_text}"
            USER EMOTIONAL STATE: "{user_emotion}"
            AI RESPONSE CONTENT: "{bot_response}"
            
            Based on this interaction, complete the following template with specific, detailed recommendations 
            for how the response should be delivered:
            
            Voice: <fill here>
            Punctuation: <fill here>
            Delivery: <fill here>
            Phrasing: <fill here>
            Tone: <fill here>
            
            Be specific, nuanced, and detailed in your recommendations. Consider the emotional state of the user,
            the content of their message, and the nature of the AI's response.
            """

            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert in communication psychology and tone analysis."},
                    {"role": "user", "content": tone_analysis_prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error analyzing tone: {e}")
            return "Voice: Warm and empathetic\nPunctuation: Natural and flowing\nDelivery: Gentle and supportive\nPhrasing: Clear and compassionate\nTone: Caring and understanding"

    async def text_to_speech(self, text, tone_guidance, model="gpt-4o-mini-tts", voice="coral"):
        try:
            async with self.client.audio.speech.with_streaming_response.create(
                model=model,
                voice=voice,
                input=text,
                instructions=tone_guidance,
                response_format="pcm",
            ) as response:
                return response
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return None
