import openai


class ToneAnalysisAgent:
    def __init__(self, model="gpt-4o"):
        self.model = model

    def analyze_tone(self, user_text, user_emotion, bot_response):
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

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in communication psychology and tone analysis."},
                    {"role": "user", "content": tone_analysis_prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error analyzing tone: {str(e)}"
