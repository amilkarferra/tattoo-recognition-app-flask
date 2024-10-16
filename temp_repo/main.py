import logging
from app import app

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("Starting the Flask application")
    port = 5000  # Change the port to 5000
    logging.info(f"Attempting to run on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
    logging.info("Flask application has stopped")
