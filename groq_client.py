from groq import Groq
from typing import Any, Union

class GroqClient:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)  # Ensure correct initialization
        self.model = "llama-3.3-70b-versatile"

    def summarize_transcript(self, transcript: str) -> str:
        system_prompt = """You are an expert YouTube video transcript analyzer. Your task is to:
1. Create a concise summary of the transcript
2. Extract key topics and themes
3. Identify main points and timestamps
4. Provide a brief overview suitable for a video description
5. Do not use markdown format
"""

        user_prompt = f"""Please analyze and summarize the following video transcript:

{transcript}

Provide a structured analysis following the format specified."""

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.5,
                max_tokens=1024,
                top_p=1
            )
            
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
            else:
                return "Failed to generate a summary."
        except Exception as e:
            return "Error: " + str(e)

    def generate_script(self, prompt: str) -> str:
        system_prompt = """You are an expert YouTube script writer. Create engaging, well-structured scripts that maintain viewer attention and deliver value. Focus on:
1. Compelling hooks
2. Clear section transitions
3. Engaging delivery style
4. Strategic timestamps
5. Natural flow
6. Clear call-to-actions
"""

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=2048,
                top_p=1
            )
            
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
            else:
                return "Failed to generate script."
        except Exception as e:
            return "Error: " + str(e)