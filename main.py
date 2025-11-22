from flask import Flask, send_file, jsonify
import random

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>🚀 Bravo ! Le site fonctionne !</h1><p><a href='/download-model'>Télécharger le modèle</a></p>"

@app.route('/download-model')
def download_model():
    return send_file('modele_poubelle.h5', as_attachment=True)

@app.route('/predict', methods=['POST'])
def predict():
    return jsonify({
        'success': True,
        'label': 'VIDE' if random.random() > 0.5 else 'PLEINE',
        'confidence': round(random.uniform(70, 95), 1)
    })

if __name__ == '__main__':
    app.run()
