from flask import Flask, send_file, jsonify, render_template, request
import os

app = Flask(__name__)

# Chemin absolu pour PythonAnywhere
@app.route('/download-model')
def download_model():
    try:
        # Sur PythonAnywhere, le fichier est dans le même dossier
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modele_poubelle.h5')
        
        if not os.path.exists(model_path):
            return jsonify({'error': 'Fichier modèle non trouvé'}), 404
            
        return send_file(
            model_path,
            as_attachment=True,
            download_name='modele_poubelle.h5'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Simulation de prédiction
    try:
        # Ici vous intégrerez votre vrai modèle
        return jsonify({
            'success': True, 
            'label': 'VIDE', 
            'confidence': 95
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)