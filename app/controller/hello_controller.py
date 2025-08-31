from flask import Blueprint, jsonify, request
from app.service.hello_service import get_hello_message
from app.mongo.fsq_handlers import (
    USER_HANDLER, TRIP_HANDLER, HEALTH_DATA_HANDLER, ALERT_HANDLER
)

hello_blueprint = Blueprint('hello', __name__)

@hello_blueprint.route('/hello', methods=['GET'])
def hello():
    return jsonify(get_hello_message()), 200

@hello_blueprint.route('/reset', methods=['POST'])
def reset():
    data = request.json
    reset_list = data.get('reset_list', [])

    if 'users' in reset_list:
        USER_HANDLER.delete_all()
    if 'trips' in reset_list:
        TRIP_HANDLER.delete_all()
    if 'health' in reset_list:
        HEALTH_DATA_HANDLER.delete_all()
    if 'alerts' in reset_list:
        ALERT_HANDLER.delete_all()

    return jsonify({"message": "Selected data has been reset."}), 200