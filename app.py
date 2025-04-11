import streamlit as st
import os
import asyncio
import pyaudio
import wave
import queue
import threading
import tempfile
import time
import numpy as np
from openai import AsyncOpenAI
from dotenv import load_dotenv
from openai.helpers import LocalAudioPlayer

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 300
SILENCE_DURATION = 3
MIN_PHRASE_LENGTH = 0.5


class TherapeuticSpeechSystem:
    def __init__(self,
                 whisper_model="gpt-4o-mini-transcribe",
                 gpt_model="gpt-4o",
                 tone_model="gpt-4o",
                 tts_model="gpt-4o-mini-tts",
                 user_demographics=None,
                 voice="coral"):
        self.whisper_model = whisper_model
        self.gpt_model = gpt_model
        self.tone_model = tone_model
        self.tts_model = tts_model
        self.voice = voice
        self.user_demographics = user_demographics or {}
        self.audio_queue = queue.Queue()

        self.conversation_history = []
        system_prompt = f"""
        You are a helpful and caring conversational therapist helping a user struggling with mental and emotional health.
        You goal is to help the understand the challenges and troubles the user is facing throughout their life. The user will share their
        story and troubles with you, which using your expertise, you will help them recover gradually, and provide them mental support.
        If they feel stuck, you will calm them down and help them overcome their obstacles. If the user is struggling, offer words of comfort, then solutions.
        Your tone must match and mimic the tone of the user to connect with them in a more emphatic , but this can change. For example: if the user seems sad, you can respond in a worried tone or whichever tone you prefer to use.
        But, you can never get angry at the user or judge them in any way, they must feel safe around you. You must analyse their conversation patterns and help them as much as possible.
        If they feel very easy, you must immediately, as polite as possible, try to diffuse the situation as best as possible.

        The user will talk to you in two ways, through text, and through their brain. A BCI device is used to listen to their brain and get their actual internal emotions. This information will be given to you as well.
        If the user seems to respond neutrally, for example: "I am fine", but their BCI input says otherwise, you are to prioritize the BCI signal more. Respond with something starting like, "I see that you are feeling something else <continuing your response>" or something similar.

        You will also be given a demographic profile of the user, which you will take into account while talking to them.

        Taking into account all that is given to you, generate a helpful and thoughtful response based on what the user says, while trying to match the appropriate tone with the user to connect to them as deeply as possible.
        """

        if self.user_demographics:
            demographics_str = "User demographic information: " + \
                ", ".join(
                    [f"{k}: {v}" for k, v in self.user_demographics.items()])
            system_prompt += f"\n\n{demographics_str}"

        self.conversation_history.append(
            {"role": "system", "content": system_prompt})

        self.recording = False
        self.push_to_talk_active = False
        self.audio_player = LocalAudioPlayer()
        self.is_speaking = False
        self.recording_led = False

        self.system_speaking = False

        self.detected_emotion = "neutral"

        self.chat_history = []
        self.new_message_event = threading.Event()

        self.audio = None
        self.stream = None

        self.currently_recording = False

    def select_bluetooth_microphone(self):
        self.audio = pyaudio.PyAudio()

        print("\nSearching for audio input devices...")
        bluetooth_devices = []

        for i in range(self.audio.get_device_count()):
            dev_info = self.audio.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels') > 0:
                device_name = dev_info.get('name', '').lower()

                if any(keyword in device_name for keyword in ['bluetooth', 'bt', 'wireless', 'airpods', 'buds', 'headset']):
                    print(f"Found input device {i}: {dev_info.get('name')}")
                    bluetooth_devices.append((i, dev_info.get('name')))

        device_index = None

        if bluetooth_devices:
            device_index = bluetooth_devices[0][0]
            print(
                f"\nSelected Bluetooth device: {bluetooth_devices[0][1]} (index {device_index})")
        else:
            print("\nNo Bluetooth devices found. Using default microphone.")

        return device_index

    def initialize_audio_system(self):
        device_index = self.select_bluetooth_microphone()

        try:
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=CHUNK
            )
            print("Audio system initialized and ready.")
            return True

        except Exception as e:
            print(f"Error opening audio stream with selected device: {e}")
            if device_index is not None:
                print("Trying default audio device instead...")
                try:
                    self.audio.terminate()
                    self.audio = pyaudio.PyAudio()

                    self.stream = self.audio.open(
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        input_device_index=None,
                        frames_per_buffer=CHUNK
                    )
                    print("Audio system initialized with default device.")
                    return True

                except Exception as e2:
                    print(f"Error opening default audio stream: {e2}")
                    return False
            else:
                return False

    def start_recording(self):
        self.recording = True
        self.audio_queue = queue.Queue()

        if self.audio is None:
            self.audio = pyaudio.PyAudio()
            if not self.initialize_audio_system():
                self.recording = False
                return False

        # Start the indicator thread
        self.led_thread = threading.Thread(
            target=self._recording_indicator)
        self.led_thread.daemon = True
        self.led_thread.start()

        # Start monitoring thread (checks for push-to-talk activation)
        self.monitoring_thread = threading.Thread(
            target=self._monitor_recording)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

        print("Recording system started. Press the button to talk.")
        return True

    def _recording_indicator(self):
        self.recording_led = True
        indicator_chars = ["|", "/", "-", "\\"]
        i = 0

        while self.recording_led:
            if self.system_speaking:
                print(
                    f"\rSystem speaking {indicator_chars[i]} (Listening disabled)", end="")
            elif self.currently_recording:
                print(
                    f"\rRecording {indicator_chars[i]} (Auto-stop on silence)", end="")
            elif self.push_to_talk_active:
                print(
                    f"\rWaiting for speech {indicator_chars[i]} (Push-to-talk active)", end="")
            else:
                print(
                    f"\rListening paused {indicator_chars[i]} (Press button to talk)", end="")
            i = (i + 1) % len(indicator_chars)
            # Use time.sleep instead of asyncio.sleep in threads
            time.sleep(0.2)

    def _monitor_recording(self):
        while self.recording:
            # If push-to-talk is activated and system is not speaking, start recording
            if self.push_to_talk_active and not self.system_speaking and not self.currently_recording:
                # Start a new recording thread
                recording_thread = threading.Thread(target=self._record_audio)
                recording_thread.daemon = True
                recording_thread.start()

            time.sleep(0.1)  # Short sleep to prevent CPU usage

    def activate_push_to_talk(self):
        if not self.system_speaking and self.recording and not self.currently_recording:
            self.push_to_talk_active = True
            print("\nPush-to-talk activated, ready to detect speech...")
            return True
        return False

    def deactivate_push_to_talk(self):
        if self.push_to_talk_active:
            self.push_to_talk_active = False
            print("\nPush-to-talk released.")
            return True
        return False

    def _record_audio(self):
        if self.system_speaking:
            return

        self.currently_recording = True
        frames = []
        silence_frames = 0
        speech_detected = False
        silence_limit = int(SILENCE_DURATION * RATE / CHUNK)
        min_frames = int(MIN_PHRASE_LENGTH * RATE / CHUNK)

        # For calibration
        print("Calibrating microphone for 2 seconds (please be quiet)...")
        background_noise = []
        for _ in range(int(2 * RATE / CHUNK)):  # 2 seconds of calibration
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                background_noise.append(np.abs(audio_data).mean())
            except Exception as e:
                print(f"Error during calibration: {e}")
                self.currently_recording = False
                return

        # Calculate a dynamic threshold based on background noise
        if background_noise:
            avg_noise = np.mean(background_noise)
            # Lower the multiplier to make speech detection more sensitive
            # Changed from 1.5 to 1.3
            dynamic_threshold = max(SILENCE_THRESHOLD, avg_noise * 1.3)
            print(
                f"Calibration complete. Background noise level: {avg_noise:.2f}")
            print(
                f"Speech detection threshold set to: {dynamic_threshold:.2f}")
        else:
            dynamic_threshold = SILENCE_THRESHOLD
            print("Calibration failed. Using default threshold.")

        print("Ready for speech. Will auto-stop on silence.")

        # Record while push-to-talk is active
        recording_start_time = time.time()
        last_speech_time = recording_start_time
        max_recording_duration = 60  # Maximum recording time in seconds

        while self.push_to_talk_active and self.recording and not self.system_speaking:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

                # Check for voice activity
                audio_data = np.frombuffer(data, dtype=np.int16)
                audio_level = np.abs(audio_data).mean()

                if audio_level > dynamic_threshold:
                    if not speech_detected:
                        speech_detected = True
                        print("\nSpeech detected!")
                    silence_frames = 0
                    last_speech_time = time.time()  # Update the last time speech was detected
                else:
                    # Only count silence after speech has been detected
                    if speech_detected:
                        silence_frames += 1

                # Auto-stop on silence after speech was detected
                if speech_detected and silence_frames >= silence_limit:
                    print("\nSilence detected, auto-stopping recording...")
                    break

                # Safety timeout - if recording for too long with no speech
                # Increased from 10 to 15 seconds
                if not speech_detected and (time.time() - recording_start_time > 15):
                    print("\nNo speech detected for 15 seconds, stopping recording...")
                    break

                # Safety timeout - if recording for too long overall
                if (time.time() - recording_start_time > max_recording_duration):
                    print(
                        f"\nMaximum recording duration of {max_recording_duration}s reached, stopping recording...")
                    break

                # If it's been more than 5 seconds since the last speech but less than the silence limit
                # Print a reminder that we're still recording
                if speech_detected and time.time() - last_speech_time > 5 and time.time() - last_speech_time < SILENCE_DURATION:
                    print(
                        "\rStill recording... continue speaking or pause to end recording", end="")

            except Exception as e:
                print(f"Error reading from audio stream: {e}")
                break

        # Reset push to talk state
        self.push_to_talk_active = False

        # Check if we have enough audio to process
        if speech_detected and len(frames) > min_frames:
            recording_duration = len(frames) * CHUNK / RATE
            print(
                f"\nProcessing audio segment ({recording_duration:.2f} seconds)...")

            # Save the audio to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                    wf.setframerate(RATE)
                    wf.writeframes(b''.join(frames))

                self.audio_queue.put(temp_file.name)
        else:
            print("No speech detected or audio too short. Nothing to process.")

        self.currently_recording = False

    def stop_recording(self):
        self.recording = False
        self.push_to_talk_active = False
        self.recording_led = False
        self.currently_recording = False
        print("\nStopping recording system...")
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()
        print("Recording system stopped.")

    async def transcribe_audio(self, audio_file):
        try:
            file_size = os.path.getsize(audio_file)
            if file_size == 0:
                print(f"Audio file is empty (0 bytes)")
                os.remove(audio_file)
                return None

            print(f"Transcribing audio file ({file_size} bytes)...")

            with open(audio_file, "rb") as audio:
                transcription = await client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=audio,
                    language="en"
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

    async def detect_emotion(self, user_text):
        try:
            emotion_prompt = f"""
            Analyze the following user statement and determine their likely emotional state.
            Return only a single word or short phrase (1-3 words) that best describes their emotional state.
            
            User statement: "{user_text}"
            
            Emotional state:
            """

            response = await client.chat.completions.create(
                model=self.tone_model,
                messages=[
                    {"role": "system", "content": "You are an emotional analysis system that identifies the likely emotional state of a speaker based on their words."},
                    {"role": "user", "content": emotion_prompt}
                ],
                temperature=0.3,
                max_tokens=10
            )

            emotion = response.choices[0].message.content.strip()
            print(f"Detected emotional state: {emotion}")
            self.detected_emotion = emotion
            return emotion

        except Exception as e:
            print(f"Error detecting emotion: {e}")
            return "neutral"

    async def get_therapeutic_response(self, user_text):
        print(f"\nYou: {user_text}")
        print(f"Detected emotion: {self.detected_emotion}")

        user_message = f"User said: {user_text}\nUser's emotional state appears to be: {self.detected_emotion}"
        self.conversation_history.append(
            {"role": "user", "content": user_message})

        self.chat_history.append({"role": "user", "content": user_text})
        self.new_message_event.set()

        try:
            response = await client.chat.completions.create(
                model=self.gpt_model,
                messages=self.conversation_history,
                temperature=0.7
            )
            therapeutic_response = response.choices[0].message.content

            self.conversation_history.append(
                {"role": "assistant", "content": therapeutic_response})

            self.chat_history.append(
                {"role": "assistant", "content": therapeutic_response})
            self.new_message_event.set()

            return therapeutic_response
        except Exception as e:
            print(f"Error getting therapeutic response: {e}")
            default_response = "I'm here to listen. Would you like to tell me more about how you're feeling right now?"

            self.chat_history.append(
                {"role": "assistant", "content": default_response})
            self.new_message_event.set()

            return default_response

    async def analyze_tone(self, user_text, user_emotion, bot_response):
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

            response = await client.chat.completions.create(
                model=self.tone_model,
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

    async def text_to_speech(self, text, tone_guidance) -> None:
        print(f"\nTherapist: {text}")
        print(f"\nTone Guidance:\n{tone_guidance}")

        try:
            self.system_speaking = True
            self.push_to_talk_active = False
            self.currently_recording = False

            async with client.audio.speech.with_streaming_response.create(
                model=self.tts_model,
                voice=self.voice,
                input=text,
                instructions=tone_guidance,
                response_format="pcm",
            ) as response:
                await self.audio_player.play(response)

            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
        finally:
            self.system_speaking = False

    async def process_next_audio(self):
        audio_file = self.audio_queue.get()
        transcription = await self.transcribe_audio(audio_file)

        if transcription:
            if "clear history" in transcription.lower():
                self.clear_history()
                return

            emotion = await self.detect_emotion(transcription)

            therapeutic_response = await self.get_therapeutic_response(transcription)

            tone_guidance = await self.analyze_tone(transcription, emotion, therapeutic_response)

            await self.text_to_speech(therapeutic_response, tone_guidance)
        else:
            print("No transcription available - skipping this audio segment")

    def clear_history(self):
        system_message = self.conversation_history[0]
        self.conversation_history = [system_message]
        self.chat_history = []
        self.new_message_event.set()
        print("Conversation history cleared.")

    async def run_conversation(self):
        print("Starting therapeutic conversation system...")
        print("Press the 'Talk' button to speak, and 'Clear Conversation' to reset")

        if not self.start_recording():
            print("Failed to start recording system.")
            return

        try:
            while self.recording:
                if not self.audio_queue.empty():
                    await self.process_next_audio()
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\nEnding conversation...")
        finally:
            self.stop_recording()


# Global variable to store conversation thread
conversation_thread = None


def create_streamlit_app():
    st.set_page_config(
        page_title="Therapeutic Conversation",
        page_icon="🧠",
        layout="wide"
    )

    st.title("AI Therapeutic Conversation")

    # Initialize session state
    if 'conversation_active' not in st.session_state:
        st.session_state.conversation_active = False

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'last_history_length' not in st.session_state:
        st.session_state.last_history_length = 0

    if 'therapy_system' not in st.session_state:
        st.session_state.therapy_system = None

    if 'is_talking' not in st.session_state:
        st.session_state.is_talking = False

    st.sidebar.title("Settings")

    selected_voice = "coral"

    # Start/stop conversation
    if not st.session_state.conversation_active:
        if st.sidebar.button("Start Conversation", use_container_width=True):
            # Create the system
            st.session_state.therapy_system = TherapeuticSpeechSystem(
                voice=selected_voice)
            st.session_state.conversation_active = True

            # Start in a new thread
            global conversation_thread
            conversation_thread = threading.Thread(
                target=run_conversation_in_thread,
                args=(st.session_state.therapy_system,),
                daemon=True
            )
            conversation_thread.start()
            st.rerun()
    else:
        if st.sidebar.button("End Conversation", use_container_width=True):
            # Stop the conversation
            if st.session_state.therapy_system:
                st.session_state.therapy_system.recording = False
            st.session_state.conversation_active = False
            st.session_state.therapy_system = None
            st.session_state.is_talking = False
            st.rerun()

    # Chat container
    chat_container = st.container()

    # Push-to-talk button
    if st.session_state.conversation_active:
        # Get system state
        system_speaking = False
        currently_recording = False
        if st.session_state.therapy_system:
            system_speaking = st.session_state.therapy_system.system_speaking
            currently_recording = st.session_state.therapy_system.currently_recording

        # Create centered column for the push-to-talk button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            button_style = """
            <style>
            div.stButton > button {
                width: 100%;
                height: 80px;
                font-size: 24px;
                font-weight: bold;
                border-radius: 40px;
            }
            </style>
            """
            st.markdown(button_style, unsafe_allow_html=True)

            # Push-to-talk button with different colors and text based on state
            if system_speaking:
                # Disabled button while system is speaking
                st.button("System Speaking...",
                          key="talk_button",
                          disabled=True,
                          use_container_width=True)
            elif currently_recording:
                # Currently recording - auto-stopping enabled
                st.button("Recording... (Auto-stop on silence)",
                          key="talk_button",
                          type="primary",
                          disabled=True,
                          use_container_width=True)
            else:
                # Ready for new recording
                if st.button("Press to Talk",
                             key="talk_button",
                             use_container_width=True):
                    if st.session_state.therapy_system and not system_speaking:
                        st.session_state.therapy_system.activate_push_to_talk()
                        st.rerun()

    # Display the conversation
    with chat_container:
        if st.session_state.conversation_active:
            st.write("Conversation is active. Press the button below to speak.")

            # Update chat history from the system
            if st.session_state.therapy_system:
                st.session_state.chat_history = st.session_state.therapy_system.chat_history

            # Display messages
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.chat_message("user").write(message["content"])
                else:
                    st.chat_message("assistant").write(message["content"])

            # Scroll to bottom (hack using HTML)
            if st.session_state.chat_history:
                js = """
                <script>
                    window.scrollTo(0, document.body.scrollHeight);
                </script>
                """
                st.markdown(js, unsafe_allow_html=True)
        else:
            st.info("Click 'Start Conversation' to begin the therapeutic session.")

    # Status indicator
    if st.session_state.conversation_active:
        status_text = ""
        if system_speaking:
            status_text = "System is speaking..."
        elif currently_recording:
            status_text = "Recording your voice (will auto-stop on silence)"
        else:
            status_text = "Ready - press button to talk"

        st.markdown(f"<div style='text-align:center; margin-top:10px; font-style:italic;'>{status_text}</div>",
                    unsafe_allow_html=True)

    # Periodically check for new messages and rerun
    if st.session_state.conversation_active and st.session_state.therapy_system:
        # Check if anything has changed that requires a UI update
        needs_update = False

        # New messages
        if len(st.session_state.therapy_system.chat_history) > st.session_state.last_history_length:
            st.session_state.last_history_length = len(
                st.session_state.therapy_system.chat_history)
            needs_update = True

        # Recording state changes
        current_system_state = (
            st.session_state.therapy_system.system_speaking,
            st.session_state.therapy_system.currently_recording
        )
        if 'last_system_state' not in st.session_state:
            st.session_state.last_system_state = current_system_state
            needs_update = True
        elif st.session_state.last_system_state != current_system_state:
            st.session_state.last_system_state = current_system_state
            needs_update = True

        if needs_update:
            time.sleep(0.1)
            st.rerun()
        else:
            time.sleep(0.5)
            st.rerun()


def run_conversation_in_thread(therapy_system):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(therapy_system.run_conversation())
    except Exception as e:
        print(f"Error in conversation thread: {e}")
    finally:
        loop.close()


if __name__ == "__main__":
    create_streamlit_app()
