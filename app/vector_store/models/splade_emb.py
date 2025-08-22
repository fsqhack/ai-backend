# from transformers import AutoTokenizer, AutoModelForMaskedLM
# import torch
# from typing import Dict, Union


# class SPLADEEmbedder:
#     """
#     Callable class to generate sparse embeddings using a SPLADE model.
#     Usage:
#         embedder = SPLADEEmbedder()
#         sparse_vector = embedder("sample text")
#     """

#     def __init__(self, model_name: str = "naver/splade-cocondenser-ensembledistil"):
#         self.tokenizer = AutoTokenizer.from_pretrained(model_name)
#         self.model = AutoModelForMaskedLM.from_pretrained(model_name)
#         self.model.eval()
#         self.torch = torch

#     def __call__(self, text):
#         """
#         Accepts a string or a list of strings.
#         Returns a sparse dict for a single string, or a list of sparse dicts for a list of strings.
#         """
#         import torch.nn.functional as F

#         if isinstance(text, str):
#             with self.torch.no_grad():
#                 inputs = self.tokenizer(text, return_tensors="pt")
#                 outputs = self.model(**inputs).logits.squeeze(0)
#                 mask = inputs["attention_mask"].squeeze(0)

#                 scores = self.torch.log(1 + self.torch.relu(outputs)).sum(0) * mask.unsqueeze(1)
#                 scores = F.softmax(scores.sum(0), dim=0)

#                 sparse_dict = {
#                     int(i): float(v)
#                     for i, v in enumerate(scores)
#                     if v > 1e-5
#                 }
#             return sparse_dict
#         elif isinstance(text, list) and all(isinstance(t, str) for t in text):
#             sparse_dicts = []
#             with self.torch.no_grad():
#                 inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
#                 outputs = self.model(**inputs).logits
#                 masks = inputs["attention_mask"]
#                 for i in range(outputs.shape[0]):
#                     out = outputs[i]
#                     mask = masks[i]
#                     scores = self.torch.log(1 + self.torch.relu(out)).sum(0) * mask.unsqueeze(1)
#                     scores = F.softmax(scores.sum(0), dim=0)
#                     sparse_dict = {
#                         int(j): float(v)
#                         for j, v in enumerate(scores)
#                         if v > 1e-5
#                     }
#                     sparse_dicts.append(sparse_dict)
#             return sparse_dicts
#         else:
#             raise TypeError("Input must be a string or a list of strings.")


# SPLADE_EMBEDDER = SPLADEEmbedder()  # Initialize the embedder instance