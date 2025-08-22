from sympy import re
from app.mongo.base_handler import BaseMongoHandler
from app.llms.openai import LangchainOpenaiJsonEngine
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

class AgriProductHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__("agri_products")

    def add_product(self, product):
        """
        Add a new product ensuring product_id is unique
        and store vector embedding from description + usage.

        Sample product structure:
        {
            "product_id": "12345",
            "name": "Organic Fertilizer : Urea 222",
            "category": "Fertilizers",
            "price": 25.99,
            "description": "High-quality organic fertilizer for better crop yield.",
            "usage": "Apply 50 kg per hectare before planting.",
            "image_url": "http://example.com/image.jpg",
            "provider": {
                "name": "AgriTech Solutions",
                "contact": "123-456-7890",
                "email": "info@agritechsolutions.com",
                "address": "123 Agri Lane, Farm City, Country"
            }
        }
        """
        return self.add_item(
            item=product,
            unique_field="product_id",
            vector_fields=["description", "usage"]
        )

    def get_product_by_id(self, product_id):
        return self.get_by_id("product_id", product_id)


class AgriServiceHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__("agri_services")

    def add_service(self, service):
        """
        Add a new service ensuring service_id is unique
        and store vector embedding from description + usage.
        
        Sample service structure:
        {
            "service_id": "service_001",
            "name": "Soil Testing Service",
            "description": "Comprehensive soil testing for nutrient levels.",
            "price": 100.00,
            "usage": "Send a soil sample to our lab for analysis.",
            "provider": {
                "name": "AgriLab Services",
                "contact": "987-654-3210",
                "email": "info@agrilabservices.com",
                "address": "456 Lab Road, Research City, Country"
            }
        }
        """
        return self.add_item(
            item=service,
            unique_field="service_id",
            vector_fields=["description", "usage"]
        )

    def get_service_by_id(self, service_id):
        return self.get_by_id("service_id", service_id)
    




def format_suggestions(suggestions):
    """
    Format product and service suggestions for message body.
    """
    lines = []
    date = suggestions.get('date', 'N/A')

    formatted_suggestions = {
        "date": date
    }

    if 'products' in suggestions and suggestions['products']:
        lines.append(f"Product suggestions for {date}:")
        for product in suggestions.get('products', []):
            lines.append(f"- Product Name: {product['product_service'].get('name', '')}")
            lines.append(f"  Category: {product['product_service'].get('category', '')}")
            lines.append(f"  Description: {product['product_service'].get('description', '')}")
            lines.append(f"  Usage: {product['product_service'].get('usage', '')}")
            lines.append(f"  Price: {product['product_service'].get('price', '')}")
            lines.append(f"  Image: {product['product_service'].get('image_url', '')}")
            lines.append(f"  Contact: {product['product_service'].get('provider', '')}")
            lines.append(f"  Why this product is suggested: {product.get('reason', '')}")
        lines.append("")
        formatted_suggestions['products'] = "\n".join(lines)

    if 'services' in suggestions and suggestions['services']:
        lines = []
        lines.append(f"Service suggestions for {date}:")
        for service in suggestions.get('services', []):
            lines.append(f"- Service Name: {service['product_service'].get('name', '')}")
            lines.append(f"  Description: {service['product_service'].get('description', '')}")
            lines.append(f"  Price: {service['product_service'].get('price', '')}")
            lines.append(f"  Provider: {service['product_service'].get('provider', '')}")
            lines.append(f"  Why this service is suggested: {service.get('reason', '')}")
        formatted_suggestions['services'] = "\n".join(lines)

    return formatted_suggestions





class ProductServiceSuggestionHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__("product_service_suggestions")

    def add_suggestions(self, suggestions):
        """
        Add a new product/service suggestion ensuring unique suggestion_id.

        Sample suggestion structure:
        {
            "sensor_hub_id": "hub_001",
            "suggestions": {},
            "timestamp": "2023-10-01T12:00:00Z",
        }
        """
        # print(f"Adding suggestions: {suggestions}")
        formatted_suggestions = format_suggestions(suggestions['suggestions'])
        # print(f"Formatted Suggestions: {formatted_suggestions}")
        if 'products' in formatted_suggestions or 'services' in formatted_suggestions:
            payload = {
                "suggestion_id": f"suggestion_{suggestions.get('sensor_hub_id', '')}_{suggestions.get('timestamp', '')}",
                "sensor_hub_id": suggestions.get('sensor_hub_id', ''),
                "suggestions": formatted_suggestions,
                "timestamp": suggestions.get('timestamp', ''),
                "delivery_status": "pending"  # [ 'pending', 'wap', 'mail' , 'wap+mail']
            }
            return self.add_item(
                item=payload,
                unique_field="suggestion_id"
            )
        else:
            print("No valid product or service suggestions to add.")
        return None
    
    def update_delivery_status(self, suggestion_id: str, delivery_status: str):
        """
        Update the delivery status of a suggestion.
        """
        if not suggestion_id or not delivery_status:
            return False
        result = self.collection.update_one(
            {"suggestion_id": suggestion_id},
            {"$set": {"delivery_status": delivery_status}}
        )
        return result.modified_count > 0
            
    

