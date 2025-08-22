from flask import Flask
from flask_cors import CORS
from app.controller.hello_controller import hello_blueprint
# from app.controller.reg_controller import reg_blueprint
# from app.controller.field_handler import field_blueprint
# from app.controller.alert_controller import alert_blueprint
# from app.controller.productservice_controller import productservice_blueprint
# from app.controller.fin_controller import fin_blueprint
# from app.controller.notifcation_controller import notification_blueprint
# from app.controller.chat_controller import chat_blueprint

app = Flask(__name__)
app.register_blueprint(hello_blueprint)
# app.register_blueprint(reg_blueprint, url_prefix='/registration')
# app.register_blueprint(field_blueprint, url_prefix='/field')
# app.register_blueprint(alert_blueprint, url_prefix='/alert')
# app.register_blueprint(productservice_blueprint, url_prefix='/productservice')
# app.register_blueprint(fin_blueprint, url_prefix='/fin')
# app.register_blueprint(notification_blueprint, url_prefix='/notification')
# app.register_blueprint(chat_blueprint, url_prefix='/chat')

CORS(app)
