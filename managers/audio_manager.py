import pyaudio
import wave
import queue
import threading
import tempfile
import numpy as np
from openai.helpers import LocalAudioPlayer
import time


# Audio recording constants
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
SILENCE_THRESHOLD = 300
SILENCE_DURATION = 1.5
MIN_PHRASE_LENGTH = 0.5


class AudioManager:
    def __init__(self):
        self.recording = False
        self.is_speaking = False
        self.recording_led = False
        self.audio = None
        self.stream = None
        self.recording_thread = None
        self.led_thread = None
        self.audio_queue = queue.Queue()
        self.audio_player = LocalAudioPlayer()
        self.system_speaking = False

    def select_bluetooth_microphone(self):
        self.audio = pyaudio.PyAudio()

        bluetooth_devices = []

        for i in range(self.audio.get_device_count()):
            dev_info = self.audio.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels') > 0:
                device_name = dev_info.get('name', '').lower()

                if any(keyword in device_name for keyword in ['bluetooth', 'bt', 'wireless', 'airpods', 'buds', 'headset']):
                    print(f"Found input device {i}: {dev_info.get('name')}")
                    bluetooth_devices.append((i, dev_info.get('name')))

        # Select device
        device_index = None

        if bluetooth_devices:
            device_index = bluetooth_devices[0][0]
            print(
                f"Selected Bluetooth device: {bluetooth_devices[0][1]} (index {device_index})")
        else:
            print("No Bluetooth devices found. Using default microphone.")

        return device_index

    def start_recording(self, record_audio_callback):
        self.recording = True
        self.audio_queue = queue.Queue()

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

            self.recording_thread = threading.Thread(
                target=lambda: self._record_audio(record_audio_callback))
            self.recording_thread.daemon = True
            self.recording_thread.start()
            print("Recording started. Speak now...")

            self.led_thread = threading.Thread(
                target=self._recording_indicator)
            self.led_thread.daemon = True
            self.led_thread.start()

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

                    self.recording_thread = threading.Thread(
                        target=lambda: self._record_audio(record_audio_callback))
                    self.recording_thread.daemon = True
                    self.recording_thread.start()
                    print("Recording started with default device. Speak now...")

                    self.led_thread = threading.Thread(
                        target=self._recording_indicator)
                    self.led_thread.daemon = True
                    self.led_thread.start()

                except Exception as e2:
                    print(f"Error opening default audio stream: {e2}")
                    self.recording = False
            else:
                self.recording = False

    def _recording_indicator(self):
        self.recording_led = True
        indicator_chars = ["|", "/", "-", "\\"]
        i = 0

        while self.recording_led:
            if self.system_speaking:
                print(
                    f"\rSystem speaking {indicator_chars[i]} (Listening paused)", end="")
            elif self.is_speaking:
                print(
                    f"\rRecording {indicator_chars[i]} (Speaking detected)", end="")
            else:
                print(
                    f"\rListening {indicator_chars[i]} (Waiting for speech)", end="")
            i = (i + 1) % len(indicator_chars)
            time.sleep(0.2)

    def _record_audio(self, record_audio_callback):
        silence_frames = 0
        frames = []
        speech_detected = False
        silence_limit = int(SILENCE_DURATION * RATE / CHUNK)
        min_frames = int(MIN_PHRASE_LENGTH * RATE / CHUNK)

        print("Calibrating microphone")
        background_noise = []
        for _ in range(int(5 * RATE / CHUNK)):
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                background_noise.append(np.abs(audio_data).mean())
            except Exception as e:
                print(f"Error during calibration: {e}")
                return

        if background_noise:
            avg_noise = np.mean(background_noise)
            dynamic_threshold = max(SILENCE_THRESHOLD, avg_noise * 2)
            print(
                f"Calibration complete. Background noise level: {avg_noise:.2f}")
            print(
                f"Speech detection threshold set to: {dynamic_threshold:.2f}")
        else:
            dynamic_threshold = SILENCE_THRESHOLD
            print("Calibration failed. Using default threshold.")

        print("\nReady for therapeutic conversation!")

        while self.recording:
            if self.system_speaking:
                time.sleep(0.1)
                continue

            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

                audio_data = np.frombuffer(data, dtype=np.int16)
                audio_level = np.abs(audio_data).mean()

                if audio_level > dynamic_threshold:
                    if not speech_detected:
                        speech_detected = True
                        print("\nSpeech detected!")
                    self.is_speaking = True
                    silence_frames = 0
                else:
                    self.is_speaking = False
                    if speech_detected:
                        silence_frames += 1

                if speech_detected and silence_frames >= silence_limit and len(frames) > min_frames:
                    print("Processing speech segment...")
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        with wave.open(temp_file.name, 'wb') as wf:
                            wf.setnchannels(CHANNELS)
                            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                            wf.setframerate(RATE)
                            wf.writeframes(b''.join(frames))

                        self.audio_queue.put(temp_file.name)
                        record_audio_callback()

                    frames = []
                    silence_frames = 0
                    speech_detected = False

                if len(frames) > int(10 * RATE / CHUNK) and not speech_detected:
                    frames = frames[-int(2 * RATE / CHUNK):]

            except Exception as e:
                print(f"Error reading from audio stream: {e}")
                break

    def stop_recording(self):
        self.recording = False
        self.recording_led = False
        print("Stopping recording...")
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()
        print("Recording stopped.")

    async def play_audio(self, tts_response):
        try:
            self.system_speaking = True
            await self.audio_player.play(tts_response)
        finally:
            self.system_speaking = False
