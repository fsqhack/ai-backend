import requests
import os
from PIL import Image  # <-- fix import here
import base64
import json
from sklearn.metrics.pairwise import cosine_similarity


class TasteAnalyzer:
    def __init__(self):
        # https://fsq-emb-server-20555262314.us-central1.run.app
        self.clip_img_emb_endpoint = "https://fsq-emb-server-20555262314.us-central1.run.app/clip/embed-images"
        self.clip_txt_emb_endpoint = "https://fsq-emb-server-20555262314.us-central1.run.app/clip/embed-texts"
        self.openai_txt_emb_endpoint = "https://fsq-emb-server-20555262314.us-central1.run.app/openai/embed-texts"

        self.traits_file = "app/data/travel-traits.json"
        self.load_traits()

    def load_traits(self):
        """
        Traits file format:
        {
            "travel-locations": [
                "Green Mountains",
                "Sandy Beaches",
                ...
            ],
            "travel-activities": [
                "Hiking",
                "Museum Visits",
                ...
            ],
            ...
        }
        """
        with open(self.traits_file, "r") as f:
            traits_data = json.load(f)

        # Check if trait embeddings file already exists
        if os.path.exists("app/data/trait-embeddings.json"):
            with open("app/data/trait-embeddings.json", "r") as f:
                self.trait_embeddings = json.load(f)
            return
        # Generate embeddings for each trait category
        self.trait_embeddings = {}
        for category, traits in traits_data.items():
            openai_embeddings = self.get_text_embeddings(traits, model="openai")
            clip_embeddings = self.get_text_embeddings(traits, model="clip")
            self.trait_embeddings[category] = {
                "traits": traits,
                "embeddings": {
                    "openai": openai_embeddings,
                    "clip": clip_embeddings
                }
            }
        # Save trait embeddings to a file for reference
        with open("app/data/trait-embeddings.json", "w") as f:
            json.dump(self.trait_embeddings, f, indent=2)
    
    def get_image_embeddings(self, user_id):
        folder_path = f"tmp/images/{user_id}/"
        # Read all images from the folder
        image_files = [
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f))
        ]

        images_base64 = []
        for img_file in image_files:
            # Resize image to 224x224
            Image.open(img_file).resize((224, 224)).save(img_file)
            with open(img_file, "rb") as f:
                img_bytes = f.read()
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                images_base64.append(img_b64)

        # Send request to embedding service
        response = requests.post(
            self.clip_img_emb_endpoint,
            json={"images": images_base64}
        )

        if response.status_code != 200:
            raise RuntimeError(f"Error from embedding service: {response.text}")

        return response.json().get("embeddings", [])
        

    def get_text_embeddings(self, texts, model="openai"):
        if model == "clip":
            response = requests.post(self.clip_txt_emb_endpoint, json={"texts": texts})
        else:
            response = requests.post(self.openai_txt_emb_endpoint, json={"texts": texts})
        if response.status_code == 200:
            return response.json().get("embeddings", [])
        else:
            return []
        
    def analyze_user_taste(self, user_id, text):
        # Assigns scores to each trait based on text and image embeddings
        # While doing img-text then consider clip embeddings 
        # While doing only text then consider openai embeddings
        text_embedding = self.get_text_embeddings([text], model="openai")[0]
        image_embeddings = self.get_image_embeddings(user_id)
        
        trait_scores = {}
        for category, data in self.trait_embeddings.items():
            traits = data["traits"]
            openai_embeddings = data["embeddings"]["openai"]
            clip_embeddings = data["embeddings"]["clip"]

            # Text-based scores using OpenAI embeddings
            text_similarities = cosine_similarity(
                [text_embedding], openai_embeddings
            )[0]
            text_scores = {trait: float(score) for trait, score in zip(traits, text_similarities)}
            # Image-based scores using CLIP embeddings
            if image_embeddings:
                img_similarities = cosine_similarity(
                    image_embeddings, clip_embeddings
                )
                img_scores_avg = img_similarities.max(axis=0)
                img_scores = {trait: float(score) for trait, score in zip(traits, img_scores_avg)}
            else:
                img_scores = {trait: 0.0 for trait in traits}

            # Combine text and image scores (weighted average)
            combined_scores = {}
            for trait in traits:
                combined_scores[trait] = {
                    "text_score": text_scores.get(trait, 0.0),
                    "image_score": img_scores.get(trait, 0.0)
                }

            trait_scores[category] = combined_scores

        # Normalize and combine scores
        for category, scores in trait_scores.items():
            max_text_score = max(score_data["text_score"] for score_data in scores.values()) or 1.0
            max_img_score = max(score_data["image_score"] for score_data in scores.values()) or 1.0

            for trait, score_data in scores.items():
                norm_text_score = score_data["text_score"] / max_text_score
                norm_img_score = score_data["image_score"] / max_img_score
                combined_score = 0.6 * norm_text_score + 0.4 * norm_img_score
                score_data["text_score"] = norm_text_score
                score_data["image_score"] = norm_img_score
                score_data["combined_score"] = combined_score
                trait_scores[category][trait] = score_data

        # Sort traits within each category by combined score
        for category in trait_scores:
            trait_scores[category] = dict(
                sorted(
                    trait_scores[category].items(),
                    key=lambda item: item[1]["combined_score"],
                    reverse=True
                )
            )

        return trait_scores