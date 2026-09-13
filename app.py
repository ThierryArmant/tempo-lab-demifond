import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="TempoLabDemifond",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN EXTERIEUR HAUT CONTRASTE (Fond noir, texte blanc, boutons bleus texte noir) ---
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

# --- INITIALISATION DE LA CONNEXION ET DES DONNÉES (MODE HYBRIDE ROBUSTE) ---
conn = None
use_gsheets = False

try:
    conn = st.connection("gsheets", type="gsheets")
    df_eleves = conn.read(worksheet="eleves", ttl=0)
    use_gsheets = True
    try:
        df_passages_saved = conn.read(worksheet="passages", ttl=0)
    except Exception:
        df_passages_saved = pd.DataFrame(columns=["Classe", "Dossard", "Plot", "Heure", "Date"])
except Exception:
    # Mode secours local si Google Sheets n'est pas branché
    if "eleves" not in st.session_state:
        noms_test = ["Arnaud Lucas", "Bernard Emma", "Bouvier Nathan", "Carre Manon", "David Hugo", 
                     "Dubois Chloé", "Durand Thomas", "Faure Clara", "Garnier Louis", "Gauthier Inès",
                     "Girard Théo", "Guerin Zoé", "Henry Lucas", "Laurent Sarah", "Lemaire Tom",
                     "Leroy Camille", "Martin Nathan", "Moreau Juliette", "Petit Hugo", "Richard Léa",
                     "Rousseau Mathis", "Roux Manon", "Simon Enzo", "Thomas Chloé", "Vidal Lucas",
                     "Vincent Emma", "Blanchard Tom", "Dumont Sarah", "Fontaine Léo", "Gauthier Maëlys"]
        st.session_state.eleves = pd.DataFrame({
            "Classe": ["6ème A"] * len(noms_test),
            "Dossard": list(range(101, 101 + len(noms_test))),
            "Nom": noms_test,
            "VMA": [14.0, 12.5, 15.2, 11.0, 13.5, 14.2, 0.0, 15.0, 13.0, 14.5,
                    12.8, 13.2, 14.8, 11.5, 15.5, 12.2, 13.8, 14.1, 12.9, 13.6,
                    14.3, 12.4, 15.1, 11.8, 13.9, 14.6, 12.6, 13.4, 14.7, 12.1],
            "Objectif_pct": [80] * len(noms_test),
            "Distance_cible_m": [600] * len(noms_test)
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
    st.info("Retrouve ton nom dans le tableau général de la classe, vérifie tes stats, puis sélectionne ton profil pour courir.")

    if not df_eleves_classe.empty:
        # --- TABLEAU DE BORD GÉNÉRAL DE LA CLASSE (VISIBLE PAR TOUS EN TEMPS RÉEL) ---
        st.subheader("📋 Tableau général des contrats de la classe")
        
        # Préparation d'une vue claire pour les élèves
        df_affichage_classe = df_eleves_classe[["Dossard", "Nom", "VMA", "Objectif_pct", "Distance_cible_m"]].copy()
        df_affichage_classe.columns = ["Dossard", "Nom", "VMA (km/h)", "Contrat (% VMA)", "Distance Cible (m)"]
        st.dataframe(df_affichage_classe, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🎯 Espace Actif de Course")

        # Sélection de l'élève pour lancer le simulateur
        df_eleves_classe["Label_Eleve"] = df_eleves_classe["Dossard"].astype(str) + " - " + df_eleves_classe["Nom"]
        choix_eleve = st.selectbox("Sélectionne ton nom pour démarrer ton chronométrage :", df_eleves_classe["Label_Eleve"])
        
        dossard_actif = int(choix_eleve.split(" - ")[0])
        eleve_info = df_eleves_classe[df_eleves_classe["Dossard"] == dossard_actif].iloc[0]

        vma_actuelle = float(eleve_info["VMA"])

        # --- CONTRÔLE OBLIGATOIRE DE LA VMA ---
        if vma_actuelle <= 0 or pd.isna(vma_actuelle):
            st.error("⚠️ **ATTENTION : Aucune VMA valide n'est enregistrée pour cet élève !** Les calculs sont impossibles.")
            st.warning("Veuillez demander au professeur de renseigner votre VMA dans l'Espace Professeur (ou indiquez-la temporairement ci-dessous).")
            vma_saisie = st.number_input("Indique ta VMA (en km/h) :", min_value=5.0, max_value=25.0, value=12.0, step=0.5)
            vma = vma_saisie
        else:
            vma = vma_actuelle

        # --- PARAMÉTRAGE DU PROTOCOLE & OBJECTIF ---
        st.subheader("⚙️ Paramétrage de ton protocole")
        col_protocole, col_dist, col_pct = st.columns(3)
        
        with col_protocole:
            ecart_plots = st.selectbox("📌 Écart entre les plots :", options=[15, 20, 25, 50], index=2)
            
        with col_dist:
            liste_distances_25m = list(range(100, 3005, 25))
            def_dist = int(eleve_info.get("Distance_cible_m", 600))
            if def_dist not in liste_distances_25m:
                def_dist = 600
            
            distance_choisie = st.selectbox(
                "📏 Distance cible (bornes de 25m) :", 
                options=liste_distances_25m, 
                index=liste_distances_25m.index(def_dist)
            )
            
        with col_pct:
            pct_choisi = st.slider("⚡ Intensité (% VMA) :", min_value=50, max_value=110, value=int(eleve_info.get("Objectif_pct", 80)), step=5)

        # Calculs cinématiques intégrés
        vitesse_cible_kmh = vma * (pct_choisi / 100)
        vitesse_ms = (vitesse_cible_kmh * 1000) / 3600
        
        st.info(f"📋 **PROTOCOLE INTÉGRÉ :** Balisage de piste tous les **{ecart_plots} mètres**.")

        temps_total_estime = (distance_choisie / vitesse_ms) if vitesse_ms > 0 else 0
        m_est = int(temps_total_estime // 60)
        s_est = int(temps_total_estime % 60)
        st.success(f"📌 **OBJECTIF CONTRAT :** Parcourir **{distance_choisie}m** à **{pct_choisi}% VMA** ({vitesse_cible_kmh:.2f} km/h) | Temps idéal : **{m_est}m {s_est:02d}s**.")

        with st.expander("⏱️ Voir mon tableau de marche idéal par plot"):
            distances_plots = list(range(ecart_plots, distance_choisie + ecart_plots, ecart_plots))
            if distances_plots[-1] != distance_choisie:
                distances_plots.append(distance_choisie)
                
            tableau_marche = []
            for d in distances_plots:
                t_sec = d / vitesse_ms if vitesse_ms > 0 else 0
                tableau_marche.append({"Plot / Distance": f"{d}m", "Temps idéal cumulé": f"{int(t_sec//60)}m {int(t_sec%60):02d}s"})
            st.table(pd.DataFrame(tableau_marche))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Élève", eleve_info["Nom"])
        col2.metric("VMA", f"{vma} km/h")
        col3.metric("Contrat", f"{pct_choisi}% VMA")
        col4.metric("Vitesse Cible", f"{vitesse_cible_kmh:.2f} km/h")

        # --- SIMULATEUR DE PASSAGE ADAPTÉ AU PROTOCOLE ---
        st.subheader("📡 Simulateur de passage terrain")
        
        noms_plots = ["Départ"] + [f"{i * ecart_plots}m" for i in range(1, (distance_choisie // ecart_plots) + 1)]
        if (distance_choisie % ecart_plots) != 0:
            noms_plots.append(f"{distance_choisie}m")

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
            
            if use_gsheets and conn is not None:
                try:
                    passages_actuels = conn.read(worksheet="passages", ttl=0)
                    passages_maj = pd.concat([passages_actuels, nouveau_passage], ignore_index=True)
                    conn.update(worksheet="passages", data=passages_maj)
                    st.success(f"Passage '{plot_nom}' enregistré dans Google Sheets !")
                    return
                except Exception:
                    pass
            
            # Mode secours local
            if "passages_local" not in st.session_state:
                st.session_state.passages_local = pd.DataFrame(columns=["Classe", "Dossard", "Plot", "Heure", "Date"])
            st.session_state.passages_local = pd.concat([st.session_state.passages_local, nouveau_passage], ignore_index=True)
            st.info(f"Passage '{plot_nom}' enregistré en local.")

        cols_simulation = st.columns(min(len(noms_plots), 4))
        for idx, plot_nom in enumerate(noms_plots):
            col_cible = cols_simulation[idx % len(cols_simulation)]
            if col_cible.button(plot_nom, key=f"btn_{plot_nom}"):
                enregistrer_passage(plot_nom)

        # Graphique et historique
        st.markdown("---")
        st.subheader("📈 Courbe d'analyse de course")
        
        try:
            df_passages_actuel = conn.read(worksheet="passages", ttl=0) if (use_gsheets and conn is not None) else st.session_state.get("passages_local", pd.DataFrame())
        except Exception:
            df_passages_actuel = st.session_state.get("passages_local", pd.DataFrame())

        if not df_passages_actuel.empty:
            df_eleve = df_passages_actuel[(df_passages_actuel["Classe"] == classe_active) & (df_passages_actuel["Dossard"] == dossard_actif)]
            if not df_eleve.empty:
                st.table(df_eleve.tail(5))
                
                mapping_plots = {"Départ": 0}
                for plot_str in noms_plots:
                    if plot_str != "Départ":
                        val_m = int(plot_str.replace("m", ""))
                        mapping_plots[plot_str] = val_m

                df_eleve_graph = df_eleve.copy()
                df_eleve_graph["Distance_Metres"] = df_eleve_graph["Plot"].map(mapping_plots)
                df_eleve_graph = df_eleve_graph.dropna(subset=["Distance_Metres"])
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
                    if use_gsheets and conn is not None:
                        try:
                            conn.update(worksheet="eleves", data=df_upload)
                            st.success("Base élèves mise à jour avec succès dans Google Sheets !")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur Google Sheets : {e}")
                    else:
                        st.session_state.eleves = df_upload
                        st.success("Base élèves mise à jour en local avec succès !")
                        st.rerun()
            except Exception as e:
                st.error(f"Erreur de lecture du fichier : {e}")

        st.markdown("---")
        st.subheader(f"📊 Modification manuelle - Classe {classe_active}")
        edited_df = st.data_editor(df_eleves_classe, num_rows="dynamic")
        
        if st.button("Enregistrer les modifications de la classe"):
            try:
                df_autres_classes = df_eleves[df_eleves["Classe"] != classe_active] if "Classe" in df_eleves.columns else pd.DataFrame()
                df_global_maj = pd.concat([df_autres_classes, edited_df], ignore_index=True)
                
                if use_gsheets and conn is not None:
                    conn.update(worksheet="eleves", data=df_global_maj)
                    st.success("Modifications synchronisées avec Google Sheets avec succès !")
                else:
                    st.session_state.eleves = df_global_maj
                    st.success("Modifications enregistrées en local avec succès !")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la mise à jour : {e}")

--------
        st.markdown("---")
        st.subheader("⚙️ Actions de séance")
        if st.button("Effacer l'historique des passages de cette classe"):
            try:
                if use_gsheets and conn is not None:
                    df_passages_actuel = conn.read(worksheet="passages", ttl=0)
                    df_passages_nettoye = df_passages_actuel[df_passages_actuel["Classe"] != classe_active]
                    conn.update(worksheet="passages", data=df_passages_nettoye)
                    st.success("Historique de la classe effacé de Google Sheets.")
                else:
                    if "passages_local" in st.session_state:
                        st.session_state.passages_local = st.session_state.passages_local[st.session_state.passages_local["Classe"] != classe_active]
                    st.success("Historique local effacé.")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")
    else:
        st.warning("Veuillez saisir le code PIN (`EPS2026`) pour accéder aux réglages de la classe.")
