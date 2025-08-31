from app.mongo.fsq_handlers import ALERT_HANDLER
from flask import Blueprint, request, jsonify
import os
from datetime import datetime

alert_bp = Blueprint('alert', __name__)


@alert_bp.route('/', methods=['GET', 'POST'])
def ping():
    return jsonify({"message": "Alert service is up!"}), 200

@alert_bp.route('/create-alert', methods=['POST'])
def create_alert():
    """
    Sample request body:
    {
        "user_id": "john.doe@example.com",
        "metadata": {
            "type": "location",
            "title": "User entered a new location",
            "description": "User has entered a new location",
            "severity": "medium",
            "lat": 37.7749,
            "lon": -122.4194
        }
    }
    """
    data = request.json
    user_id = data.get('user_id')
    metadata = data.get('metadata', {})
    # Current timestamp
    timestamp = data.get('timestamp', datetime.now().isoformat())
    if not user_id or not timestamp or not metadata:
        return jsonify({"error": "Missing required fields"}), 400
    
    type = metadata.get('type')
    title = metadata.get('title')
    description = metadata.get('description')
    severity = metadata.get('severity', 'medium')   
    lat = metadata.get('lat')
    lon = metadata.get('lon')

    if not type or not title or not description:
        return jsonify({"error": "Missing required metadata fields"}), 400
    
    try:
        ALERT_HANDLER.add_alert(
            user_id=user_id,
            timestamp=timestamp,
            metadata={
                "type": type,
                "title": title,
                "description": description,
                "severity": severity,
                "lat": lat,
                "lon": lon
            }
        )
        return jsonify({"message": "Alert created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@alert_bp.route('/get-alerts', methods=['POST'])
def get_alerts():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        alerts = ALERT_HANDLER.get_by_user_id(user_id)
        for alert in alerts:
            alert['_id'] = str(alert['_id'])
        return jsonify({"alerts": alerts}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@alert_bp.route('/delete-alert', methods=['POST'])
def delete_alert():
    data = request.json
    alert_id = data.get('alert_id')

    if not alert_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        ALERT_HANDLER.delete_by_id("alert_id", alert_id)
        return jsonify({"message": "Alert deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@alert_bp.route('/delete-alerts-by-user', methods=['POST'])
def delete_all_alerts():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        ALERT_HANDLER.delete_by_id("user_id", user_id)
        return jsonify({"message": "All alerts deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500