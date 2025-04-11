import os
import openai
import asyncio
from dotenv import load_dotenv
from agents import TherapyAgent, ToneAnalysisAgent, TTSAgent


class TherapeuticAgentWorkflow:

    def __init__(self):
        load_dotenv()

        openai.api_key = os.getenv("OPENAI_API_KEY")

        self.therapy_agent = TherapyAgent()
        self.tone_agent = ToneAnalysisAgent()
        self.tts_agent = TTSAgent()

    async def process_user_input(self, user_input, bci_content):
        self.therapy_agent.add_message(
            role="user",
            user_content=user_input,
            bci_content=bci_content
        )

        therapy_response = self.therapy_agent.get_response()

        tone_analysis = self.tone_agent.analyze_tone(
            user_text=user_input,
            user_emotion=bci_content,
            bot_response=therapy_response
        )

        print(f"\nTherapist: {therapy_response}")

        await self.tts_agent.process_tts_interaction(therapy_response, tone_analysis)

        return therapy_response, tone_analysis

    async def run_session(self):
        print("Therapeutic Agent System initialized")

        while True:
            # TODO: change to STT
            user_input = input("\nYou: ")

            if user_input.lower() == "exit":
                print("Goodbye! Take care of yourself.")
                await self.tts_agent.process_tts_interaction("Goodbye! Take care of yourself.", tone_analysis="normal")
                break

            bci_content = input("BCI: ")

            await self.process_user_input(user_input, bci_content)


async def main():
    orchestrator = TherapeuticAgentWorkflow()
    await orchestrator.run_session()

if __name__ == "__main__":
    asyncio.run(main())
