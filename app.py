import os
import json
import logging
from flask import Flask, render_template, request, jsonify
from google.cloud import vision
from google.oauth2 import service_account
from PIL import Image
import io
import base64
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load the tattoo database
try:
    with open('tattoo_database.json', 'r') as f:
        tattoo_database = json.load(f)
    logger.info("Tattoo database loaded successfully")
except Exception as e:
    logger.error(f"Error loading tattoo database: {str(e)}")
    tattoo_database = []    

# Initialize Google Cloud Vision client
client = None
try:
    credentials_file = 'macro-plate-355517-55057e047a57.json'
    if os.path.exists(credentials_file):
        client = vision.ImageAnnotatorClient.from_service_account_file(credentials_file)
        logger.info('Google Cloud Vision client initialized successfully with provided credentials file')
    else:
        logger.error(f'Credentials file {credentials_file} not found')
except Exception as e:
    logger.error(f'Error initializing Google Cloud Vision client: {str(e)}')

def string_similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

@app.route('/')
def index():
    return render_template('index_updated.html')

@app.route('/health')
def health_check():
    status = "ok" if client else "error"
    message = "Server is running, Google Cloud Vision client initialized" if client else "Server is running, but Google Cloud Vision client is not initialized"
    return jsonify({"status": status, "message": message}), 200 if client else 500

