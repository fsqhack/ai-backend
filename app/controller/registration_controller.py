from app.mongo.fsq_handlers import USER_HANDLER, TRIP_HANDLER
from flask import Blueprint, request, jsonify
import os


registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/', methods=['GET', 'POST'])
def ping():
    return jsonify({"message": "Registration service is up!"}), 200

@registration_bp.route('/add-user', methods=['POST'])
def add_user():
    """
    Sample user_data:
    {
        "user_id": "john.doe@example.com",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "123-456-7890"
    }
    """
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')

    if not user_id or not name or not email or not phone:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        USER_HANDLER.add_user(data)
        return jsonify({"message": "User added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@registration_bp.route('/add-taste', methods=['POST'])
def add_taste():
    user_id = request.form.get('user_id')
    taste_text = request.form.get('taste_text')
    photos = request.files.getlist('photos')
    # Save photos in tmp/images/{user_id}/
    if not user_id or not taste_text or not photos:
        return jsonify({"error": "Missing required fields"}), 400
    img_folder = f"tmp/images/{user_id}/"
    os.makedirs(img_folder, exist_ok=True)
    for photo in photos:
        photo.save(os.path.join(img_folder, photo.filename))

    try:
        response = USER_HANDLER.add_taste_group(user_id, taste_text)
        if isinstance(response, dict) and "error" in response:
            return jsonify(response), 400
        return jsonify({"message": "Taste group added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@registration_bp.route('/get-user-details', methods=['POST'])
def get_user_details():
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        user_details = USER_HANDLER.get_by_id("user_id", user_id)
        if not user_details:
            return jsonify({"error": "User not found"}), 404
        user_details["_id"] = str(user_details["_id"])
        return jsonify(user_details), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@registration_bp.route('/add-trip', methods=['POST'])
def add_trip():
    """
        Sample trip_data:
        {
            "trip_id": "trip123",
            "trip_name": "Weekend in SF",
            "user_ids": ["user123"],
            "context": "Going for a leisure trip to San Francisco on 1st Oct 2025",
            "trip_image": "<link_to_image>",
            "metadata": {
                "start_lat": 37.7749,
                "start_lng": -122.4194,
                "start_time": "2023-10-01T10:00:00Z",
                "explosure": "medium",
                "type": "leisure"
            }
        }
        """
    data = request.json
    if not data.get('trip_id') or not data.get('trip_name') or not data.get('user_ids') or not data.get('context') or not data.get('trip_image') or not data.get('metadata'):
        return jsonify({"error": "Missing required fields"}), 400

    if not data['metadata'].get('start_lat') or not data['metadata'].get('start_lng') or not data['metadata'].get('start_time'):
        return jsonify({"error": "Missing required metadata fields"}), 400

    try:
        TRIP_HANDLER.add_trip(data)
        return jsonify({"message": "Trip added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@registration_bp.route('/request-invite', methods=['POST'])
def request_invite():
    data = request.json
    trip_id = data.get('trip_id')
    user_id = data.get('user_id')

    if not trip_id or not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        response = TRIP_HANDLER.add_invite(trip_id, user_id)
        if isinstance(response, dict) and "error" in response:
            return jsonify(response), 400
        return jsonify({"message": "Invite request sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@registration_bp.route('/approve-invite', methods=['POST'])
def approve_invite():
    data = request.json
    trip_id = data.get('trip_id')
    approver_id = data.get('approver_id')
    invitee_id = data.get('invitee_id')

    if not trip_id or not approver_id or not invitee_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        response = TRIP_HANDLER.approve_invite(trip_id, approver_id, invitee_id)
        if isinstance(response, dict) and "error" in response:
            return jsonify(response), 400
        return jsonify({"message": "Invite approved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@registration_bp.route('/deny-invite', methods=['POST'])
def deny_invite():
    data = request.json
    trip_id = data.get('trip_id')
    approver_id = data.get('approver_id')
    invitee_id = data.get('invitee_id')

    if not trip_id or not approver_id or not invitee_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        response = TRIP_HANDLER.deny_invite(trip_id, approver_id, invitee_id)
        if isinstance(response, dict) and "error" in response:
            return jsonify(response), 400
        return jsonify({"message": "Invite denied successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@registration_bp.route('/view-invites', methods=['POST'])
def view_invites():
    trip_id = request.json.get('trip_id')
    user_id = request.json.get('user_id')

    if not trip_id or not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        response = TRIP_HANDLER.view_invites(trip_id, user_id)
        if isinstance(response, dict) and "error" in response:
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@registration_bp.route('/view-members', methods=['POST'])
def view_members():
    trip_id = request.json.get('trip_id')
    user_id = request.json.get('user_id')

    if not trip_id or not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        response = TRIP_HANDLER.view_members(trip_id, user_id)
        if isinstance(response, dict) and "error" in response:
            return jsonify(response), 400
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@registration_bp.route('/get-user-trips', methods=['POST'])
def get_user_trips():
    user_id = request.json.get('user_id')

    if not user_id:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        trips = TRIP_HANDLER.get_all_trips_for_user(user_id)
        for trip in trips:
            trip['_id'] = str(trip['_id'])
        return jsonify({"trips": trips}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500