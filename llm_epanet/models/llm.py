import sys
from openai import OpenAI
from llm_epanet.utils.settings import OPENROUTER_API_KEY, OPENROUTER_API_BASE, ANTHROPIC_API_KEY, ANTHROPIC_LARGE_MODEL
import anthropic
from llm_epanet.utils.logger import logger

class LanguageModel:
    def __init__(self, model_name: str,
                 temperature: float = 1.0, 
                 openrouter_api_key: str=OPENROUTER_API_KEY, 
                 openrouter_api_base: str=OPENROUTER_API_BASE,
                 **kwargs):
        try:
            self.client = OpenAI(
                base_url=openrouter_api_base,
                api_key=openrouter_api_key,
            )
            self.model_name = model_name
            self.temperature = temperature
            self.kwargs = kwargs
        except Exception as e:
            logger.error(f"Failed to initialize LanguageModel: {str(e)}")
            raise

    def ask(self, prompt: str = None, temperature: float = None):
        logger.debug("Asking OpenRouter API")
        logger.debug(f"Prompt:\n{prompt}")
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                    "role": "user",
                    "content": prompt
                    }
                ],
                extra_body={
                        "usage": {
                            "include": True
                        }
                    }
            )
            return completion.choices[0].message.content, getattr(completion, "usage", None)
        except Exception as e:
            logger.error(f"OpenRouter API call failed, falling back to Anthropic: {str(e)}")
            sys.exit(-1)
            return self.ask_anthropic(prompt, temperature)

    def ask_anthropic(self, prompt: str = None, temperature: float = None):
        """ Try to ask the Anthropic API if the OpenRouter API fails """
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            completion = client.messages.create(
                model=ANTHROPIC_LARGE_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.content[0].text, None
        except Exception as e:
            logger.error(f"Anthropic API call failed: {str(e)}")
            raise
    
    def clean_response(self, response):
        try:
            response = response.split("```python")[1].split("```")[0]
        except Exception as e:
            logger.debug(f"Failed to clean response, returning original: {str(e)}")
            pass

        # Strip single backticks (inline code formatting)
        response = response.strip().strip('`')
        return response
    
    def __call__(self, prompt: str):
        try:
            res, usage = self.ask(prompt)
            res = self.clean_response(res)
            return res, usage
        except Exception as e:
            logger.error(f"Failed to process prompt: {str(e)}")
            raise