@app.route('/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        logger.warning("No image file uploaded")
        return jsonify({'error': 'No image file uploaded'}), 400

    image_file = request.files['image']
    max_labels = int(request.form.get('max_labels', 15))
    
    # Read the image file
    image_content = image_file.read()
    
    if not client:
        logger.error("Google Cloud Vision client not initialized")
        return jsonify({'error': 'Image analysis service unavailable. Please check the server configuration.'}), 500

    try:
        # Perform label detection on the image file
        image = vision.Image(content=image_content)
        response = client.label_detection(image=image, max_results=max_labels)
        labels = response.label_annotations

        # Extract label descriptions with confidence threshold
        label_descriptions = [label.description for label in labels if label.score > 0.7]
        logger.info(f"Labels detected: {label_descriptions}")

        # Find the best match in the tattoo database
        best_match = None
        best_score = 0
        threshold = 0.3  # Adjust this value as needed

        logger.info("Starting matching process")
        for tattoo in tattoo_database:
            score = 0
            for desc in tattoo['descripciones']:
                desc_score = max(string_similarity(desc['label'], label) * label_score * desc['weight'] for label, label_score in zip(label_descriptions, [label.score for label in labels]))
                score += desc_score
            
            # Normalize the score based on the number of descriptions
            score = score / len(tattoo['descripciones'])
            
            logger.debug(f"Matching '{tattoo['nombreImagen']}': score = {score}")
            if score > best_score and score >= threshold:
                best_score = score
                best_match = tattoo

        # Convert image to base64 for displaying in the frontend
        img = Image.open(io.BytesIO(image_content))
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        if best_match:
            logger.info(f"Best match found: {best_match['nombreImagen']} with score {best_score}")
            return jsonify({
                'match': best_match,
                'uploaded_image': f'data:image/png;base64,{img_base64}',
                'labels': label_descriptions,
                'matched_labels': [desc['label'] for desc in best_match['descripciones']]
            })
        else:
            logger.warning(f"No matching tattoo found. Best score: {best_score}")
            return jsonify({
                'error': 'No matching tattoo found',
                'uploaded_image': f'data:image/png;base64,{img_base64}',
                'labels': label_descriptions,
                'matched_labels': []
            }), 404

    except Exception as e:
        logger.error(f'Error during image analysis: {str(e)}')
        if 'invalid authentication credentials' in str(e).lower():
            return jsonify({'error': 'Authentication error. Please check the API key.'}), 401
        else:
            return jsonify({'error': 'An error occurred during image analysis. Please try again later.'}), 500

@app.route('/tattoo_database')
def get_tattoo_database():
    return jsonify(tattoo_database)

@app.route('/add_tattoo', methods=['POST'])
def add_tattoo():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded'}), 400

    image_file = request.files['image']
    image_content = image_file.read()
    max_labels = int(request.form.get('max_labels', 15))

    try:
        # Analyze image with Vision API
        image = vision.Image(content=image_content)
        response = client.label_detection(image=image, max_results=max_labels)
        labels = response.label_annotations
        label_descriptions = [{"label": label.description, "weight": 1.0} for label in labels if label.score > 0.7]

        # Save image to static/images folder
        image_filename = f"{len(tattoo_database) + 1}_{image_file.filename}"
        image_path = os.path.join('static', 'images', image_filename)
        with open(image_path, 'wb') as f:
            f.write(image_content)

        # Add new tattoo to database
        new_tattoo = {
            "nombreImagen": image_filename,
            "descripciones": label_descriptions,
            "user_uploaded": True
        }
        tattoo_database.append(new_tattoo)

        # Save updated database
        with open('tattoo_database.json', 'w') as f:
            json.dump(tattoo_database, f, indent=2)

        return jsonify({'success': True, 'message': 'Tattoo added successfully', 'tattoo': new_tattoo}), 200
    except Exception as e:
        logger.error(f'Error adding new tattoo: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/edit_labels/<image_name>', methods=['GET', 'POST'])
def edit_labels(image_name):
    tattoo = next((t for t in tattoo_database if t['nombreImagen'] == image_name), None)
    if not tattoo:
        return jsonify({'error': 'Tattoo not found'}), 404

    if request.method == 'POST':
        new_labels = request.json.get('labels', [])
        tattoo['descripciones'] = [{"label": label, "weight": 1.0} for label in new_labels]
        with open('tattoo_database.json', 'w') as f:
            json.dump(tattoo_database, f, indent=2)
        return jsonify({'success': True, 'message': 'Labels updated successfully'})

    return jsonify({'labels': [desc['label'] for desc in tattoo['descripciones']]})

@app.route('/edit_weights/<image_name>', methods=['POST'])
def edit_weights(image_name):
    tattoo = next((t for t in tattoo_database if t['nombreImagen'] == image_name), None)
    if not tattoo:
        return jsonify({'error': 'Tattoo not found'}), 404

    new_weights = request.json.get('weights', {})
    for desc in tattoo['descripciones']:
        if desc['label'] in new_weights:
            desc['weight'] = float(new_weights[desc['label']])

    with open('tattoo_database.json', 'w') as f:
        json.dump(tattoo_database, f, indent=2)

    return jsonify({'success': True, 'message': 'Weights updated successfully'})

@app.route('/delete_tattoo/<image_name>', methods=['POST'])
def delete_tattoo(image_name):
    global tattoo_database
    tattoo_database = [t for t in tattoo_database if t['nombreImagen'] != image_name]
    with open('tattoo_database.json', 'w') as f:
        json.dump(tattoo_database, f, indent=2)
    
    # Delete the image file
    image_path = os.path.join('static', 'images', image_name)
    if os.path.exists(image_path):
        os.remove(image_path)
    
    return jsonify({'success': True, 'message': 'Tattoo deleted successfully'})

@app.route('/recreate_description/<image_name>', methods=['POST'])
def recreate_description(image_name):
    tattoo = next((t for t in tattoo_database if t['nombreImagen'] == image_name), None)
    if not tattoo:
        return jsonify({'error': 'Tattoo not found'}), 404

    image_path = os.path.join('static', 'images', image_name)
    if not os.path.exists(image_path):
        return jsonify({'error': 'Image file not found'}), 404

    try:
        with open(image_path, 'rb') as image_file:
            image_content = image_file.read()

        image = vision.Image(content=image_content)
        max_labels = int(request.form.get('max_labels', 15))
        response = client.label_detection(image=image, max_results=max_labels)
        labels = response.label_annotations
        new_descriptions = [{"label": label.description, "weight": 1.0} for label in labels if label.score > 0.7]

        tattoo['descripciones'] = new_descriptions
        with open('tattoo_database.json', 'w') as f:
            json.dump(tattoo_database, f, indent=2)

        return jsonify({'success': True, 'message': 'Description recreated successfully', 'new_descriptions': new_descriptions})
    except Exception as e:
        logger.error(f'Error recreating description: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
