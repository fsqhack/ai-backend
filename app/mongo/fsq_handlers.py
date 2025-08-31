from random import sample
from app.mongo.base_handler import BaseMongoHandler
from app.service.taste_analysis import TasteAnalyzer
from app.service.geo import get_temperature
import os
from collections import defaultdict
import numpy as np


class UserHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__('users')
        self.taste_analyzer = TasteAnalyzer()

    def add_user(self, user_data):
        """
        Sample user_data:
        {
            "user_id": "user123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "123-456-7890",
        }
        """
        user_data['taste_groups'] = {}

        # if same user_id exists, then replace
        existing_user = self.collection.find_one({"user_id": user_data["user_id"]})
        if existing_user:
            self.collection.delete_one({"user_id": user_data["user_id"]})
        response = self.collection.insert_one(user_data)
        return response
    
    def add_taste_group(self, user_id, taste_text):
        """
        Adds a new taste group for the user.
        taste_text: A descriptive text about the user's travel preferences.
        """
        # Sanity check (user_id exists and taste_text is non-empty and tmp/images/user_id/ has images)
        user = self.collection.find_one({"user_id": user_id})
        if not user:
            return {"error": "User not found."}
        if not taste_text or not taste_text.strip():
            return {"error": "Taste text is empty."}
        img_folder = f"tmp/images/{user_id}/"
        if not os.path.exists(img_folder) or not os.listdir(img_folder):
            return {"error": "No images found for the user."}
        
        taste_scores = self.taste_analyzer.analyze_user_taste(user_id, taste_text)
        # Category -> Sub-category -> score
        category_wise_traits = {}
        for category, scores in taste_scores.items():
            traits = {trait: score_data["combined_score"] for trait, score_data in scores.items() if score_data["combined_score"] > 0.5}
            if traits:
                category_wise_traits[category] = traits
        if not category_wise_traits:
            return {"error": "No significant traits found."}
        response = self.collection.update_one(
            {"user_id": user_id},
            {"$set": {f"taste_groups.{len(category_wise_traits)}": category_wise_traits}}
        )
        return response
    




class TripHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__('trips')

    def add_trip(self, trip_data):
        """
        Sample trip_data:
        {
            "trip_id": "trip123",
            "trip_name": "Weekend in SF",
            "user_ids": ["user123"],
            "context": "Going for a leisure trip to San Francisco on 1st Oct 2025",
            "metadata": {
                "start_lat": 37.7749,
                "start_lng": -122.4194,
                "start_time": "2023-10-01T10:00:00Z",
                "explosure": "medium",
                "type": "leisure"
            }
        }
        """
        trip_data["pending_invites"] = []
        # if same trip_id exists, then replace
        existing_trip = self.collection.find_one({"trip_id": trip_data["trip_id"]})
        if existing_trip:
            self.collection.delete_one({"trip_id": trip_data["trip_id"]})
        response = self.collection.insert_one(trip_data)
        return response
    
    def add_invite(self, trip_id, user_id):
        """
        Add a user to the pending invites of a trip after checking if they are already invited.
        """
        trip = self.collection.find_one({"trip_id": trip_id})
        if not trip:
            return {"error": "Trip not found"}

        if user_id in trip.get("pending_invites", []):
            return {"message": "User already invited"}
        
        if user_id in trip.get("user_ids", []):
            return {"message": "User already part of the trip"}

        self.collection.update_one(
            {"trip_id": trip_id},
            {"$push": {"pending_invites": user_id}}
        )
        return {"message": "User invited successfully"}
    
    def approve_invite(self, trip_id, approver_id, invitee_id):
        """
        Approve a trip invite by moving the user from pending_invites to user_ids.
        """
        trip = self.collection.find_one({"trip_id": trip_id})
        if not trip:
            return {"error": "Trip not found"}

        if approver_id not in trip.get("user_ids", []):
            return {"error": "Approver is not part of the trip"}

        if invitee_id not in trip.get("pending_invites", []):
            return {"error": "Invitee not in pending invites"}

        self.collection.update_one(
            {"trip_id": trip_id},
            {
                "$pull": {"pending_invites": invitee_id},
                "$push": {"user_ids": invitee_id}
            }
        )
        return {"message": "Invite approved successfully"}
    
    def deny_invite(self, trip_id, approver_id, invitee_id):
        """
        Deny a trip invite by removing the user from pending_invites.
        """
        trip = self.collection.find_one({"trip_id": trip_id})
        if not trip:
            return {"error": "Trip not found"}

        if approver_id not in trip.get("user_ids", []):
            return {"error": "Approver is not part of the trip"}

        if invitee_id not in trip.get("pending_invites", []):
            return {"error": "Invitee not in pending invites"}

        self.collection.update_one(
            {"trip_id": trip_id},
            {"$pull": {"pending_invites": invitee_id}}
        )
        return {"message": "Invite denied successfully"}

    def view_invites(self, trip_id, user_id):
        """
        View all pending invites for a trip.
        """
        trip = self.collection.find_one({"trip_id": trip_id})
        if not trip:
            return {"error": "Trip not found"}

        if user_id not in trip.get("user_ids", []):
            return {"error": "User is not part of the trip"}

        return {"pending_invites": trip.get("pending_invites", [])}
    
    def view_members(self, trip_id, user_id):
        """
        View all members of a trip.
        """
        trip = self.collection.find_one({"trip_id": trip_id})
        if not trip:
            return {"error": "Trip not found"}

        if user_id not in trip.get("user_ids", []):
            return {"error": "User is not part of the trip"}

        return {"members": trip.get("user_ids", [])}
    




class HealthDataHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__(collection_name="health_data")

    def add_health_data(self, user_id, health_data):
        """
        Add health data for a user.
        Sample health_data format:
        {
            "point_id": "point-1",
            "trip_id": "trip-1",
            "user_id": "user-1",
            "timestamp": "2023-10-01T10:00:00Z",
            "data":{
                "latitude": 37.7749,
                "longitude": -122.4194,
                "altitude": 30.0,
                "speed_x": 0.5,
                "speed_y": 0.1,
                "speed_z": 0.0,
                "heart_rate": 72,
                "calories_burned": 150,
                "o2_saturation": 98,
                "distance_traveled": 1.2
            }
        }
        """
        health_data["user_id"] = user_id
        # if same point_id exists for the user, then replace
        existing_data = self.collection.find_one({"point_id": health_data["point_id"], "user_id": user_id})
        if existing_data:
            self.collection.delete_one({"point_id": health_data["point_id"], "user_id": user_id})
        self.collection.insert_one(health_data)
        return {"message": "Health data added successfully"}
    
    def _bucketize(self, value, bucket_size):
        """Floor value into its bucket."""
        return int(np.floor(value / bucket_size) * bucket_size)

    def _compute_stats(self, values):
        """Compute mean, max, min, variance for a list of values."""
        if not values:
            return None
        arr = np.array(values)
        return {
            "mean": float(np.mean(arr)),
            "max": float(np.max(arr)),
            "min": float(np.min(arr)),
            "var": float(np.var(arr))
        }
    
    def get_health_data(self, user_id, trip_id):
        """
        Retrieve all health data for a user in a specific trip.
        """
        records = list(self.collection.find({
            "user_id": user_id,
            "trip_id": trip_id
        }))
        return records

    def analyze_health_data(self, user_id, start_time, end_time):
        """
        Analyze health data for a user in the given time range.
        Creates bucketed mappings of (temp, altitude, speed_xy, speed_z) → health stats.
        """
        # Query only relevant records
        records = list(self.collection.find({
            "user_id": user_id,
            # "timestamp": {"$gte": start_time, "$lte": end_time}
        }))
        print(f"Found {len(records)} records for user {user_id} between {start_time} and {end_time}")

        # Use defaultdict for metrics per bucket
        factor_buckets = {
            "temperature": defaultdict(lambda: defaultdict(list)),
            "altitude": defaultdict(lambda: defaultdict(list)),
            "speed_xy": defaultdict(lambda: defaultdict(list)),
            "speed_z": defaultdict(lambda: defaultdict(list))
        }

        # Precompute bucketization factors
        bucket_sizes = {
            "temperature": 5,
            "altitude": 10,
            "speed_xy": 5*5/18,
            "speed_z": 5*5/18
        }
        # randomly sample 10 records
        sampled_records = sample(records, min(len(records), 10))
        
        for rec in sampled_records:
            print(f"Processing record: {rec.get('point_id')}")
            data = rec.get("data")
            if not data:
                continue

            lat, lon, ts = data.get("latitude"), data.get("longitude"), rec.get("timestamp")
            temp = get_temperature(lat, lon, ts)
            speed_x, speed_y, speed_z_val = data.get("speed_x", 0), data.get("speed_y", 0), data.get("speed_z", 0)
            speed_xy = np.hypot(speed_x, speed_y)
            altitude = data.get("altitude", 0)
            speed_z_abs = abs(speed_z_val)

            # Bucket values
            buckets = {
                "temperature": self._bucketize(temp, bucket_sizes["temperature"]),
                "altitude": self._bucketize(altitude, bucket_sizes["altitude"]),
                "speed_xy": self._bucketize(speed_xy, bucket_sizes["speed_xy"]),
                "speed_z": self._bucketize(speed_z_abs, bucket_sizes["speed_z"])
            }

            # Health metrics
            metrics = {
                "heart_rate": data.get("heart_rate"),
                "calories_burned": data.get("calories_burned"),
                "o2_saturation": data.get("o2_saturation")
            }

            # Collect metrics per bucket
            for factor, bucket in buckets.items():
                for metric, value in metrics.items():
                    if value is not None:
                        factor_buckets[factor][bucket][metric].append(value)

        # Compute stats per bucket
        results = {}
        for factor, buckets in factor_buckets.items():
            results[factor] = {
                bucket: {
                    f"{metric}_stats": self._compute_stats(values)
                    for metric, values in metrics.items()
                } if metrics else None
                for bucket, metrics in buckets.items()
            }

        return results


class AlertHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__(collection_name="alerts")
        
    def add_alert(self, user_id, timestamp, metadata):
        """
        Sample metadata format:
        {
            "type": "health", # Mandatory
            "title": "High Heart Rate Alert", # Mandatory
            "description": "Your heart rate exceeded 120 bpm during trekking.", # Mandatory
            "severity": "high", # Mandatory: low, medium, high
            "latitude": 27.98, # Optional
            "longitude": 86.92, # Optional
        }
        """
        alert = {
            "alert_id": f"alert-{user_id}-{timestamp}",
            "user_id": user_id,
            "timestamp": timestamp,
            "metadata": metadata
        }
        
        allowed_types = ['health', 'pharmacy', 'restaurant', 'gym', 'location']
        if metadata.get('type') not in allowed_types:
            return {"error": f"Invalid alert type. Allowed types: {allowed_types}"}
        allowed_severities = ['low', 'medium', 'high']
        if metadata.get('severity') not in allowed_severities:
            return {"error": f"Invalid severity level. Allowed levels: {allowed_severities}"}

        existing_alert = self.collection.find_one({"alert_id": alert["alert_id"]})
        if existing_alert:
            self.collection.delete_one({"alert_id": alert["alert_id"]})
        self.collection.insert_one(alert)
        return {"message": "Alert added successfully"}

    def get_by_user_id(self, user_id):
        alerts = list(self.collection.find({"user_id": user_id}))
        return alerts






USER_HANDLER = UserHandler()
TRIP_HANDLER = TripHandler()
HEALTH_DATA_HANDLER = HealthDataHandler()
ALERT_HANDLER = AlertHandler()