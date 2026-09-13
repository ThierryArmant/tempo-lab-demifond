import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="TempoLab - Arrivée & Classement",
    page_icon="🏁",
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

# --- BASE ÉLÈVES AVEC NUMÉRO DE POCHETTE / PUCE ---
if "eleves_cross" not in st.session_state:
    st.session_state.eleves_cross = pd.DataFrame({
        "Pochette_RFID": ["PUCE_01", "PUCE_02", "PUCE_03", "PUCE_04"],
        "Classe": ["5e5", "5e5", "5e5", "5e7"],
        "Dossard": [501, 502, 503, 701],
        "Nom": ["Nathan Blanc", "Chloé Bonnet", "Lucas Brunet", "Emma Colin"],
    })

# --- SIMULATION DU FLUX D'ARRIVÉE CAPTÉ PAR LA BORNE ---
# (Ordre chronologique exact où les puces ont franchi la ligne d'arrivée)
if "log_arrivee_rfid" not in st.session_state:
    st.session_state.log_arrivee_rfid = pd.DataFrame([
        {"Pochette_RFID": "PUCE_03", "Heure_Arrivee": "10:15:42.100"},
        {"Pochette_RFID": "PUCE_01", "Heure_Arrivee": "10:15:45.300"},
        {"Pochette_RFID": "PUCE_04", "Heure_Arrivee": "10:15:50.800"},
        {"Pochette_RFID": "PUCE_02", "Heure_Arrivee": "10:16:02.150"},
    ])

df_eleves = st.session_state.eleves_cross
df_log = st.session_state.log_arrivee_rfid

# --- NAVIGATION DANS L'APPLI ---
mode = st.sidebar.radio("📍 Mode de l'application :", ["👤 Bilan Élève (Intermédiaires)", "🏁 Classement Arrivée (Cross / Fin de course)"])

if mode == "🏁 Classement Arrivée (Cross / Fin de course)":
    st.title("🏁 Arrivée en Direct - Classement Automatique (RFID)")
    st.write("Les élèves franchissent la ligne équipés de leur pochette brassière. Le système établit le classement instantanément.")

    # Fusionner les arrivées brutes avec la liste des élèves pour afficher les noms et classes
    df_classement = pd.merge(df_log, df_eleves, on="Pochette_RFID", how="inner")
    
    # Trier par heure de passage réelle
    df_classement = df_classement.sort_values(by="Heure_Arrivee").reset_index(drop=True)
    
    # Ajouter la colonne du classement (1er, 2e, 3e...)
    df_classement.insert(0, "Classement", [f"🥇 {i+1}" if i==0 else f"🥈 {i+1}" if i==1 else f"🥉 {i+1}" if i==2 else f"{i+1}e" for i in range(len(df_classement))])

    st.markdown("---")

    # Affichage du podium / tableau officiel
    st.subheader("🏆 Classement Officiel de la Course")
    st.dataframe(
        df_classement[["Classement", "Nom", "Classe", "Dossard", "Heure_Arrivee"]].rename(
            columns={
                "Nom": "Nom de l'élève",
                "Classe": "Classe",
                "Dossard": "Dossard",
                "Heure_Arrivee": "Heure de passage (RFID)"
            }
        ),
        use_container_width=True,
        hide_index=True
    )

else:
    # --- MODE BILAN INDIVIDUEL (Éléments vus précédemment) ---
    st.sidebar.markdown("---")
    classes_dispo = sorted(df_eleves["Classe"].unique().tolist())
    classe_choisie = st.sidebar.selectbox("📂 Choisir la classe :", classes_dispo)
    
    df_classe = df_eleves[df_eleves["Classe"] == classe_choisie]
    st.title(f"🏃 Bilan Individuel - Classe {classe_choisie}")
    
    nom_selectionne = st.selectbox("🎯 Sélectionne ton nom :", df_classe["Nom"])
    if nom_selectionne:
        infos = df_classe[df_classe["Nom"] == nom_selectionne].iloc[0]
        st.success(info_texte := f"Pochette assignée : **{infos['Pochette_RFID']}** (Dossard {infos['Dossard']})")
        st.info("Ici s'affichent les temps intermédiaires et les graphiques d'écarts de l'élève.")
