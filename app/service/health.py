from pydantic import BaseModel, Field
from app.llms.openai import LangchainOpenaiJsonEngine
from app.service.geo import get_place_info
from app.mongo.fsq_handlers import HEALTH_DATA_HANDLER, ALERT_HANDLER
from datetime import datetime
import os
import numpy as np  
import requests

from pydantic import BaseModel, Field

class ScenarioMentioned(BaseModel):
    """
    Model to capture if a scenario with actual address or name of place is mentioned.
    """
    is_address: bool = Field(..., description="True if input is address, False if lat/lon")
    destination: str = Field(..., description="Address of the destination")

class InferredScenario(BaseModel):
    """
    Model to capture inferred scenario details.
    """
    is_decidable: bool = Field(..., description="True if scenario can be decided, False otherwise")
    altitude_m: float = Field(..., description="Estimated altitude in meters considering existing knowledge")
    temperature_C: dict = Field(..., description="Estimated avg temperature in Celsius considering existing knowledge")


class HealthAlert(BaseModel):
    """
    Model to capture health alert details.
    """
    is_severe: bool = Field(..., description="True if alert is severe, False otherwise")
    alert_title: str = Field(..., description="Title of health alert, e.g., 'High Heart Rate', 'Low O2 Saturation'")
    severity: str = Field(..., description="Severity of the alert, e.g., 'low', 'medium', 'high'")
    message: str = Field(..., description="Detailed message about the alert")
    medical_advice: str = Field(..., description="Medical advice or recommendations")
    carry_medication: str = Field(..., description="Which precautionary medication to carry, if any")