class BaseRequirements(BaseModel):
    product_requirements: List[str] = Field(title="Agricultural product requirements", description="List of specific product requirements based on alerts which could be needed for compensation for the severity of the alert.")
    service_requirements: List[str] = Field(title="Agricultural service requirements", description="List of specific service requirements based on alerts which could be needed for compensation for the severity of the alert.")

class IsValidCombination(BaseModel):
    is_valid: bool = Field(title="Is Valid Combination", description="Does the product/service combination meet the specific requirements?")
    reason: str = Field(title="Reason", description="Explanation of why the combination is valid or not.")

class AlertStorageHandler(BaseMongoHandler):
    def __init__(self, model_name="gpt-4o-mini", temperature=0.5, 
                 product_handler: AgriProductHandler = None, 
                 service_handler: AgriServiceHandler = None,
                 product_service_suggestion_handler: ProductServiceSuggestionHandler = None):
        self.product_handler = product_handler
        self.service_handler = service_handler
        self.product_service_suggestion_handler = product_service_suggestion_handler
        super().__init__("alerts")
        self.req_engine = LangchainOpenaiJsonEngine(
            model_name=model_name,
            temperature=temperature,
            sampleBaseModel=BaseRequirements,
            systemPromptText="""
You are an expert in agricultural product and service requirements.
Based on the provided alerts, generate a list of product and service requirements.
Each requirement should be a string describing the need.
Instrctions:
   - Give specific requirements based on the alerts , do not give generic requirements. Example: Need to balance nitrogen levels in soil, need to control pest infestations.
   - Do not include any other information or context, just the requirements.
   - The requirements should be brief and to the point.
   - If no requirements can be generated, return an empty list for both product and service requirements.
"""
        )
        self.product_validator_engine = LangchainOpenaiJsonEngine(
            model_name=model_name,
            temperature=temperature,
            sampleBaseModel=IsValidCombination,
            systemPromptText="""You are an expert in validating agricultural product and service combinations.
Given a product/service combination and the requirements. Validate if the combination meets the specific requirements.
Instructions:
    - Only valid if the requirement indicates a specific need that the product/service can address.
    - Valid if the product/service directly solve any one of the requirements specified.
    - Not valid if the requirement is too vague or generic like "improve yield" without specifics.
    - Not valid if the product/service have no relation to the requirement.
    - Provide a reason for the validation result.
"""
        )

    def _generate_input_prompt(self, alerts):
        """
        Generate a user prompt for the requirement generation engine.
        """
        prompt = "The following are the alerts received:\n"
        for alert in alerts:
            prompt += f"- {alert.get('action_body', 'N/A')}\n"
        prompt += "\nBased on these alerts, please generate the agricultural product and service requirements needed to address the issues raised in the alerts."
        return prompt

    def add_alert(self, alert):
        """
        Add a new alert ensuring alert_id is unique.
        Sample Alert:
        {
            timestamp: "2023-10-01T12:00:00Z",
            alert_id: "alert_001",
            action_body: "...."
            action_severity: "high",
            type: "sensor"  # or "rain" etc
            sensor_hub_id: "hub_001" 
        }
        """
        alert = {
            **alert,
            "delivery_status": "pending",  # [ 'pending', 'wap', 'mail' , 'wap+mail']
            "comments": [],
            "resolved": False
        }
        return self.add_item(
            item=alert,
            unique_field="alert_id",
            vector_fields=["action_body"]
        )

    def get_alert_by_id(self, alert_id):
        return self.get_by_id("alert_id", alert_id)
    
    def get_alerts_by_hub_id(self, sensor_hub_id):
        """
        Get all alerts for a given sensor_hub_id.
        """
        return list(self.collection.find({"sensor_hub_id": sensor_hub_id}))
    
    def get_alerts_by_hub_ids(self, sensor_hub_ids: List[str]):
        """
        Get all alerts for a list of sensor_hub_ids.
        """
        if not sensor_hub_ids:
            return []
        return list(self.collection.find({"sensor_hub_id": {"$in": sensor_hub_ids}}))
    
    def update_delivery_status(self, alert_id: str, delivery_status: str):
        """
        Update the delivery status of an alert.
        """
        if not alert_id or not delivery_status:
            return False
        result = self.collection.update_one(
            {"alert_id": alert_id},
            {"$set": {"delivery_status": delivery_status}}
        )
        return result.modified_count > 0
    
    def change_alert_status(self, alert_id: str, resolved: bool):
        """
        Change the resolved status of an alert.
        """
        if not alert_id:
            return False
        result = self.collection.update_one(
            {"alert_id": alert_id},
            {"$set": {"resolved": resolved}}
        )
        return result.modified_count > 0
    
    def add_comment_to_alert(self, alert_id: str, comment: str):
        """
        Add a comment to an alert.
        """
        if not alert_id or not comment:
            return False
        result = self.collection.update_one(
            {"alert_id": alert_id},
            {"$push": {"comments": comment}}
        )
        return result.modified_count > 0


    def generate_requirement(self, date:str, sensor_hub_id: str):
        """
        Step 1: Get all alerts for the given date with high and critical action_severity
        Step 2: Analyze if any agricultural products or services are needed
        Step 3: Generate a product requirement based on the analysis
        Step 4: Return the service requirement based on the analysis
        """
        alerts = self.collection.find({
            "timestamp": {"$regex": f"^{date}"},
            "action_severity": {"$in": ["high", "critical"]},
            "sensor_hub_id": sensor_hub_id
        })
        
        alerts_list = list(alerts)
        if not alerts_list:
            return dict(BaseRequirements(product_requirements=[], service_requirements=[]))
        prompt = self._generate_input_prompt(alerts_list)
        requirements = self.req_engine.run(prompt)[0]
        return dict(requirements)

    def validate_combination(self, combinations: List[Dict[str, Any]], requirements: List[Dict[str, Any]]):
        """
        Validate a list of product/service combinations against the requirements.
        
        Args:
            combinations (List[Dict[str, Any]]): List of product/service combinations to validate.
            requirements (List[Dict[str, Any]]): List of requirements to validate against.
        
        Returns:
            List[IsValidCombination]: List of validation results for each combination.
        """
        results = []
        combined_requirements = "\n".join([f"- {req}" for req in requirements])
        for combination in combinations:
            element = f"Name: {combination.get('name', 'N/A')}, Description: {combination.get('description', 'N/A')}, Usage: {combination.get('usage', 'N/A')}"
            prompt = f"Validate the following combination against the requirements:\n\nCombination:\n{element}\n\nRequirements:\n{combined_requirements}\n\nIs this combination valid? Provide a reason."
            # print(f"Validating combination: {prompt}")
            validation_result = self.product_validator_engine.run(prompt)[0]
            # print(f"Validation Result for {element}: {validation_result}")
            if validation_result['is_valid']:
                results.append({
                    "reason": validation_result['reason'],
                    "product_service": combination
                })
        return results
            

    def suggest_for_date(self, date: str, sensor_hub_id: str):
        """
        Suggest products and services based on the requirements generated for the given date.
        """
        requirements = self.generate_requirement(date, sensor_hub_id)
        # print(f"Generated Requirements for {date}: {requirements}")
        product_suggestions = []
        service_suggestions = []
        if requirements.get('product_requirements'):
            for req in requirements['product_requirements']:
                # print(f"Searching for products matching requirement: {req}")
                products = self.product_handler.search(req, vector_field='vector')
                product_suggestions.extend(products[:1])

        print(f"[PRODUCT] Before filtering, found {len(product_suggestions)} product suggestions for date {date}.")
        filtered_product_suggestions = self.validate_combination(
            combinations=product_suggestions,
            requirements=requirements['product_requirements']
        )
        print(f"[PRODUCT] After filtering, found {len(filtered_product_suggestions)} valid product suggestions for date {date}.")

        if requirements.get('service_requirements'):
            for req in requirements['service_requirements']:
                # print(f"Searching for services matching requirement: {req}")
                services = self.service_handler.search(req, vector_field='vector')
                service_suggestions.extend(services[:1])

        print(f"[SERVICE] Before filtering, found {len(service_suggestions)} service suggestions for date {date}.")
        filtered_service_suggestions = self.validate_combination(
            combinations=service_suggestions,
            requirements=requirements['service_requirements']
        )
        print(f"[SERVICE] After filtering, found {len(filtered_service_suggestions)} valid service suggestions for date {date}.")

        result = {
            "date": date,
            "products": filtered_product_suggestions,
            "services": filtered_service_suggestions
        }

        self.product_service_suggestion_handler.add_suggestions({
            "sensor_hub_id": sensor_hub_id,
            "suggestions": result,
            "timestamp": date
        })

        return result


class UserHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__("users")

    def add_user(self, user):
        """
        Add a new user ensuring user_id is unique.
        Sample User:
        {
            "user_id": "user_001",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "whatsapp_number": "+1234567890",
            "location": {
                "latitude": 12.345678,
                "longitude": 98.765432
            }
        }
        """
        return self.add_item(
            item=user,
            unique_field="user_id"
        )
    


class WeatherHandler(BaseMongoHandler):
    def __init__(self):
        super().__init__("weather")

    def add_weather_data(self, weather_data):
        """
        Add weather data ensuring date is unique.
        Sample Weather Data:
        {
            "date":
            "latitude": 12.345678,
            "longitude": 98.765432,
            "forecast": [
                {
                    "date": "2023-10-01",
                    "temperature_avg": 25.0,
                    "precipitation_sum": 5.0,
                    ...
                },
                {
                }
            ],
            "recent": [
                {
                    "date": "2023-09-30",
                    "temperature_avg": 24.0,
                    "precipitation_sum": 3.0,
                    ...
                },
                {
                }
            ]
        }
        """
        unique_field = "latitude_longitude_date"
        
        weather_data['latitude_longitude_date'] = f"{int(weather_data['latitude'])}_{int(weather_data['longitude'])}_{weather_data['date']}"
        return self.add_item(
            item=weather_data,
            unique_field=unique_field
        )
    

