# trash_app_advanced.py - SYSTÈME ANTI-FAUX POSITIFS
import streamlit as st
import tensorflow as tf
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import os
from datetime import datetime
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Smart Bin Detector Pro",
    page_icon="🗑️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé - AVEC ALERTES
st.markdown("""
<style>
    /* Styles existants... */
    
    /* Alertes de confiance */
    .high-confidence {
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
        color: white;
    }
    
    .medium-confidence {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: white;
    }
    
    .low-confidence {
        background: linear-gradient(135deg, #ff5e62 0%, #ff9966 100%);
        color: white;
    }
    
    .warning-alert {
        background: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    
    .confidence-indicator {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    .high-conf { background: #d4edda; color: #155724; }
    .medium-conf { background: #fff3cd; color: #856404; }
    .low-conf { background: #f8d7da; color: #721c24; }
    
    /* Historique */
    .history-item {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .correct-prediction { border-left: 4px solid #28a745; }
    .incorrect-prediction { border-left: 4px solid #dc3545; }
</style>
""", unsafe_allow_html=True)

class AdvancedPoubellePredictor:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.confidence_thresholds = {
            'high': 85.0,    # Très fiable
            'medium': 70.0,  # Moyennement fiable  
            'low': 0.0       # Peu fiable
        }
        self.load_model()
        
    def load_model(self):
        """Charge le modèle entraîné"""
        try:
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
                return True
            else:
                return False
        except Exception as e:
            st.error(f"Erreur lors du chargement: {e}")
            return False
    
    def get_confidence_level(self, confidence):
        """Détermine le niveau de confiance"""
        if confidence >= self.confidence_thresholds['high']:
            return 'high', '🔒 Haute confiance'
        elif confidence >= self.confidence_thresholds['medium']:
            return 'medium', '⚠️ Confiance moyenne'
        else:
            return 'low', '🚨 Faible confiance'
    
    def analyze_prediction_reliability(self, label, confidence, image_features=None):
        """Analyse la fiabilité de la prédiction"""
        conf_level, conf_text = self.get_confidence_level(confidence)
        
        # Règles pour détecter les faux positifs/négatifs potentiels
        warnings = []
        
        # Règle 1: Très faible confiance
        if conf_level == 'low':
            warnings.append("Prédiction peu fiable - vérification manuelle recommandée")
        
        # Règle 2: Confiance moyenne pour "PLEINE" (souvent plus d'erreurs)
        if label == "PLEINE" and conf_level == 'medium':
            warnings.append("Prédiction 'PLEINE' avec confiance modérée - risque de faux positif")
        
        # Règle 3: Ambiguïté (proche du seuil 0.5)
        raw_confidence = confidence if label == "VIDE" else (100 - confidence)
        if 45 <= raw_confidence <= 55:
            warnings.append("Résultat ambigu - l'image pourrait être difficile à classifier")
        
        return conf_level, conf_text, warnings
    
    def convert_webp_to_compatible(self, image):
        """Convertit les images WebP en format compatible"""
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        except Exception as e:
            st.error(f"Erreur conversion WebP: {e}")
            return image
    
    def preprocess_image(self, image):
        """Prétraite l'image pour la prédiction"""
        try:
            image = self.convert_webp_to_compatible(image)
            image_resized = image.resize((150, 150))
            img_array = np.array(image_resized) / 255.0
            
            if img_array.shape != (150, 150, 3):
                return None
            
            img_array = np.expand_dims(img_array, axis=0)
            return img_array
            
        except Exception as e:
            st.error(f"Erreur prétraitement: {e}")
            return None
    
    def predict(self, image):
        """Fait une prédiction sur l'image avec analyse de fiabilité"""
        if self.model is None:
            return None, None, None, []
        
        try:
            processed_image = self.preprocess_image(image)
            
            if processed_image is None:
                return None, None, None, []
            
            prediction = self.model.predict(processed_image, verbose=0)[0][0]
            
            confidence = float(prediction)
            if prediction > 0.5:
                label = "VIDE"
                confidence_percent = confidence * 100
            else:
                label = "PLEINE"
                confidence_percent = (1 - confidence) * 100
            
            # Analyse de fiabilité
            conf_level, conf_text, warnings = self.analyze_prediction_reliability(label, confidence_percent)
                
            return label, confidence_percent, conf_level, warnings
            
        except Exception as e:
            st.error(f"Erreur prédiction: {e}")
            return None, None, None, []

