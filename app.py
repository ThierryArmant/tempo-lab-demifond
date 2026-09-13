import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="TempoLabDemifond",
    page_icon="⏱️",
    layout="wide"
)

# --- CONNEXION GOOGLE SHEETS (Mode sécurisé avec secours local) ---
try:
    conn = st.connection("gsheets", type="gsheets")
    df_eleves = conn.read(worksheet="eleves", ttl=0)
except Exception:
    # Mode secours local si Google Sheets n'est pas encore branché sur le Cloud
    if "eleves" not in st.session_state:
        st.session_state.eleves = pd.DataFrame({
            "Dossard": [101, 102, 103],
            "Nom": ["Dupont Thomas", "Martin Chloé", "Bernard Lucas"],
            "VMA": [14.0, 12.5, 15.2],
            "Objectif_pct": [80, 75, 85],
            "Distance_cible_m": [600, 500, 800]
        })
    df_eleves = st.session_state.eleves

if "passages" not in st.session_state:
    st.session_state.passages = []

# --- NAVIGATION ---
st.sidebar.title("🧭 TempoLabDemifond")
mode = st.sidebar.radio("Choisir l'espace :", ["Espace Élève / Terrain", "Espace Professeur (Sécurisé)"])

# --- ESPACE ÉLÈVE / TERRAIN ---
if mode == "Espace Élève / Terrain":
    st.title("🏃 TempoLabDemifond - Espace Élève")
    st.info("Consultez votre contrat d'allure et simulez vos passages sur le terrain.")

    dossard_actif = st.selectbox("Sélectionnez votre dossard :", df_eleves["Dossard"])
    eleve_info = df_eleves[df_eleves["Dossard"] == dossard_actif].iloc[0]

    vma = eleve_info["VMA"]
    pct = eleve_info["Objectif_pct"]
    vitesse_cible = vma * (pct / 100)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Élève", eleve_info["Nom"])
    col2.metric("VMA", f"{vma} km/h")
    col3.metric("Contrat", f"{pct}% VMA")
    col4.metric("Vitesse Cible", f"{vitesse_cible:.2f} km/h")

    st.markdown("---")
    st.success(f"📌 **Objectif :** Parcourir **{eleve_info['Distance_cible_m']} mètres** à une allure de **{vitesse_cible:.1f} km/h**.")

    st.subheader("📡 Simulateur de passage (En attendant le matériel RFID)")
    col_sim1, col_sim2, col_sim3, col_sim4 = st.columns(4)
    
    heure_actuelle = datetime.datetime.now().strftime("%H:%M:%S")
    date_actuelle = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if col_sim1.button("Départ (0m)"):
        st.session_state.passages.append({"Dossard": dossard_actif, "Plot": "Départ", "Heure": heure_actuelle, "Date": date_actuelle})
        st.success("Départ enregistré !")
        
    if col_sim2.button("Plot 25m"):
        st.session_state.passages.append({"Dossard": dossard_actif, "Plot": "25m", "Heure": heure_actuelle, "Date": date_actuelle})
        st.info("Passage 25m validé.")

    if col_sim3.button("Plot 50m"):
        st.session_state.passages.append({"Dossard": dossard_actif, "Plot": "50m", "Heure": heure_actuelle, "Date": date_actuelle})
        st.info("Passage 50m validé.")

    if col_sim4.button("Tournant 75m"):
        st.session_state.passages.append({"Dossard": dossard_actif, "Plot": "75m", "Heure": heure_actuelle, "Date": date_actuelle})
        st.warning("Demi-tour 75m validé !")

    st.markdown("### 📋 Historique de vos passages")
    if len(st.session_state.passages) > 0:
        df_all = pd.DataFrame(st.session_state.passages)
        df_eleve = df_all[df_all["Dossard"] == dossard_actif]
        if not df_eleve.empty:
            st.table(df_eleve.tail(5))
        else:
            st.write("Aucun passage pour ce dossard.")
    else:
        st.write("Aucun passage enregistré pour l'instant.")

# --- ESPACE PROFESSEUR (SÉCURISÉ) ---
elif mode == "Espace Professeur (Sécurisé)":
    st.title("🔒 TempoLabDemifond - Administration Professeur")
    
    code_pin = st.text_input("Entrez le code professeur :", type="password")
    
    if code_pin == "EPS2026":
        st.success("Accès administrateur déverrouillé.")
        
        st.subheader("📊 Gestion des élèves et des VMA")
        edited_df = st.data_editor(df_eleves, num_rows="dynamic")
        if st.button("Enregistrer les modifications"):
            st.session_state.eleves = edited_df
            st.success("Modifications prises en compte pour la session !")

        st.subheader("⚙️ Actions de séance")
        if st.button("Effacer l'historique des passages"):
            st.session_state.passages = []
            st.rerun()
    else:
        st.warning("Veuillez saisir le code PIN (`EPS2026`) pour accéder aux réglages.")
