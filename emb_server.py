from flask import Flask, request, jsonify
# from transformers import CLIPProcessor, CLIPModel
# import torch
# from PIL import Image
# import io
# import base64

import os
import numpy as np
from typing import Dict
from dotenv import load_dotenv
load_dotenv()


# class CLIPEmbedder:
#     """
#     A wrapper around CLIP model to generate embeddings for text and images.
#     """

#     def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
#         self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#         self.model = CLIPModel.from_pretrained(model_name).to(self.device)
#         self.processor = CLIPProcessor.from_pretrained(model_name)
#         self.model.eval()

#     def embed_texts(self, texts):
#         """
#         Generate embeddings for a list of texts.
#         """
#         if isinstance(texts, str):
#             texts = [texts]

#         inputs = self.processor(text=texts, return_tensors="pt", padding=True).to(self.device)

#         with torch.no_grad():
#             embeddings = self.model.get_text_features(**inputs)

#         return embeddings.cpu().tolist()

#     def embed_images(self, images):
#         """
#         Generate embeddings for a list of images.
#         Images can be base64 strings or PIL Images.
#         """
#         processed_images = []
#         for img in images:
#             if isinstance(img, str):  # assume base64
#                 img = Image.open(io.BytesIO(base64.b64decode(img))).convert("RGB")
#             processed_images.append(img)

#         inputs = self.processor(images=processed_images, return_tensors="pt").to(self.device)

#         with torch.no_grad():
#             embeddings = self.model.get_image_features(**inputs)

#         return embeddings.cpu().tolist()


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


# Initialize
# CLIP_EMBEDDER = CLIPEmbedder()
OPENAI_EMBEDDER = OpenAIEmbedder()  # Initialize the embedder instance
app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Embedding Server is running!"})

# CLIP Embedder Endpoints
@app.route("/clip/", methods=["GET"])
def home():
    return jsonify({"message": "CLIP Embedder is running!"})


# @app.route("/clip/embed-texts", methods=["POST"])
# def embed_texts():
#     data = request.json
#     texts = data.get("texts", None)

#     if not texts:
#         return jsonify({"error": "No texts provided"}), 400

#     embeddings = CLIP_EMBEDDER.embed_texts(texts)
#     return jsonify({"embeddings": embeddings})


# @app.route("/clip/embed-images", methods=["POST"])
# def embed_images():
#     data = request.json
#     images = data.get("images", None)

#     if not images:
#         return jsonify({"error": "No images provided"}), 400

#     embeddings = CLIP_EMBEDDER.embed_images(images)
#     return jsonify({"embeddings": embeddings})

# OpenAI Embedder Endpoint
@app.route("/openai/", methods=["GET"])
def openai_home():
    return jsonify({"message": "OpenAI Embedder is running!"})

@app.route("/openai/embed-texts", methods=["POST"])
def openai_embed():
    data = request.json
    texts = data.get("texts", None)

    if not texts:
        return jsonify({"error": "No texts provided"}), 400

    embeddings = OPENAI_EMBEDDER(texts)
    # Convert numpy arrays to lists for JSON serialization
    if isinstance(embeddings, np.ndarray):
        embeddings = embeddings.tolist()
    else:
        embeddings = [emb.tolist() for emb in embeddings]

    return jsonify({"embeddings": embeddings})  




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
