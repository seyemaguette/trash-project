from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image
import numpy as np
import tensorflow as tf
from datetime import datetime
import base64
from io import BytesIO
from flask import send_from_directory
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file

# Charger le modèle une fois au démarrage
print("🧠 Chargement du modèle...")
model = tf.keras.models.load_model('modele_poubelle.h5')
print("✅ Modèle chargé !")

def preprocess_image(image):
    """Prétraite l'image pour la prédiction"""
    # Conversion et redimensionnement
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image = image.resize((150, 150))
    
    # Conversion en array et normalisation
    img_array = np.array(image) / 255.0
    
    if img_array.shape == (150, 150, 3):
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Vérifier si un fichier a été uploadé
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier uploadé'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400
        
        # Vérifier l'extension
        allowed_extensions = {'jpg', 'jpeg', 'png', 'webp'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'error': 'Format non supporté'}), 400
        
        # Ouvrir et traiter l'image
        image = Image.open(file.stream)
        
        # Prétraitement
        processed_image = preprocess_image(image)
        if processed_image is None:
            return jsonify({'error': 'Erreur de traitement de l\'image'}), 400
        
        # Prédiction
        prediction = model.predict(processed_image, verbose=0)[0][0]
        
        # Interprétation
        confidence = float(prediction)
        if prediction > 0.5:
            label = "VIDE"
            confidence_percent = confidence * 100
        else:
            label = "PLEINE"
            confidence_percent = (1 - confidence) * 100
        
        # Préparer l'image pour l'affichage
        buffered = BytesIO()
        image.save(buffered, format="JPEG", quality=70)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'label': label,
            'confidence': round(confidence_percent, 1),
            'image_data': f"data:image/jpeg;base64,{img_str}",
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur: {str(e)}'}), 500
    

@app.route('/download-model')
def download_model():
    try:
        # Chemin vers le modèle dans le dossier parent
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modele_poubelle.h5')
        return send_file(model_path, as_attachment=True, download_name='modele_poubelle.h5')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# OU si vous voulez le servir comme fichier statique
@app.route('/modele_poubelle.h5')
def serve_model():
    return send_from_directory('..', 'modele_poubelle.h5')

if __name__ == '__main__':
    app.run(debug=True)