import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="TempoLabDemifond",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN EXTERIEUR HAUT CONTRASTE (ANTI-REFLETS SOLEIL) ---
st.markdown("""
    <style>
    /* Fond global noir mat anti-reflets */
    .stApp {
        background-color: #050505;
        color: #ffffff;
    }
    
    /* Forcer le texte en blanc pour un contraste maximal au soleil */
    h1, h2, h3, h4, h5, h6, p, span, label {
        color: #ffffff !important;
    }
    
    /* Style des conteneurs / cartes métriques bien détachés */
    div[data-testid="stMetric"], div.stAlert {
        background-color: #16181d;
        border: 2px solid #333842;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Boutons larges et ultra-visibles sur le terrain */
    .stButton>button {
        width: 100%;
        background-color: #1f6feb;
        color: white;
        font-weight: bold;
        font-size: 18px;
        border-radius: 8px;
        border: 2px solid #58a6ff;
        padding: 12px;
    }
    .stButton>button:hover {
        background-color: #388bfd;
        border-color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONNEXION GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type="gsheets")
    df_eleves = conn.read(worksheet="eleves", ttl=0)
    try:
        df_passages_saved = conn.read(worksheet="passages", ttl=0)
    except Exception:
        df_passages_saved = pd.DataFrame(columns=["Classe", "Dossard", "Plot", "Heure", "Date"])
except Exception:
    # Mode secours local si Google Sheets n'est pas branché
    if "eleves" not in st.session_state:
        st.session_state.eleves = pd.DataFrame({
            "Classe": ["6ème A", "6ème A", "5ème B", "5ème B"],
            "Dossard": [101, 102, 201, 202],
            "Nom": ["Dupont Thomas", "Martin Chloé", "Durand Lucas", "Moreau Sarah"],
            "VMA": [14.0, 12.5, 15.2, 11.0],
            "Objectif_pct": [80, 75, 85, 80],
            "Distance_cible_m": [600, 500, 800, 500]
        })
    df_eleves = st.session_state.eleves

    if "passages_local" not in st.session_state:
        st.session_state.passages_local = pd.DataFrame(columns=["Classe", "Dossard", "Plot", "Heure", "Date"])
    df_passages_saved = st.session_state.passages_local

# --- BARRE LATÉRALE : SÉLECTION DE LA CLASSE & NAVIGATION ---
st.sidebar.title("🧭 TempoLabDemifond")

# SÉLECTEUR DE CLASSE GLOBAL (Gère jusqu'à 8 classes et plus)
list_classes = sorted(df_eleves["Classe"].unique().tolist()) if "Classe" in df_eleves.columns else ["6ème A"]
classe_active = st.sidebar.selectbox("📂 Choisir la classe :", list_classes)

st.sidebar.markdown("---")
mode = st.sidebar.radio("Espace :", ["Espace Élève / Terrain", "Espace Professeur (Sécurisé)"])

# Filtrer les élèves de la classe active
df_eleves_classe = df_eleves[df_eleves["Classe"] == classe_active] if "Classe" in df_eleves.columns else df_eleves

# --- ESPACE ÉLÈVE / TERRAIN ---
if mode == "Espace Élève / Terrain":
    st.title(f"🏃 TempoLabDemifond - Classe : {classe_active}")
    st.info("Sélectionnez votre dossard pour voir votre contrat d'allure et valider vos passages.")

    if not df_eleves_classe.empty:
        dossard_actif = st.selectbox("Sélectionnez votre dossard :", df_eleves_classe["Dossard"])
        eleve_info = df_eleves_classe[df_eleves_classe["Dossard"] == dossard_actif].iloc[0]

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

        # Simulateur de passage
        st.subheader("📡 Simulateur de passage")
        col_sim1, col_sim2, col_sim3, col_sim4 = st.columns(4)
        heure_actuelle = datetime.datetime.now().strftime("%H:%M:%S")
        date_actuelle = datetime.datetime.now().strftime("%Y-%m-%d")
        
        def enregistrer_passage(plot_nom):
            nouveau_passage = pd.DataFrame([{
                "Classe": classe_active,
                "Dossard": dossard_actif,
                "Plot": plot_nom,
                "Heure": heure_actuelle,
                "Date": date_actuelle
            }])
            
            try:
                passages_actuels = conn.read(worksheet="passages", ttl=0)
                passages_maj = pd.concat([passages_actuels, nouveau_passage], ignore_index=True)
                conn.update(worksheet="passages", data=passages_maj)
                st.success(f"Passage '{plot_nom}' enregistré dans Google Sheets !")
            except Exception:
                if "passages_local" not in st.session_state:
                    st.session_state.passages_local = pd.DataFrame(columns=["Classe", "Dossard", "Plot", "Heure", "Date"])
                st.session_state.passages_local = pd.concat([st.session_state.passages_local, nouveau_passage], ignore_index=True)
                st.info(f"Passage '{plot_nom}' enregistré en local.")

        if col_sim1.button("Départ (0m)"):
            enregistrer_passage("Départ")
        if col_sim2.button("Plot 25m"):
            enregistrer_passage("25m")
        if col_sim3.button("Plot 50m"):
            enregistrer_passage("50m")
        if col_sim4.button("Tournant 75m"):
            enregistrer_passage("75m")

        # Historique de la classe / de l'élève
        st.markdown("### 📋 Historique de vos passages")
        try:
            df_passages_actuel = conn.read(worksheet="passages", ttl=0)
        except Exception:
            df_passages_actuel = st.session_state.get("passages_local", pd.DataFrame())

        if not df_passages_actuel.empty:
            df_eleve = df_passages_actuel[(df_passages_actuel["Classe"] == classe_active) & (df_passages_actuel["Dossard"] == dossard_actif)]
            if not df_eleve.empty:
                st.table(df_eleve.tail(5))
            else:
                st.write("Aucun passage enregistré pour ce dossard.")
        else:
            st.write("Aucun passage enregistré pour l'instant.")
    else:
        st.warning("Aucun élève trouvé pour cette classe.")

# --- ESPACE PROFESSEUR (SÉCURISÉ) ---
elif mode == "Espace Professeur (Sécurisé)":
    st.title(f"🔒 Administration - Classe : {classe_active}")
    code_pin = st.text_input("Entrez le code professeur :", type="password")
    
    if code_pin == "EPS2026":
        st.success("Accès administrateur déverrouillé.")
        
        st.subheader(f"📊 Gestion des élèves de la classe {classe_active}")
        edited_df = st.data_editor(df_eleves_classe, num_rows="dynamic")
        
        if st.button("Enregistrer les modifications dans Google Sheets"):
            try:
                df_autres_classes = df_eleves[df_eleves["Classe"] != classe_active] if "Classe" in df_eleves.columns else pd.DataFrame()
                df_global_maj = pd.concat([df_autres_classes, edited_df], ignore_index=True)
                conn.update(worksheet="eleves", data=df_global_maj)
                st.success("Modifications synchronisées avec Google Sheets avec succès !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la mise à jour : {e}")

        st.subheader("⚙️ Actions de séance")
        if st.button("Effacer l'historique des passages de cette classe"):
            try:
                df_passages_actuel = conn.read(worksheet="passages", ttl=0)
                df_passages_nettoye = df_passages_actuel[df_passages_actuel["Classe"] != classe_active]
                conn.update(worksheet="passages", data=df_passages_nettoye)
                st.success("Historique de la classe effacé de Google Sheets.")
                st.rerun()
            except Exception:
                if "passages_local" in st.session_state:
                    st.session_state.passages_local = st.session_state.passages_local[st.session_state.passages_local["Classe"] != classe_active]
                st.success("Historique local effacé.")
    else:
        st.warning("Veuillez saisir le code PIN (`EPS2026`) pour accéder aux réglages de la classe.")
