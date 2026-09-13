import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="TempoLab - Curseur VMA & Distance Cible",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN HAUT CONTRASTE (Plein soleil) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #111418 !important; border-right: 2px solid #262a33; }
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stDataFrame"] *, [data-testid="stTable"] *, th, td { color: #000000 !important; }
    div[data-testid="stMetric"] { background-color: #16181d; border: 2px solid #333842; border-radius: 10px; padding: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- BASE ÉLÈVES (CLASSE DE 5ème - 20 Élèves) ---
if "eleves_vma" not in st.session_state:
    st.session_state.eleves_vma = pd.DataFrame({
        "Classe": ["5ème"] * 20,
        "Dossard": [5501, 5502, 5503, 5504, 5505, 5506, 5507, 5508, 5509, 5510, 
                    5511, 5512, 5513, 5514, 5515, 5516, 5517, 5518, 5519, 5520],
        "Nom": [
            "Blanc Nathan", "Bonnet Chloé", "Brunet Lucas", "Chevalier Manon", 
            "Clement Hugo", "Colin Emma", "David Théo", "Dupond Sarah", 
            "Dupont Thomas", "Fabre Inès", "Faure Louis", "Fontaine Zoé", 
            "Fournier Lucas", "Garcia Léa", "Garnier Tom", "Gautier Camille", 
            "Girard Nathan", "Guerin Juliette", "Henry Hugo", "Laurent Maëlys"
        ],
        "VMA": [13.5, 11.5, 14.8, 12.0, 13.0, 12.8, 15.0, 10.5, 14.2, 13.2, 
                12.2, 14.0, 15.5, 11.8, 13.8, 12.5, 14.5, 13.6, 12.9, 14.1],
        "Objectif_pct": [80, 75, 85, 80, 80, 75, 90, 75, 80, 80, 
                         75, 85, 90, 80, 80, 75, 85, 80, 75, 80]
    })

# --- GÉNÉRATION AUTOMATIQUE DES PASSAGES AUX BORNES (Tous les 25m jusqu'à 600m) ---
if "log_bornes_vma" not in st.session_state:
    logs = []
    np.random.seed(42) # Pour garder des résultats stables
    
    for _, eleve in st.session_state.eleves_vma.iterrows():
        dossard = eleve["Dossard"]
        vma = eleve["VMA"]
        pct = eleve["Objectif_pct"]
        
        # Vitesse réelle en m/s avec un petit facteur aléatoire de forme le jour J
        vitesse_effective = (vma * (pct / 100) * 1000) / 3600 * np.random.uniform(0.97, 1.03)
        
        temps_cumule = 0
        for borne in range(25, 601, 25):
            # Temps théorique pour 25m + micro variation de régularité
            temps_intervalle = (25 / vitesse_effective) * np.random.uniform(0.98, 1.02)
            temps_cumule += temps_intervalle
            
            logs.append({
                "Dossard": dossard,
                "Borne_m": borne,
                "Temps_s": round(temps_cumule, 1)
            })
            
    st.session_state.log_bornes_vma = pd.DataFrame(logs)

df_eleves = st.session_state.eleves_vma
df_passages = st.session_state.log_bornes_vma

# --- MENU LATÉRAL ---
st.sidebar.title("🏁 TempoLab - VMA & Bornes")
classes_dispo = sorted(df_eleves["Classe"].unique().tolist())
classe_choisie = st.sidebar.selectbox("📂 Choisir la classe :", classes_dispo)

df_classe = df_eleves[df_eleves["Classe"] == classe_choisie]

st.title(f"🏃 Bilan Individuel & Curseur VMA - Classe {classe_choisie}")
st.write("Sélectionne ton nom, ajuste si besoin ton intensité (% VMA) et analyse ta distance cible par rapport au réel des bornes RFID.")

st.markdown("---")

# --- SÉLECTION DE L'ÉLÈVE ---
df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
nom_selectionne = st.selectbox("🎯 Sélectionne ton nom :", df_classe["Label"])

if nom_selectionne:
    dossard_actif = int(nom_selectionne.split(" - ")[0])
    infos_eleve = df_classe[df_classe["Dossard"] == dossard_actif].iloc[0]

    st.markdown("---")
    
    # --- CURSEUR D'INTENSITÉ / VMA ---
    st.subheader(f"⚡ Réglage du Contrat - {infos_eleve['Nom']}")
    
    vma_eleve = float(infos_eleve["VMA"])
    pct_initial = int(infos_eleve["Objectif_pct"])

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.metric("VMA de référence", f"{vma_eleve} km/h")
    with col_v2:
        # Le curseur pour ajuster l'intensité en direct
        pct_vma_curseur = st.slider("Curseur d'intensité (% VMA) :", min_value=50, max_value=110, value=pct_initial, step=5)

    # Calcul de la vitesse en mètres par seconde (m/s)
    vitesse_ms = (vma_eleve * (pct_vma_curseur / 100) * 1000) / 3600
    
    st.info(f"📌 **Vitesse cible :** {vitesse_ms:.2f} m/s (soit environ {(vitesse_ms*60):.1f} m par minute).")

    st.markdown("---")

    # Récupérer les passages RFID de l'élève
    df_ses_bornes = df_passages[df_passages["Dossard"] == dossard_actif].copy()

    if not df_ses_bornes.empty:
        # Calcul dynamique de la distance idéale / cible pour chaque temps de passage enregistré par les bornes
        df_ses_bornes["Distance_Cible_m"] = (vitesse_ms * df_ses_bornes["Temps_s"]).round(1)
        
        distance_max_reelle = df_ses_bornes["Borne_m"].max()
        dernier_temps_s = df_ses_bornes.iloc[-1]["Temps_s"]
        distance_cible_finale = vitesse_ms * dernier_temps_s

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("📏 Distance Réelle Validée", f"{distance_max_reelle} m")
        col_m2.metric("🎯 Distance Cible Théorique", f"{distance_cible_finale:.1f} m")
        col_m3.metric("⏱️ Temps Total", f"{dernier_temps_s} secondes")

        st.markdown("---")

        st.subheader("📋 Tableau des passages aux bornes (25m, 50m, 75m...) et Distances Cibles")
        st.write("*(Ce tableau recalcule dynamiquement ta distance cible théorique selon la position du curseur % VMA ci-dessus)*")

        # Affichage du tableau propre
        st.dataframe(
            df_ses_bornes[["Borne_m", "Temps_s", "Distance_Cible_m"]].rename(
                columns={
                    "Borne_m": "Borne RFID (m)",
                    "Temps_s": "Temps (secondes)",
                    "Distance_Cible_m": "Distance Cible (m)"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        # Graphique comparatif corrigé
        st.subheader("📉 Comparatif Borne Réelle vs Distance Cible")
        df_graph = df_ses_bornes[["Borne_m", "Distance_Cible_m"]].set_index("Borne_m")
        df_graph["Distance_Réelle"] = df_graph.index
        st.line_chart(df_graph)

    else:
        st.info("Aucun passage enregistré pour cet élève.")
