import os
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AIHandler:
    def __init__(self):
        # We'll load the key here to support the user's .env file
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        self.provider = "mock" 
        self.client = None
        
        # Priority 1: Google Gemini
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.client = genai
                self.provider = "gemini"
                print("AIHandler: Switched to Gemini provider.")
            except ImportError:
                print("AIHandler: google-generativeai library not found.")
            except Exception as e:
                print(f"AIHandler: Error initializing Gemini: {e}.")

        # Priority 2: Groq (Fallback if Gemini missing)
        elif self.groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.groq_key)
                self.provider = "groq"
                print("AIHandler: Switched to GROQ provider.")
            except Exception as e:
                print(f"AIHandler: Error initializing Groq: {e}.")
        
        if self.provider == "mock":
            print("AIHandler: Using mock provider.")
            
    def process_text(self, text, mode="commander", prompt_instruction=None):
        """
        Process the text based on the mode.
        mode: 'commander', 'explain'
        prompt_instruction: Used for 'commander' mode (e.g. "Translate to Spanish")
        """
        
        if self.provider == "gemini":
            try:
                return self._call_gemini(text, mode, prompt_instruction)
            except Exception as e:
                print(f"Gemini API Error: {e}. Falling back to mock.")
                return self._mock_response(text, mode, prompt_instruction)
                
        elif self.provider == "groq":
            try:
                return self._call_groq(text, mode, prompt_instruction)
            except Exception as e:
                print(f"Groq API Error: {e}. Falling back to mock.")
                return self._mock_response(text, mode, prompt_instruction)
        
        return self._mock_response(text, mode, prompt_instruction)

    def _mock_response(self, text, mode, prompt_instruction):
        time.sleep(1) # Simulate network delay
        
        if mode == "commander":
            return f"[Commander: {prompt_instruction}] {text}"
            
        elif mode == "explain":
            return f"[Explanation] This text contains {len(text.split())} words and appears to be a code/text snippet."
            
        return text

    def _call_gemini(self, text, mode, prompt_instruction):
        system_instruction = ""
        
        if mode == "commander":
            system_instruction = "Execute the user's specific instruction on the text. Output ONLY the result."
            user_content = f"Instruction: {prompt_instruction}\n\nText:\n{text}"
            
        elif mode == "explain":
            system_instruction = "You are an expert technical educator. Explain the selected text or code clearly and concisely. Do not explain what you are doing, just provide the explanation."
            user_content = text
            
        else:
            system_instruction = "Process the following text:"
            user_content = text

        # Using 'gemini-2.5-flash' as requested.
        # We prepend system instruction to user prompt as requested.
        full_prompt = f"{system_instruction}\n\n{user_content}"
        
        model = self.client.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(full_prompt)
        
        return response.text.strip()

    def _call_groq(self, text, mode, prompt_instruction):
        system_prompt = ""
        user_prompt = ""
        
        if mode == "commander":
            system_prompt = (
                "You are a helpful AI assistant integrated into the user's OS. "
                "Execute the user's specific instruction on the provided text. "
                "Output ONLY the result. Do not add quotes around the result unless requested."
            )
            user_prompt = f"Instruction: {prompt_instruction}\n\nText to process:\n{text}"
            
        elif mode == "explain":
            system_prompt = (
                "You are an expert technical educator. Explain the selected text or code clearly and concisely. "
                "Do not explain what you are doing, just provide the explanation."
            )
            user_prompt = f"Explain this:\n\n{text}"

        completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama3-70b-8192", # Groq's fast model
            temperature=0.3, # Low temp for deterministic edits
            max_tokens=1024,
            top_p=1,
            stop=None,
            stream=False,
        )

        return completion.choices[0].message.content.strip()