def main():
    # Header principal
    st.markdown('<h1 class="main-header">🗑️ Smart Bin Detector Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Système avancé avec détection des erreurs</p>', unsafe_allow_html=True)
    
    # Vérification du modèle
    h5_files = [f for f in os.listdir('.') if f.endswith('.h5')]
    
    if not h5_files:
        st.error("❌ Aucun modèle trouvé. Placez un fichier .h5 dans le dossier.")
        return
    
    # Initialisation du prédicteur avancé
    predictor = AdvancedPoubellePredictor(h5_files[0])
    
    if not predictor.model:
        st.error("❌ Erreur de chargement du modèle")
        return
    
    # SECTION 1: IMPORTATION
    st.markdown('<div class="card upload-card">', unsafe_allow_html=True)
    st.subheader("📤 Étape 1 : Importer une image")
    
    uploaded_file = st.file_uploader(
        "Glissez-déposez votre image ici",
        type=['jpg', 'jpeg', 'png', 'webp'],
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        # Aperçu
        st.markdown("---")
        st.subheader("📷 Aperçu")
        st.image(image, use_container_width=True)
        
        # Informations
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Format", image.format)
        with col2: st.metric("Dimensions", f"{image.size[0]}x{image.size[1]}")
        with col3: st.metric("Mode", image.mode)
        
        # Bouton d'analyse
        st.markdown("---")
        st.subheader("🔍 Étape 2 : Analyser")
        
        if st.button("🎯 Analyser avec vérification d'erreurs", use_container_width=True, type="primary"):
            with st.spinner("Analyse approfondie en cours..."):
                label, confidence, conf_level, warnings = predictor.predict(image)
            
            if label and confidence is not None:
                # Stocker les résultats
                st.session_state.prediction_label = label
                st.session_state.prediction_confidence = confidence
                st.session_state.confidence_level = conf_level
                st.session_state.warnings = warnings
                st.session_state.analysis_time = datetime.now()
                st.session_state.show_results = True
                
                # Ajouter à l'historique
                if 'prediction_history' not in st.session_state:
                    st.session_state.prediction_history = []
                
                st.session_state.prediction_history.append({
                    'time': st.session_state.analysis_time,
                    'label': label,
                    'confidence': confidence,
                    'confidence_level': conf_level,
                    'warnings': warnings
                })
    
    else:
        st.info("💡 Importez une image de poubelle pour commencer")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # SECTION 2: RÉSULTATS AVEC VÉRIFICATION
    if hasattr(st.session_state, 'show_results') and st.session_state.show_results:
        label = st.session_state.prediction_label
        confidence = st.session_state.prediction_confidence
        conf_level = st.session_state.confidence_level
        warnings = st.session_state.warnings
        
        st.markdown('<div class="card result-card">', unsafe_allow_html=True)
        st.subheader("🎯 Résultats de l'analyse")
        
        # Indicateur de confiance
        conf_class = f"{conf_level}-confidence"
        conf_badge_class = f"{conf_level}-conf"
        conf_badge_text = "🔒 Haute" if conf_level == 'high' else "⚠️ Moyenne" if conf_level == 'medium' else "🚨 Faible"
        
        st.markdown(f'<div class="card result-card {conf_class}">', unsafe_allow_html=True)
        
        # Statut avec badge de confiance
        col_status, col_conf = st.columns([3, 1])
        with col_status:
            if label == "VIDE":
                st.markdown('<div class="status-badge badge-vide">🗑️ POUBELLE VIDE</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-badge badge-pleine">🚮 POUBELLE PLEINE</div>', unsafe_allow_html=True)
        
        with col_conf:
            st.markdown(f'<div class="confidence-indicator {conf_badge_class}">{conf_badge_text}</div>', unsafe_allow_html=True)
        
        # Score de confiance
        st.markdown(f'<h2 style="margin: 1rem 0; font-size: 3rem;">{confidence:.1f}%</h2>', unsafe_allow_html=True)
        st.markdown('<p style="opacity: 0.9; margin: 0; font-size: 1.1rem;">Score de confiance</p>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # ALERTES DE FIABILITÉ
        if warnings:
            st.markdown("---")
            st.subheader("🚨 Avertissements de fiabilité")
            for warning in warnings:
                st.markdown(f'<div class="warning-alert">⚠️ {warning}</div>', unsafe_allow_html=True)
        
        # RECOMMANDATIONS
        st.markdown("---")
        st.subheader("💡 Recommandations")
        
        if conf_level == 'high':
            if label == "VIDE":
                st.success("**Action :** Aucune action nécessaire - Prédiction très fiable")
            else:
                st.warning("**Action :** Vider la poubelle - Prédiction très fiable")
        
        elif conf_level == 'medium':
            st.info("**Action :** Vérification recommandée - Prédiction moyennement fiable")
            if label == "VIDE":
                st.caption("Suggestion : Vérifier visuellement si la poubelle n'est pas presque pleine")
            else:
                st.caption("Suggestion : Vérifier visuellement si la poubelle n'est pas presque vide")
        
        else:  # low confidence
            st.error("**Action :** Vérification manuelle requise - Prédiction peu fiable")
            st.caption("Suggestion : Prendre une nouvelle photo sous un meilleur angle")
        
        # STATISTIQUES DÉTAILLÉES
        with st.expander("📊 Analyse détaillée des risques"):
            st.write("**Seuils de confiance :**")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: st.metric("Haute", "≥ 85%")
            with col_t2: st.metric("Moyenne", "≥ 70%")
            with col_t3: st.metric("Faible", "< 70%")
            
            st.write("**Risques détectés :**")
            if conf_level == 'high':
                st.success("✓ Faible risque d'erreur")
            elif conf_level == 'medium':
                st.warning("⚠ Risque modéré d'erreur")
            else:
                st.error("🚨 Risque élevé d'erreur")
            
            st.write("**Valeur brute du modèle :**")
            raw_value = confidence/100 if label == "VIDE" else 1 - (confidence/100)
            st.code(f"{raw_value:.3f} (seuil à 0.5)")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # HISTORIQUE DES PRÉDICTIONS
        if hasattr(st.session_state, 'prediction_history') and st.session_state.prediction_history:
            st.markdown("---")
            st.subheader("📈 Historique des analyses")
            
            # Statistiques globales
            history = st.session_state.prediction_history
            total = len(history)
            high_conf = len([h for h in history if h['confidence_level'] == 'high'])
            medium_conf = len([h for h in history if h['confidence_level'] == 'medium'])
            low_conf = len([h for h in history if h['confidence_level'] == 'low'])
            
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1: st.metric("Total analyses", total)
            with col_stat2: st.metric("Haute confiance", high_conf)
            with col_stat3: st.metric("Faible confiance", low_conf)
            
            # Dernières analyses
            st.write("**Dernières prédictions :**")
            for i, pred in enumerate(reversed(history[-5:])):  # 5 dernières
                time_str = pred['time'].strftime('%H:%M:%S')
                conf_badge = "🟢" if pred['confidence_level'] == 'high' else "🟡" if pred['confidence_level'] == 'medium' else "🔴"
                st.text(f"{conf_badge} {time_str} - {pred['label']} ({pred['confidence']:.1f}%)")
        
        # BOUTONS D'ACTION
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔄 Nouvelle analyse", use_container_width=True):
                st.session_state.show_results = False
                st.rerun()
        with col_btn2:
            if st.button("📊 Rapport détaillé", use_container_width=True):
                generate_detailed_report()
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #7f8c8d; margin-top: 2rem;">'
        '<p>🛡️ Système anti-erreurs • 📈 Analyse de confiance • 📊 Historique des prédictions</p>'
        '</div>',
        unsafe_allow_html=True
    )

def generate_detailed_report():
    """Génère un rapport détaillé des performances"""
    st.info("📊 **Rapport de fiabilité généré**")
    
    if hasattr(st.session_state, 'prediction_history'):
        history = st.session_state.prediction_history
        
        # Calcul des statistiques
        total = len(history)
        if total > 0:
            avg_confidence = sum(h['confidence'] for h in history) / total
            high_conf_count = len([h for h in history if h['confidence_level'] == 'high'])
            low_conf_count = len([h for h in history if h['confidence_level'] == 'low'])
            
            st.write(f"**Statistiques sur {total} analyses :**")
            st.write(f"- Confiance moyenne : {avg_confidence:.1f}%")
            st.write(f"- Prédictions haute confiance : {high_conf_count}/{total} ({high_conf_count/total*100:.1f}%)")
            st.write(f"- Prédictions à vérifier : {low_conf_count}/{total} ({low_conf_count/total*100:.1f}%)")
            
            # Recommandations d'amélioration
            if low_conf_count / total > 0.3:  # Plus de 30% de faibles confiances
                st.warning("**Recommandation :** Envisager de ré-entraîner le modèle avec plus de données variées")

# Initialisation session state
if 'show_results' not in st.session_state:
    st.session_state.show_results = False
if 'prediction_label' not in st.session_state:
    st.session_state.prediction_label = ""
if 'prediction_confidence' not in st.session_state:
    st.session_state.prediction_confidence = 0
if 'confidence_level' not in st.session_state:
    st.session_state.confidence_level = ""
if 'warnings' not in st.session_state:
    st.session_state.warnings = []
if 'analysis_time' not in st.session_state:
    st.session_state.analysis_time = None

if __name__ == "__main__":
    main()