class HealthAlertGenerator:
    def __init__(self):
        self.llm_engine_0 = LangchainOpenaiJsonEngine(
            model_name="gpt-4o-mini",
            systemPromptText="""You are an helpful assistant that extracts structured information from user queries. 
Your task is to identify if the user has mentioned location (address) and extract it.
User may mention places like cities, tourist spots, landmarks, or specific addresses.
            """,
            sampleBaseModel=ScenarioMentioned,
            temperature=0.2
        )

        self.llm_engine_1 = LangchainOpenaiJsonEngine(
            model_name="gpt-4o-mini",
            systemPromptText="""You are an expert assistant that infers scenario details based on location and date. 
Like if user says they are going to a high altitude place in winter, you should infer low temperature and high altitude out of common knowledge.
            """,
            sampleBaseModel=InferredScenario,
            temperature=0.2
        )

        self.llm_engine_2 = LangchainOpenaiJsonEngine(
            model_name="gpt-4o-mini",
            systemPromptText="""You are a medical expert assistant that generates health alerts based on user data and smart device readings. 
You should consider factors like heart rate, oxygen saturation, altitude, temperature, and user health conditions to determine if there are any health risks. 
Generate alerts with severity levels and medical advice accordingly.
Risk is consdered if 
- Metric is outside normal range (e.g., high heart rate, low O2 saturation)
- High variance in readings compared to the average etc
- While suggesting medical advice, consider common medications like aspirin, acetaminophen etc which can be bought over the counter. Don't suggest prescription drugs.
            """,
            sampleBaseModel=HealthAlert,
            temperature=0.2
        )

        self.health_data_handler = HEALTH_DATA_HANDLER
        self.alert_handler = ALERT_HANDLER


    def get_closest_health_data(self, user_id: str, temp: float, altitude: float):
        analysis = self.health_data_handler.analyze_health_data(
            user_id,
            start_time=datetime(2020,10,1,6,0,0),
            end_time=datetime(2027,10,1,8,0,0)
        )
        # Find closest buckets
        closest = {}
        for factor in ["temperature", "altitude"]: 
            if factor not in analysis:
                continue
            buckets = list(analysis[factor].keys())
            if not buckets:
                continue
            buckets = [float(b) for b in buckets]
            if factor == "temperature":
                bucket_size = 5
                target = int(np.floor(temp / bucket_size) * bucket_size)
            elif factor == "altitude":
                bucket_size = 10
                target = int(np.floor(altitude / bucket_size) * bucket_size)
            closest_bucket_index = np.argmin([abs(b - target) for b in buckets])
            closest_bucket = buckets[closest_bucket_index]
            closest[factor] = {
                "bucket": closest_bucket,
                "stats": analysis[factor][closest_bucket]
            }
        return closest
    
    def format_scenario_info(self, info: dict):
        if not info:
            return "No scenario information available."

        details = []
        details.append(f"Location: {info.get('address', 'Unknown')}")
        details.append(f"Latitude: {info.get('lat', 'Unknown')}, Longitude: {info.get('lon', 'Unknown')}")
        details.append(f"Altitude: {info.get('altitude_m', 'Unknown')} meters")
        details.append(f"Estimated Temperature: {info.get('temperature_C', 'Unknown')} °C")

        closest_health = info.get('closest_health_data', {})
        for factor, data in closest_health.items():
            unit = "°C" if factor == "temperature" else "meters"
            details.append(f"\nHealth data closest to {factor} bucket {data.get('bucket', 'N/A')} {unit}:")
            stats = data.get('stats', {})
            for metric, metric_stats in stats.items():
                if metric_stats:
                    details.append(f"  {metric}: Mean={metric_stats['mean']}, Max={metric_stats['max']}, Min={metric_stats['min']}, Var={metric_stats['var']}")

        return "\n".join(details)
    

    def push_health_alert(self, user_id: str, alert: HealthAlert):
        timestamp = datetime.utcnow()
        title = alert["alert_title"]
        severity = alert["severity"]
        description = alert["message"]+"\n Advice: "+alert["medical_advice"]+"\n\n Medication: "+alert["carry_medication"]
        metadata = {
            "type": "health",
            "title": title,
            "description": description,
            "severity": severity.lower()
        }
        
        self.alert_handler.add_alert(user_id, timestamp, metadata)

    def push_pharmacy_alert(self, user_id: str, lat: float, lon: float, alert: str):
        foursquare_microservice_url = os.getenv("FOURSQUARE_MICROSERVICE_URL","http://13.126.242.38:5000/api/foursquare/search?query=pharmacy&ll={lat},{lon}&radius=100")
        foursquare_microservice_url = foursquare_microservice_url.format(lat=lat, lon=lon)
        try:
            response = requests.get(foursquare_microservice_url)
            if response.status_code != 200:
                print("Failed to fetch nearby pharmacies")
                return
            data = response.json()
            results = data["results"][:2]
            for r in results:
                name = r.get("name")
                location = r.get("location", {})
                location_str = ",\n".join(f"{k}: {v}" for k, v in location.items() if v)
                tel = r.get("tel", "N/A")
                website = r.get("website", "N/A")
                latitude, longitude = r.get("latitude"), r.get("longitude")
                metadata = {
                    "type": "pharmacy",
                    "title": f"Nearby Pharmacy: {name}",
                    "description": f"{name}\nLocation:\n{location_str}\nContact: {tel}\nWebsite: {website}\n\nHealth Alert: {alert}",
                    "severity": "medium",
                    "latitude": latitude,
                    "longitude": longitude
                }
                print("Pushing pharmacy alert:", metadata)
                self.alert_handler.add_alert(user_id, datetime.utcnow().isoformat(), metadata)
        except Exception as e:
            print("Error fetching pharmacies:", str(e))
            return


    def run(self, user_id:str, user_input: str):
        # Step 1: Extract location information
        result = self.llm_engine_0.run(user_input)[0]
        print(result)
        if not result['is_address'] and not result['destination']:
            print("No address mentioned, cannot infer scenario.")
            # result = self.llm_engine_1.run(result)
            # if result['is_decidable']:
            return {}
            
        today = datetime.utcnow().strftime("%Y-%m-%d")
        # Step 2: Infer scenario details
        fetched_info = get_place_info(result['destination'], 
                                      os.getenv("GOOGLE_MAPS_API_KEY"),
                                       date=today,
                                        use_google_elevation=True)
        print("Fetched place info:", fetched_info)
        if not fetched_info:
            print("Failed to fetch place info")
            return {}
        
        closest_health_data = self.get_closest_health_data(user_id, 
                                                        fetched_info['temperature_C'], 
                                                        fetched_info['altitude_m'])
        fetched_info['closest_health_data'] = closest_health_data
        print("Closest health data found")
        formatted_info = self.format_scenario_info(fetched_info)
        alert = self.llm_engine_2.run(f"""Based on the following scenario details and user health data, generate any necessary health alerts with severity and medical advice.
Health metrics analysis report:
{formatted_info}

User is saying: {user_input}
        """)[0]
        print("=== Scenario Details ===")
        print(formatted_info)
        print("\n=== Health Alert ===")
        print(alert)

        self.push_health_alert(user_id, alert)
        
        self.push_pharmacy_alert(user_id, fetched_info['lat'], fetched_info['lon'], alert['message'])

        return {
            "lat": fetched_info['lat'],
            "lon": fetched_info['lon'],
            "scenario_details": formatted_info,
            "health_alert": alert
        }
    


HEALTH_ALERT_GENERATOR = HealthAlertGenerator()