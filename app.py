import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="TempoLab - Suivi RFID Intermédiaire",
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

# --- SIMULATION DE LA BASE ÉLÈVES ---
if "eleves_rfid" not in st.session_state:
    st.session_state.eleves_rfid = pd.DataFrame({
        "Classe": ["5e5", "5e5", "5e7"],
        "Dossard": [501, 502, 701],
        "Nom": ["Nathan Blanc", "Chloé Bonnet", "Lucas Brunet"],
        "VMA": [13.5, 11.5, 14.2]
    })

# --- SIMULATION DES PASSAGES AUX BORNES RFID (Tous les 25m) ---
if "log_bornes_rfid" not in st.session_state:
    st.session_state.log_bornes_rfid = pd.DataFrame([
        # Nathan Blanc (Dossard 501) - Passages aux bornes intermédiaires
        {"Dossard": 501, "Borne_m": 25, "Temps_Intermediaire": "00:06:42", "Ecart_Temps_s": -2},
        {"Dossard": 501, "Borne_m": 50, "Temps_Intermediaire": "00:13:15", "Ecart_Temps_s": -1},
        {"Dossard": 501, "Borne_m": 75, "Temps_Intermediaire": "00:19:50", "Ecart_Temps_s": +1},
        {"Dossard": 501, "Borne_m": 100, "Temps_Intermediaire": "00:26:20", "Ecart_Temps_s": 0},
        {"Dossard": 501, "Borne_m": 125, "Temps_Intermediaire": "00:32:55", "Ecart_Temps_s": +2},
        {"Dossard": 501, "Borne_m": 150, "Temps_Intermediaire": "00:39:30", "Ecart_Temps_s": 0},
        # Chloé Bonnet (Dossard 502)
        {"Dossard": 502, "Borne_m": 25, "Temps_Intermediaire": "00:07:10", "Ecart_Temps_s": +4},
        {"Dossard": 502, "Borne_m": 50, "Temps_Intermediaire": "00:14:25", "Ecart_Temps_s": +6},
        {"Dossard": 502, "Borne_m": 75, "Temps_Intermediaire": "00:21:40", "Ecart_Temps_s": +5},
        {"Dossard": 502, "Borne_m": 100, "Temps_Intermediaire": "00:29:00", "Ecart_Temps_s": +8},
    ])

df_eleves = st.session_state.eleves_rfid
df_passages = st.session_state.log_bornes_rfid

# --- MENU LATÉRAL ---
st.sidebar.title("🏁 TempoLab - RFID Bornes")
classes_dispo = sorted(df_eleves["Classe"].unique().tolist())
classe_choisie = st.sidebar.selectbox("📂 Choisir la classe :", classes_dispo)

df_classe = df_eleves[df_eleves["Classe"] == classe_choisie]

st.title(f"🏃 Suivi Bornes Intermédiaires (RFID) - Classe {classe_choisie}")
st.write("L'élève sélectionne son nom pour analyser ses temps intermédiaires et ses écarts enregistrés par les bornes tous les 25 mètres.")

st.markdown("---")

# --- SÉLECTION DE L'ÉLÈVE ---
df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
nom_selectionne = st.selectbox("🎯 Sélectionne ton nom :", df_classe["Label"])

if nom_selectionne:
    dossard_actif = int(nom_selectionne.split(" - ")[0])
    infos_eleve = df_classe[df_classe["Dossard"] == dossard_actif].iloc[0]

    st.markdown("---")
    st.header(f"👤 Bilan de course : {infos_eleve['Nom']}")

    # Filtrer les passages RFID de l'élève
    df_ses_bornes = df_passages[df_passages["Dossard"] == dossard_actif]

    if not df_ses_bornes.empty:
        distance_max = df_ses_bornes["Borne_m"].max()
        dernier_temps = df_ses_bornes.iloc[-1]["Temps_Intermediaire"]

        # Métriques globales
        col1, col2, col3 = st.columns(3)
        col1.metric("📏 Distance Totale Validée (RFID)", f"{distance_max} mètres")
        col2.metric("⏱️ Dernier Temps Intermédiaire", dernier_temps)
        col3.metric("⚡ VMA", f"{infos_eleve['VMA']} km/h")

        st.markdown("---")

        # Graphique des écarts de temps par borne (25m, 50m, 75m...)
        st.subheader("📉 Écarts au temps cible à chaque borne (en secondes)")
        st.write("*(Au-dessus de 0 = en retard par rapport au contrat ; En dessous de 0 = en avance)*")
        
        df_graph = df_ses_bornes.set_index("Borne_m")[["Ecart_Temps_s"]]
        st.bar_chart(df_graph)

        # Tableau détaillé des bornes intermédiaires
        st.subheader("📋 Tableau des temps intermédiaires par borne")
        st.dataframe(
            df_ses_bornes[["Borne_m", "Temps_Intermediaire", "Ecart_Temps_s"]].rename(
                columns={
                    "Borne_m": "Borne (mètres)",
                    "Temps_Intermediaire": "Temps Intermédiaire",
                    "Ecart_Temps_s": "Écart au temps cible (sec)"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Aucune donnée de borne RFID enregistrée pour cet élève pour l'instant.")
