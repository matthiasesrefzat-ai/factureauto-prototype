# FacturationAuto 📄

Générez des factures automatiquement depuis vos relevés bancaires PDF/CSV.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🚀 Fonctionnalités

- **Import flexible** : PDF, CSV et formats bancaires bruts
- **Parsing intelligent** : Formats Qonto, CSV général, brut
- **Génération PDF** : Factures professionnelles avec TVA
- **Mode groupé** : Regrouper les transactions par client
- **Export ZIP** : Téléchargement complet des factures

## 🛠️ Installation Rapide

```bash
# 1. Cloner le dépôt
git clone https://github.com/VOTRE_UTILISATEUR/facturation-auto.git

# 2. Créer un fichier .env à partir de l'exemple
cp .env.example .env

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
python app.py