class FieldHandler(BaseMongoHandler):
    def __init__(self, user_handler: UserHandler = None):
        super().__init__("fields")
        self.user_handler = user_handler

    def add_field(self, field):
        """
        Add a new field ensuring field_id is unique.
        Sample Field:
        {
            "field_id": "field_001",
            "user_id": "user_001",
            "name": "Field A",
            "location": {
                "latitude": 12.345678,
                "longitude": 98.765432
            },
            "sensor_hub_id": "hub_001",
            "crop_type": "Wheat",
            "user_texts":[
                "This is a sample field description.",
                "The field is well irrigated and has good soil quality."
            ]
        }
        """
        return self.add_item(
            item={
                **field,
                "created_at": datetime.utcnow().isoformat()
            },
            unique_field="field_id"
        )
    
    def get_fields_by_user_id(self, user_id):
        """
        Get all fields for a given user_id.
        """
        return list(self.collection.find({"user_id": user_id}))

    def get_fields_by_hub_id(self, sensor_hub_id):
        """
        Get all fields for a given sensor_hub_id.
        """
        return list(self.collection.find({"sensor_hub_id": sensor_hub_id}))

    def get_user_by_field_id(self, field_id):
        """
        Get user_id for a given field_id.
        """
        field = self.collection.find_one({"field_id": field_id})
        if field and self.user_handler:
            return self.user_handler.get_by_id("user_id", field.get("user_id"))
        return None
    
    def get_user_by_hub_id(self, sensor_hub_id):
        """
        Get user_id for a given sensor_hub_id.
        """
        field = self.collection.find_one({"sensor_hub_id": sensor_hub_id})
        if field and self.user_handler:
            return self.user_handler.get_by_id("user_id", field.get("user_id"))
        return None
    
    def delete_by_id(self, unique_field, value):
        super().delete_by_id(unique_field, value)
        # remove the field from the user handler if it exists
        if self.user_handler:
            user = self.user_handler.get_by_id("user_id", value)
            if user:
                # Assuming user has a list of field_ids
                user['field_ids'] = [fid for fid in user.get('field_ids', []) if fid != value]
                self.user_handler.update_item(user, unique_field="user_id")
        return True


# Handlers
AGRI_PRODUCT_HANDLER = AgriProductHandler()
AGRI_SERVICE_HANDLER = AgriServiceHandler()
AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER = ProductServiceSuggestionHandler()
ALERT_STORAGE_HANDLER = AlertStorageHandler(
    product_handler=AGRI_PRODUCT_HANDLER,
    service_handler=AGRI_SERVICE_HANDLER,
    product_service_suggestion_handler=AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER
)
USER_HANDLER = UserHandler()
WEATHER_HANDLER = WeatherHandler()
FIELD_HANDLER = FieldHandler(user_handler=USER_HANDLER)


def reset_handlers(exclusions=[]):
    """
    Reset all handlers by deleting all data in their respective collections.
    This is useful for testing or resetting the database.
    """
    if 'product' not in exclusions:
        print("Resetting AgriProductHandler...")
        AGRI_PRODUCT_HANDLER.delete_all()
    if 'service' not in exclusions:
        print("Resetting AgriServiceHandler...")
        AGRI_SERVICE_HANDLER.delete_all()
    if 'suggestion' not in exclusions:
        print("Resetting ProductServiceSuggestionHandler...")
        AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER.delete_all()
    if 'alert' not in exclusions:
        print("Resetting AlertStorageHandler...")
        ALERT_STORAGE_HANDLER.delete_all()
    if 'user' not in exclusions:
        print("Resetting UserHandler...")
        USER_HANDLER.delete_all()
    if 'weather' not in exclusions:
        print("Resetting WeatherHandler...")
        WEATHER_HANDLER.delete_all()
    if 'field' not in exclusions:
        print("Resetting FieldHandler...")
        FIELD_HANDLER.delete_all()