from app.mongo.fsq_handlers import HEALTH_DATA_HANDLER, ALERT_HANDLER, USER_HANDLER, TRIP_HANDLER
from flask import Blueprint, request, jsonify
from app.service.health import HEALTH_ALERT_GENERATOR
from app.service.simulate import simulate_scenario_points
import os
from datetime import datetime


health_bp = Blueprint('health', __name__)


def validate_user_trip(user_id=None, trip_id=None):
    if user_id:
        user = USER_HANDLER.get_by_id("user_id", user_id)
        if not user:
            return False, "User not found"
    if trip_id:
        trip = TRIP_HANDLER.get_by_id("trip_id", trip_id)
        if not trip:
            return False, "Trip not found"
    return True, ""

@health_bp.route('/simulate-scenario', methods=['POST'])
def simulate_scenario():
    """
    Sample request body:
    {
        "user_id": "john.doe@example.com",
        "trip_id": "trip-1",
        "scenario": "Trekking with palpitation problem",
        "start_lat": 12.9716,
        "start_lon": 77.5946,
        "start_alt": 3000,
        "start_time": "2023-01-01T10:00:00",
        "end_time": "2023-01-01T12:00:00",
        "time_interval": 30  
    }
    """
    data = request.json
    user_id = data.get('user_id')
    trip_id = data.get('trip_id')
    scenario = data.get('scenario')
    start_lat = data.get('start_lat')
    start_lon = data.get('start_lon')
    start_alt = data.get('start_alt')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    time_interval = data.get('time_interval', 30)  # in seconds

    # validate user and trip
    is_valid, msg = validate_user_trip(user_id, trip_id)
    if not is_valid:
        return jsonify({"error": msg}), 400

    start_time = datetime.fromisoformat(start_time)
    end_time = datetime.fromisoformat(end_time)
    start_lat = float(start_lat)
    start_lon = float(start_lon)
    start_alt = float(start_alt)

    template_scenarios = [
        "Trekking with palpitation problem",
        "Trekking in low oxygen and high altitude area",
        "Healthy person in a normal trekking",
        "Roaming about in a beach"
    ]

    if scenario not in template_scenarios:
        return jsonify({"error": "Invalid scenario"}), 400
    
    points = simulate_scenario_points(
        user_id, trip_id, scenario,
        start_lat, start_lon, start_alt,
        start_time, end_time,
        time_interval=time_interval
    )

    for point in points:
        HEALTH_DATA_HANDLER.add_health_data(user_id, point)

    return jsonify({"message": f"Simulated {len(points)} health data points for scenario '{scenario}'"}), 200


@health_bp.route('/get-health-data', methods=['POST'])
def get_health_data():
    data = request.json
    user_id = data.get('user_id')
    trip_id = data.get('trip_id')

    if not user_id or not trip_id:
        return jsonify({"error": "Missing required fields"}), 400
    
    is_valid, msg = validate_user_trip(user_id, trip_id)
    if not is_valid:
        return jsonify({"error": msg}), 400
    
    try:
        health_data = HEALTH_DATA_HANDLER.get_health_data(user_id, trip_id)
        for record in health_data:
            record['_id'] = str(record['_id'])
        return jsonify({"health_data": health_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
                 
    

@health_bp.route('/generate-health-alert', methods=['POST'])
def generate_health_alert():
    data = request.json
    user_id = data.get('user_id')
    trip_id = data.get('trip_id')

    if not user_id or not trip_id:
        return jsonify({"error": "Missing required fields"}), 400

    is_valid, msg = validate_user_trip(user_id, trip_id)
    if not is_valid:
        return jsonify({"error": msg}), 400

    context = TRIP_HANDLER.get_by_id("trip_id", trip_id).get("context", "")
    print("Context:", context)

    try:
        result = HEALTH_ALERT_GENERATOR.run(user_id, context)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500