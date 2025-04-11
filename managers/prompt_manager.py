class PromptManager:

    def __init__(self, user_demographics=None):
        self.user_demographics = user_demographics or {}
        self.conversation_history = []
        self.detected_emotion = "neutral"

        # Initialize with therapeutic system prompt
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

        # Add demographic information if provided
        if self.user_demographics:
            demographics_str = "User demographic information: " + \
                ", ".join(
                    [f"{k}: {v}" for k, v in self.user_demographics.items()])
            system_prompt += f"\n\n{demographics_str}"

        self.conversation_history.append(
            {"role": "system", "content": system_prompt})

    def add_user_message(self, user_text, emotion):
        """Add a user message with emotional state to the conversation history."""
        user_message = f"User said: {user_text}\nUser's emotional state appears to be: {emotion}"
        self.conversation_history.append(
            {"role": "user", "content": user_message})
        self.detected_emotion = emotion
        return user_text, emotion

    def add_assistant_message(self, response):
        """Add an assistant message to the conversation history."""
        self.conversation_history.append(
            {"role": "assistant", "content": response})
        return response

    def clear_history(self):
        """Clear the conversation history except for the system message."""
        system_message = self.conversation_history[0]
        self.conversation_history = [system_message]
        print("Conversation history cleared.")
