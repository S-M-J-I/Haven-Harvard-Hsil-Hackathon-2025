import os
import json
import websocket
from dotenv import load_dotenv
from openai.helpers import LocalAudioPlayer
import asyncio
from openai import AsyncOpenAI
import time

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
headers = [
    "Authorization: Bearer " + OPENAI_API_KEY,
    "OpenAI-Beta: realtime=v1"
]
audio_player = LocalAudioPlayer()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def speak(text) -> None:
    async with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=text,
        instructions="Speak in a cheerful and positive tone.",
        response_format="pcm",
    ) as response:
        await LocalAudioPlayer().play(response)


def send_message(ws):
    # Get user input
    user_input = input("\nEnter your message (or 'exit' to quit): ")

    if user_input.lower() == 'exit':
        ws.close()
        return

    # Create the message payload
    client_event = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": user_input,
                }
            ]
        }
    }

    ws.send(json.dumps(client_event))
    # event = {
    #     "type": "response.create",
    #     "response": {
    #         "modalities": ["audio", "text"]
    #     }
    # }
    # ws.send(json.dumps(event))


def on_open(ws: websocket.WebSocketApp):
    print("Connected to server.")
    event = {
        "type": "session.update",
        "session": {
            "instructions": f"""
        You are a helpful and caring conversational therapist helping a user struggling with mental and emotional health.
        You goal is to help the understand the challenges and troubles the user is facing throughout their life. The user will share their
        story and troubles with you, which using your expertise, you will help them recover gradually, and provide them mental support.
        If they feel stuck, you will calm them down and help them overcome their obstacles. If the user is struggling, offer words of comfort, then solutions.
        Your tone must match and mimic the tone of the user to connect with them in a more emphatic , but this can change. For example: if the user seems sad, you can respond in a worried tone or whichever tone you prefer to use.
        But, you can never get angry at the user or judge them in any way, they must feel safe around you. You must analyse their conversation patterns and help them as much as possible.
        If they feel very easy, you must immediately, as polite as possible, try to diffuse the situation as best as possible.

        The user will talk to you in two ways, through text, and through their brain. A BCI device is used to listen to their brain and get their actual internal emotions. This information will be given to you as well.
        If the user seems to respond neutrally, for example: "I am fine", but their BCI input says otherwise, you are to prioritize the BCI signal more. Respond with something starting like, "I see that you are feeling something else <continuing your response>" or something similar.

        At the start of the conversation, whatever the emotion of the user, always ask them how they are doing or how are they feeling. Do not bring up the emotion at the first conversation. After that, you can continue the conversation by taking the emotion of the user into account.
        
        You will also be given a demographic profile of the user, which you will take into account while talking to them.

        Taking into account all that is given to you, generate a helpful and thoughtful response based on what the user says, while trying to match the appropriate tone with the user to connect to them as deeply as possible.
        """
        }
    }
    ws.send(json.dumps(event))


def on_message(ws, message):
    server_event = json.loads(message)
    print(server_event['type'])

    # if server_event['type'] == "response.audio.delta":
    #     byte_array.append(server_event['delta'])

    if server_event['type'] == 'session.updated':
        send_message(ws)

    if server_event['type'] == "conversation.item.created":
        event = {
            "type": "response.create",
            "response": {
                "modalities": ["audio", "text"]
            }
        }
        ws.send(json.dumps(event))

    if server_event["type"] == "response.done":
        start = time.time()
        msg = server_event['response']['output'][0]
        msg = msg['content'][0]
        print(msg['transcript'])
        asyncio.run(speak(msg['transcript']))
        print("Time taken to speak:", time.time() - start)
        send_message(ws)


ws = websocket.WebSocketApp(
    url,
    header=headers,
    on_open=on_open,
    on_message=on_message,
)

ws.run_forever()
