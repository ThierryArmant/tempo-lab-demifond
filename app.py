import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="TempoLabDemifond",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN EXTERIEUR HAUT CONTRASTE (VALIDÉ : Fond noir, texte blanc, boutons bleus texte noir) ---
st.markdown("""
    <style>
    /* Fond global de l'application */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Fond sombre et net sur la barre latérale */
    [data-testid="stSidebar"] {
        background-color: #111418 !important;
        border-right: 2px solid #262a33;
    }
    
    /* Forcer tous les textes en blanc pour un contraste maximal au soleil */
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Textes et instructions du File Uploader en blanc lisible */
    [data-testid="stFileUploader"] section, [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span {
        color: #ffffff !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: #16181d !important;
        border: 2px dashed #388bfd !important;
    }
    
    /* Style des conteneurs / cartes métriques bien détachés */
    div[data-testid="stMetric"], div.stAlert {
        background-color: #16181d;
        border: 2px solid #333842;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* BOUTONS : Fond bleu vif et ÉCRITURE NOIRE pour un contraste choc au soleil */
    .stButton>button {
        width: 100%;
        background-color: #388bfd !important;
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 18px !important;
        border-radius: 8px;
        border: 2px solid #ffffff;
        padding: 12px;
    }
    .stButton>button:hover {
        background-color: #58a6ff !important;
        color: #000000 !important;
        border-color: #388bfd;
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

list_classes = sorted(df_eleves["Classe"].unique().tolist()) if "Classe" in df_eleves.columns else ["6ème A"]
classe_active = st.sidebar.selectbox("📂 Choisir la classe :", list_classes)

st.sidebar.markdown("---")
mode = st.sidebar.radio("Espace :", ["Espace Élève / Terrain", "Espace Professeur (Sécurisé)"])

df_eleves_classe = df_eleves[df_eleves["Classe"] == classe_active] if "Classe" in df_eleves.columns else df_eleves

# --- ESPACE ÉLÈVE / TERRAIN ---
if mode == "Espace Élève / Terrain":
    st.title(f"🏃 TempoLabDemifond - Classe : {classe_active}")
    st.info("Sélectionne ton dossard, choisis ta distance et ton intensité pour définir ton contrat d'allure.")

    if not df_eleves_classe.empty:
        dossard_actif = st.selectbox("Sélectionne ton dossard :", df_eleves_classe["Dossard"])
        eleve_info = df_eleves_classe[df_eleves_classe["Dossard"] == dossard_actif].iloc[0]

        vma = eleve_info["VMA"]

        # --- SAISIE LIBRE DE L'OBJECTIF PAR L'ÉLÈVE ---
        col_saisie1, col_saisie2 = st.columns(2)
        with col_saisie1:
            distance_choisie = st.number_input("📏 Ta distance cible (en mètres) :", min_value=100, max_value=3000, value=int(eleve_info.get("Distance_cible_m", 600)), step=50)
        with col_saisie2:
            pct_choisi = st.slider("⚡ Ton intensité (% de VMA) :", min_value=50, max_value=110, value=int(eleve_info.get("Objectif_pct", 80)), step=5)

        vitesse_cible = vma * (pct_choisi / 100)
        
        # Calcul du temps théorique indicatif (en minutes/secondes)
        temps_secondes_estime = (distance_choisie / (vitesse_cible * 1000 / 3600)) if vitesse_cible > 0 else 0
        minutes_est = int(temps_secondes_estime // 60)
        secondes_est = int(temps_secondes_estime % 60)

        st.markdown("---")
        # Bannière d'objectif dynamique personnalisée par l'élève
        st.success(f"📌 **OBJECTIF CONTRAT :** Parcourir **{distance_choisie} mètres** à **{pct_choisi}% VMA** (soit **{vitesse_cible:.2f} km/h** | Temps estimé : **{minutes_est}m {secondes_est:02d}s**).")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Élève", eleve_info["Nom"])
        col2.metric("VMA", f"{vma} km/h")
        col3.metric("Contrat", f"{pct_choisi}% VMA")
        col4.metric("Vitesse Cible", f"{vitesse_cible:.2f} km/h")

        # Simulateur de passage
        st.subheader("📡 Simulateur de passage terrain")
        col_sim1, col_sim2, col_sim3, col_sim4 = st.columns(4)
        heure_actuelle_obj = datetime.datetime.now()
        heure_str = heure_actuelle_obj.strftime("%H:%M:%S")
        date_str = heure_actuelle_obj.strftime("%Y-%m-%d")
        
        def enregistrer_passage(plot_nom):
            nouveau_passage = pd.DataFrame([{
                "Classe": classe_active,
                "Dossard": dossard_actif,
                "Plot": plot_nom,
                "Heure": heure_str,
                "Date": date_str
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

        # Graphique et historique
        st.markdown("---")
        st.subheader("📈 Courbe d'analyse de course")
        
        try:
            df_passages_actuel = conn.read(worksheet="passages", ttl=0)
        except Exception:
            df_passages_actuel = st.session_state.get("passages_local", pd.DataFrame())

        if not df_passages_actuel.empty:
            df_eleve = df_passages_actuel[(df_passages_actuel["Classe"] == classe_active) & (df_passages_actuel["Dossard"] == dossard_actif)]
            if not df_eleve.empty:
                st.table(df_eleve.tail(5))
                
                mapping_plots = {"Départ": 0, "25m": 25, "50m": 50, "75m": 75}
                df_eleve_graph = df_eleve.copy()
                df_eleve_graph["Distance_Metres"] = df_eleve_graph["Plot"].map(mapping_plots)
                df_eleve_graph = df_eleve_graph.sort_values(by="Heure")
                
                if len(df_eleve_graph) > 1:
                    chart_data = df_eleve_graph.set_index("Heure")[["Distance_Metres"]]
                    st.line_chart(chart_data)
                else:
                    st.info("Valide au moins 2 plots pour visualiser ta courbe.")
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
        
        st.subheader("📥 Importer une liste d'élèves (Fichier CSV ou Excel)")
        uploaded_file = st.file_uploader("Glissez-déposez votre fichier ici (Colonnes : Classe, Dossard, Nom, VMA, Objectif_pct, Distance_cible_m)", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.write("Aperçu du fichier importé :", df_upload.head(3))
                if st.button("Valider et remplacer la base élèves par ce fichier"):
                    try:
                        conn.update(worksheet="eleves", data=df_upload)
                        st.success("Base élèves mise à jour avec succès depuis le fichier !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la synchronisation Google Sheets : {e}")
            except Exception as e:
                st.error(f"Erreur de lecture du fichier : {e}")

        st.markdown("---")
        st.subheader(f"📊 Modification manuelle - Classe {classe_active}")
        edited_df = st.data_editor(df_eleves_classe, num_rows="dynamic")
        
        if st.button("Enregistrer les modifications de la classe"):
            try:
                df_autres_classes = df_eleves[df_eleves["Classe"] != classe_active] if "Classe" in df_eleves.columns else pd.DataFrame()
                df_global_maj = pd.concat([df_autres_classes, edited_df], ignore_index=True)
                conn.update(worksheet="eleves", data=df_global_maj)
                st.success("Modifications synchronisées avec Google Sheets avec succès !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la mise à jour : {e}")

        st.markdown("---")
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
