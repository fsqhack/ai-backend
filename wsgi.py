from app import app as application

app = application

if __name__ == "__main__":
    application.run(
        host='0.0.0.0',
        port=8080,
        # ssl_context=('https_cert.pem', 'https_key.pem')  # Add your certificate and key file paths here
    )