import os
import numpy as np
from typing import Dict
from dotenv import load_dotenv
load_dotenv()


# Check if OPENAI_API_KEY is set
if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")


class OpenAIEmbedder:
    """
    Callable class to generate dense embeddings using OpenAI's embedding API.
    Usage:
        embedder = OpenAIEmbedder()
        vector = embedder("sample text")
    """

    def __init__(self, model: str = "text-embedding-ada-002"):
        import openai
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        self.openai = openai
        self.model = model

    def __call__(self, text):
        """
        Accepts a string or a list of strings.
        Returns a numpy array for a single string, or a list of numpy arrays for a list of strings.
        """
        if isinstance(text, str):
            response = self.openai.embeddings.create(
                model=self.model,
                input=text
            )
            return np.array(response.data[0].embedding)
        elif isinstance(text, list) and all(isinstance(t, str) for t in text):
            response = self.openai.embeddings.create(
                model=self.model,
                input=text
            )
            return [np.array(item.embedding) for item in response.data]
        else:
            raise TypeError("Input must be a string or a list of strings.")

OPENAI_EMBEDDER = OpenAIEmbedder()  # Initialize the embedder instance