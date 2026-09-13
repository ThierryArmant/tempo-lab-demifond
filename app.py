import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="TempoLabDemifond",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN EXTERIEUR HAUT CONTRASTE ---
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #111418 !important;
        border-right: 2px solid #262a33;
    }
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    [data-testid="stDataFrame"] *, [data-testid="stTable"] *, th, td {
        color: #000000 !important;
    }
    [data-testid="stExpander"] *, [data-testid="stExpander"] p, [data-testid="stExpander"] span {
        color: #000000 !important;
    }
    [data-testid="stExpander"] {
        background-color: #f0f2f6 !important;
        border: 2px solid #388bfd !important;
        border-radius: 8px;
    }
    [data-testid="stFileUploader"] section, [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span {
        color: #ffffff !important;
    }
    [data-testid="stFileUploader"] section {
        background-color: #16181d !important;
        border: 2px dashed #388bfd !important;
    }
    div[data-testid="stMetric"], div.stAlert {
        background-color: #16181d;
        border: 2px solid #333842;
        border-radius: 10px;
        padding: 10px;
    }
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

# --- BASE DE DONNÉES DES PALIERS VMA (Léger-Boucher & Vaussenat simplifiés) ---
# Dictionnaire indicatif Palier -> Vitesse VMA (km/h)
TABLE_VMA = {
    "Palier 1 (8.0 km/h)": 8.0, "Palier 2 (8.5 km/h)": 8.5, "Palier 3 (9.0 km/h)": 9.0,
    "Palier 4 (9.5 km/h)": 9.5, "Palier 5 (10.0 km/h)": 10.0, "Palier 6 (10.5 km/h)": 10.5,
    "Palier 7 (11.0 km/h)": 11.0, "Palier 8 (11.5 km/h)": 11.5, "Palier 9 (12.0 km/h)": 12.0,
    "Palier 10 (12.5 km/h)": 12.5, "Palier 11 (13.0 km/h)": 13.0, "Palier 12 (13.5 km/h)": 13.5,
    "Palier 13 (14.0 km/h)": 14.0, "Palier 14 (14.5 km/h)": 14.5, "Palier 15 (15.0 km/h)": 15.0,
    "Palier 16 (15.5 km/h)": 15.5, "Palier 17 (16.0 km/h)": 16.0, "Palier 18 (16.5 km/h)": 16.5,
    "Palier 19 (17.0 km/h)": 17.0, "Palier 20 (17.5 km/h)": 17.5
}

# --- INITIALISATION DE LA CONNEXION ET DES DONNÉES ---
conn = None
use_gsheets = False

try:
    conn = st.connection("gsheets", type="gsheets")
    df_eleves = conn.read(worksheet="eleves", ttl=0)
    use_gsheets = True
    try:
        df_seances_saved = conn.read(worksheet="seances", ttl=0)
    except Exception:
        df_seances_saved = pd.DataFrame(columns=["Classe", "Date", "Mode", "Dossard", "Nom", "Details_Performance"])
except Exception:
    if "eleves" not in st.session_state:
        # Données de test multi-classes (6A, 5B, 4D, 3A)
        st.session_state.eleves = pd.DataFrame({
            "Classe": ["6ème A", "6ème A", "5ème B", "5ème B", "4ème D", "4ème D", "3ème A", "3ème A"],
            "Dossard": [101, 102, 201, 202, 401, 402, 301, 302],
            "Nom": ["Arnaud Lucas", "Bernard Emma", "Durand Thomas", "Garnier Louis", "Henry Lucas", "Lemaire Tom", "Simon Enzo", "Vidal Lucas"],
            "VMA": [14.0, 12.5, 12.0, 13.0, 14.8, 15.5, 15.1, 13.9],
            "Objectif_pct": [80, 75, 80, 85, 80, 90, 85, 80],
            "Distance_cible_m": [600, 500, 600, 800, 600, 1000, 800, 600]
        })
    df_eleves = st.session_state.eleves

    if "seances_local" not in st.session_state:
        st.session_state.seances_local = pd.DataFrame(columns=["Classe", "Date", "Mode", "Dossard", "Nom", "Details_Performance"])
    df_seances_saved = st.session_state.seances_local

# --- BARRE LATÉRALE : NAVIGATION & CLASSES ---
st.sidebar.title("🧭 TempoLabDemifond")

list_classes = sorted(df_eleves["Classe"].unique().tolist()) if "Classe" in df_eleves.columns else ["6ème A"]
classe_active = st.sidebar.selectbox("📂 Choisir la classe :", list_classes)

st.sidebar.markdown("---")
mode_seance = st.sidebar.radio("Mode de Séance :", [
    "📊 Tableau de Bord & Feedback", 
    "🏃 Demi-fond (Contrat / Plots)", 
    "⚡ Test VMA (Vaussenat / Léger-Boucher)", 
    "🔄 Intermittent (30-30 ou 45-15)", 
    "🔒 Espace Professeur (Admin)"
])

df_eleves_classe = df_eleves[df_eleves["Classe"] == classe_active] if "Classe" in df_eleves.columns else df_eleves

# =========================================================================
# 1. TABLEAU DE BORD & FEEDBACK (ACCUEIL TEMPS RÉEL)
# =========================================================================
if mode_seance == "📊 Tableau de Bord & Feedback":
    st.title(f"📊 Feedback en Temps Réel - Classe : {classe_active}")
    st.info("Retrouvez ci-dessous la vue globale de la classe, les contrats en cours et l'historique des séances enregistrées pour ajuster vos feedbacks.")

    if not df_eleves_classe.empty:
        st.subheader("📋 Liste officielle et contrats de la classe")
        df_vue = df_eleves_classe.copy()
        df_vue["Vitesse Cible (km/h)"] = (df_vue["VMA"] * (df_vue["Objectif_pct"] / 100)).round(2)
        df_affichage = df_vue[["Dossard", "Nom", "VMA", "Objectif_pct", "Distance_cible_m", "Vitesse Cible (km/h)"]].copy()
        df_affichage.columns = ["Dossard", "Nom", "VMA (km/h)", "Contrat (% VMA)", "Distance Cible (m)", "Vitesse Cible (km/h)"]
        st.dataframe(df_affichage, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📜 Historique des séances enregistrées pour cette classe")
        
        try:
            df_seances_actuel = conn.read(worksheet="seances", ttl=0) if (use_gsheets and conn is not None) else st.session_state.get("seances_local", pd.DataFrame())
        except Exception:
            df_seances_actuel = st.session_state.get("seances_local", pd.DataFrame())

        if not df_seances_actuel.empty:
            df_seances_classe = df_seances_actuel[df_seances_actuel["Classe"] == classe_active]
            if not df_seances_classe.empty:
                st.dataframe(df_seances_classe, use_container_width=True, hide_index=True)
            else:
                st.write("Aucune séance enregistrée pour cette classe pour l'instant.")
        else:
            st.write("Aucune séance enregistrée dans la base.")
    else:
        st.warning("Aucun élève trouvé pour cette classe.")

# =========================================================================
# 2. ESPACE DEMI-FOND (CONTRAT / PLOTS)
# =========================================================================
elif mode_seance == "🏃 Demi-fond (Contrat / Plots)":
    st.title(f"🏃 Demi-fond - Classe : {classe_active}")
    
    if not df_eleves_classe.empty:
        # Choix du mode de saisie (Puce / Tactile vs Manuel)
        type_saisie = st.radio("🛠️ Mode de chronométrage :", ["Mode Tactile / Manuel (Enseignant ou Élève)", "Mode Puce / Détecteur (Simulation automatique)"], horizontal=True)

        df_eleves_classe["Label_Eleve"] = df_eleves_classe["Dossard"].astype(str) + " - " + df_eleves_classe["Nom"]
        choix_eleve = st.selectbox("🎯 Sélectionner l'élève actif :", df_eleves_classe["Label_Eleve"])
        
        dossard_actif = int(choix_eleve.split(" - ")[0])
        eleve_info = df_eleves_classe[df_eleves_classe["Dossard"] == dossard_actif].iloc[0]

        vma = float(eleve_info["VMA"])
        if vma <= 0 or pd.isna(vma):
            st.error("⚠️ Aucune VMA valide pour cet élève. Veuillez la renseigner.")
            vma = st.number_input("Saisir la VMA (km/h) :", min_value=5.0, max_value=25.0, value=12.0)

        # Paramétrage protocole
        col_p, col_d, col_c = st.columns(3)
        with col_p:
            ecart_plots = st.selectbox("📌 Écart plots :", options=[15, 20, 25, 50], index=2)
        with col_d:
            liste_d = list(range(100, 3005, 25))
            def_d = int(eleve_info.get("Distance_cible_m", 600))
            if def_d not in liste_d: def_d = 600
            distance_choisie = st.selectbox("📏 Distance cible (m) :", options=liste_d, index=liste_d.index(def_d))
        with col_c:
            pct_choisi = st.slider("⚡ Intensité (% VMA) :", 50, 110, int(eleve_info.get("Objectif_pct", 80)), 5)

        v_kmh = vma * (pct_choisi / 100)
        v_ms = (v_kmh * 1000) / 3600
        t_est = (distance_choisie / v_ms) if v_ms > 0 else 0
        
        st.success(f"📌 **Contrat :** {distance_choisie}m à {pct_choisi}% VMA ({v_kmh:.2f} km/h) | Temps idéal : {int(t_est//60)}m {int(t_est%60):02d}s")

        with st.expander(f"⏱️ Tableau de marche idéal - {eleve_info['Nom']}"):
            d_plots = list(range(ecart_plots, distance_choisie + ecart_plots, ecart_plots))
            if d_plots[-1] != distance_choisie: d_plots.append(distance_choisie)
            t_marche = [{"Plot": f"{d}m", "Temps idéal": f"{int((d/v_ms)//60)}m {int((d/v_ms)%60):02d}s"} for d in d_plots]
            st.table(pd.DataFrame(t_marche))

        noms_plots = ["Départ"] + [f"{i * ecart_plots}m" for i in range(1, (distance_choisie // ecart_plots) + 1)]
        if (distance_choisie % ecart_plots) != 0: noms_plots.append(f"{distance_choisie}m")

        if type_saisie == "Mode Tactile / Manuel (Enseignant ou Élève)":
            st.subheader("📡 Simulateur de passage terrain")
            cols_sim = st.columns(min(len(noms_plots), 4))
            for idx, p_nom in enumerate(noms_plots):
                if cols_sim[idx % len(cols_sim)].button(p_nom, key=f"btn_{p_nom}"):
                    # Enregistrement séance
                    nouvelle_ L = pd.DataFrame([{
                        "Classe": classe_active,
                        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Mode": "Demi-fond",
                        "Dossard": dossard_actif,
                        "Nom": eleve_info["Nom"],
                        "Details_Performance": f"Passage validé : {p_nom} ({distance_choisie}m à {pct_choisi}%VMA)"
                    }])
                    if use_gsheets and conn is not None:
                        try:
                            s_act = conn.read(worksheet="seances", ttl=0)
                            conn.update(worksheet="seances", data=pd.concat([s_act, nouvelle_ L], ignore_index=True))
                        except Exception:
                            pass
                    else:
                        st.session_state.seances_local = pd.concat([st.session_state.seances_local, nouvelle_ L], ignore_index=True)
                    st.success(f"Passage '{p_nom}' enregistré et synchronisé pour le feedback !")
        else:
            st.info("📡 Mode Puce activé : En attente de détection automatique des dossards sur la ligne...")
            if st.button("Simuler un passage par puce"):
                st.success(f"Puce détectée pour {eleve_info['Nom']} !")

# =========================================================================
# 3. TEST VMA (VAUSSENAT / LÉGER-BOUCHER)
# =========================================================================
elif mode_seance == "⚡ Test VMA (Vaussenat / Léger-Boucher)":
    st.title(f"⚡ Évaluation VMA - Classe : {classe_active}")
    st.info("Sélectionnez le test réalisé, puis enregistrez le palier atteint par chaque élève pour mettre à jour sa VMA instantanément dans la base.")

    type_test = st.selectbox("Type de test :", ["Test Léger-Boucher (Pistes 20m)", "Test de Vaussenat (Pôles continus)"])

    if not df_eleves_classe.empty:
        # Saisie groupée ou individuelle des paliers de VMA
        st.subheader("📝 Saisie des résultats du test VMA")
        
        eleve_vma_choix = st.selectbox("Choisir l'élève à évaluer :", df_eleves_classe["Dossard"].astype(str) + " - " + df_eleves_classe["Nom"])
        dossard_vma = int(eleve_vma_choix.split(" - ")[0])
        
        palier_atteint = st.selectbox("Dernier palier validé :", list(TABLE_VMA.keys()))
        vma_calculee = TABLE_VMA[palier_atteint]

        st.success(f"VMA correspondante au palier : **{vma_calculee} km/h**")

        if st.button("Mettre à jour la VMA de cet élève"):
            df_eleves.loc[df_eleves["Dossard"] == dossard_vma, "VMA"] = vma_calculee
            if use_gsheets and conn is not None:
                try:
                    conn.update(worksheet="eleves", data=df_eleves)
                    st.success("VMA mise à jour dans Google Sheets avec succès !")
                except Exception as e:
                    st.error(f"Erreur de synchro : {e}")
            else:
                st.session_state.eleves = df_eleves
                st.success("VMA mise à jour en local avec succès !")
            st.rerun()

# =========================================================================
# 4. INTERMITTENT (30-30 ou 45-15)
# =========================================================================
elif mode_seance == "🔄 Intermittent (30-30 ou 45-15)":
    st.title(f"🔄 Séance Intermittente - Classe : {classe_active}")
    st.info("Saisissez les performances de vos élèves sur les blocs fractionnés (ex: nombre de répétitions ou distance totale parcourue par bloc).")

    protocole_inter = st.selectbox("Format d'effort :", ["30 - 30", "45 - 15"])
    
    if not df_eleves_classe.empty:
        eleve_inter = st.selectbox("Élève :", df_eleves_classe["Dossard"].astype(str) + " - " + df_eleves_classe["Nom"])
        dossard_inter = int(eleve_inter.split(" - ")[0])
        nom_inter = eleve_inter.split(" - ")[1]

        blocs_realises = st.number_input("Nombre de blocs / répétitions réussies :", min_value=1, max_value=30, value=10)
        distance_totale_m = st.number_input("Distance totale parcourue sur l'exercice (en mètres) :", min_value=50, max_value=5000, value=1200, step=50)

        if st.button("Enregistrer la performance intermittente"):
            nouvelle_s = pd.DataFrame([{
                "Classe": classe_active,
                "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Mode": f"Intermittent {protocole_inter}",
                "Dossard": dossard_inter,
                "Nom": nom_inter,
                "Details_Performance": f"{blocs_realises} blocs | {distance_totale_m}m parcourus"
            }])
            if use_gsheets and conn is not None:
                try:
                    s_act = conn.read(worksheet="seances", ttl=0)
                    conn.update(worksheet="seances", data=pd.concat([s_act, nouvelle_s], ignore_index=True))
                    st.success("Performance intermittente enregistrée dans Google Sheets !")
                except Exception:
                    pass
            else:
                st.session_state.seances_local = pd.concat([st.session_state.seances_local, nouvelle_s], ignore_index=True)
                st.success("Performance enregistrée en local !")

# =========================================================================
# 5. ESPACE PROFESSEUR (ADMIN)
# =========================================================================
elif mode_seance == "🔒 Espace Professeur (Admin)":
    st.title(f"🔒 Administration - Classe : {classe_active}")
    code_pin = st.text_input("Code professeur :", type="password")
    
    if code_pin == "EPS2026":
        st.success("Accès administrateur déverrouillé.")
        
        st.subheader("📥 Importer vos listes (6A, 5B, 4D, 3A...)")
        uploaded_file = st.file_uploader("Fichier CSV ou Excel (Colonnes attendues : Classe, Dossard, Nom, VMA, Objectif_pct, Distance_cible_m)", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                st.write("Aperçu :", df_upload.head(3))
                if st.button("Remplacer la base globale par ce fichier"):
                    if use_gsheets and conn is not None:
                        conn.update(worksheet="eleves", data=df_upload)
                        st.success("Base élèves mise à jour dans Google Sheets !")
                        st.rerun()
                    else:
                        st.session_state.eleves = df_upload
                        st.success("Base élèves mise à jour en local !")
                        st.rerun()
            except Exception as e:
                st.error(e)

        st.markdown("---")
        st.subheader(f"📊 Modification manuelle - {classe_active}")
        edited_df = st.data_editor(df_eleves_classe, num_rows="dynamic")
        
        if st.button("Enregistrer les modifications"):
            df_autres = df_eleves[df_eleves["Classe"] != classe_active] if "Classe" in df_eleves.columns else pd.DataFrame()
            df_global = pd.concat([df_autres, edited_df], ignore_index=True)
            if use_gsheets and conn is not None:
                conn.update(worksheet="eleves", data=df_global)
                st.success("Synchronisé avec Google Sheets !")
            else:
                st.session_state.eleves = df_global
                st.success("Enregistré en local !")
            st.rerun()
    else:
        st.warning("Saisissez le code PIN (`EPS2026`).")
