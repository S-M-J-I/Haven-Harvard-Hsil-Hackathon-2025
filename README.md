# Speech-to-speech BCI powered mental health chatbot with tone control [Winner of the Harvard HSIL Hackathon 2024, Dhaka Hub]

We introduce Haven, a mental health speech-to-speech chatbot that understands your emotions and responds accordingly.

## 🧩 Core Technologies

| Component                 | Description                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------- |
| 🧠 Emotive BCI             | Used to read EEG signals, enabling detection of cognitive states such as attention or engagement. |
| 🗣️ OpenAI GPT-4o + Whisper | Whisper for speech-to-text transcription, GPT-4o for intelligent conversational responses.        |
| 🔥 Firebase                | Stores session data, user inputs, and conversation history.                                       |
| 📺 Streamlit               | Lightweight Python web UI to display conversations, user state, and interface controls.           |

## 📸 Features

- Real-time EEG signal monitoring and integration with conversation flow.
- Voice-to-text transcription via OpenAI Whisper.
- GPT-4o-powered contextual conversation generation.
- Session tracking and data persistence with Firebase.
- Minimalistic UI using Streamlit for live testing and visualization.

## 🧪 How It Works

1. EEG Detection: Emotive headset streams live brainwave data.
2. Voice Input: User speaks into mic → Whisper transcribes speech.
3. Contextual Response: GPT-4o processes input and EEG context. Based on the emotions and text, it selects a tone to respond with (e.g, a depressed user is met with sad tone by Haven), and then responds to the user.
4. Display & Store: Streamlit shows chat; Firebase logs sessions.

## 📚 Future Directions

- Expand EEG interpretation (e.g., frustration, stress, excitement).
- Support multi-modal inputs (gaze, blink, gesture).
- Allow EHR processing.
- Human-in-the-loop finetuning.

## 🧑‍💻 Authors

Sadia Ahmmed, Farhan Ishtiaq, S M Jishanul Islam, Sahid Hossain Mustakim, Asif Islam
