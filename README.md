# RX Void Analyzer (Streamlit)

## Fonctionnalités
- Chargement image RX (png / jpg)
- Définition de ROI par polygones (canvas)
- Masque ROI vert / noir
- Corrections manuelles RX par clic :
  - Jaune = soudure forcée
  - Rouge = void / manque
- Deux masques séparés
- Export PNG & JSON

## Lancement local
```bash
pip install -r requirements.txt
streamlit run app.py
