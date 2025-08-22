from pymongo import MongoClient
from app.vector_store.models.openai_emb import OPENAI_EMBEDDER
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from dotenv import load_dotenv
load_dotenv()




class BaseMongoHandler:
    def __init__(self, collection_name):
        self.client = MongoClient(os.environ['MONGO_DB_URI'])
        self.db_name = "capital_one_db"
        self.db = self.client[self.db_name]
        self.collection = self.db[collection_name]

    def add_item(self, item, unique_field, vector_fields=None):
        """
        Adds an item to the database with optional embedding generation.
        
        Args:
            item (dict): The item to add.
            unique_field (str): Field name that must be unique.
            vector_fields (list): List of text fields to combine for embedding.
        """
        # if self.collection.find_one({unique_field: item[unique_field]}):
        #     raise ValueError(f"Item with {unique_field} '{item[unique_field]}' already exists.")

        if vector_fields:
            combined_text = " ".join(item[field] for field in vector_fields if field in item)
            item_vector = OPENAI_EMBEDDER(combined_text).tolist()
            item['vector'] = item_vector

        self.collection.insert_one(item)
        return item

    def get_by_id(self, unique_field, value):
        return self.collection.find_one({unique_field: value})

    def get_all(self):
        return list(self.collection.find())
    
    def get_by_query(self, query):
        """
        Retrieves items from the collection based on a query.
        
        Args:
            query (dict): The query to filter items.
        Example:
            query = {"field_name": "value"}
        
        Returns:
            list: List of items matching the query.
        """
        return list(self.collection.find(query))
    
    def update_by_id(self, unique_field, value, update_fields):
        """
        Updates an item in the collection by its unique field.
        
        Args:
            unique_field (str): The field that uniquely identifies the item.
            value: The value of the unique field to identify the item.
            update_fields (dict): The fields to update.
        
        Returns:
            dict: The updated item.
        """
        result = self.collection.find_one_and_update(
            {unique_field: value},
            {'$set': update_fields},
            return_document=True
        )
        return result

    def delete_by_id(self, unique_field, value):
        result = self.collection.delete_one({unique_field: value})
        return result.deleted_count
    
    def delete_by_query(self, query):
        """
        Deletes items from the collection based on a query.
        
        Args:
            query (dict): The query to filter items for deletion.
        
        Returns:
            int: Number of deleted items.
        """
        result = self.collection.delete_many(query)
        return result.deleted_count

    def delete_all(self):
        result = self.collection.delete_many({})
        return result.deleted_count > 0

    def search(self, query, vector_field='vector', similarity_threshold=0.5):
        query_vector = OPENAI_EMBEDDER(query)
        items = self.collection.find()
        results = []
        for item in items:
            if vector_field in item:
                item_vector = np.array(item[vector_field]).reshape(1, -1)
                similarity = cosine_similarity(query_vector.reshape(1, -1), item_vector)[0][0]
                results.append((item, similarity))
        results.sort(key=lambda x: x[1], reverse=True)
        return [item for item, sim in results if sim > similarity_threshold]