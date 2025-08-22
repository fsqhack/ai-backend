# from transformers import AutoImageProcessor, AutoModelForImageClassification
# from PIL import Image

# class PlantDiseaseDetector:
#     def __init__(self, model_name="Diginsa/Plant-Disease-Detection-Project"):
#         self.preprocessor = AutoImageProcessor.from_pretrained(model_name)
#         self.model = AutoModelForImageClassification.from_pretrained(model_name)
#         self.label_map = self.model.config.id2label

#     def predict(self, image_path):
#         image = Image.open(image_path)
#         inputs = self.preprocessor(images=image, return_tensors="pt")
#         outputs = self.model(**inputs)
#         logits = outputs.logits
#         predicted_class_idx = logits.argmax(-1).item()
#         return self.label_map[predicted_class_idx]
