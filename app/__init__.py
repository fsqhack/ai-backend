from flask import Flask
from flask_cors import CORS
from app.controller.hello_controller import hello_blueprint
from app.controller.registration_controller import registration_bp
from app.controller.alert_controller import alert_bp
from app.controller.health_controller import health_bp

app = Flask(__name__)
app.register_blueprint(hello_blueprint)
app.register_blueprint(registration_bp, url_prefix='/registration')
app.register_blueprint(alert_bp, url_prefix='/alerts')
app.register_blueprint(health_bp, url_prefix='/health')


CORS(app)
