import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="TempoLab - Demi-fond & RFID",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN HAUT CONTRASTE (OPTIMISÉ PLEIN SOLEIL) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #111418 !important; border-right: 2px solid #262a33; }
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stDataFrame"] *, [data-testid="stTable"] *, th, td { color: #000000 !important; }
    div[data-testid="stMetric"], div.stAlert { background-color: #16181d; border: 2px solid #333842; border-radius: 10px; padding: 10px; }
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
    .stButton>button:hover { background-color: #58a6ff !important; color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISATION DE LA CONNEXION ET DES DONNÉES (MODE HYBRIDE) ---
conn = None
use_gsheets = False

try:
    conn = st.connection("gsheets", type="gsheets")
    df_eleves = conn.read(worksheet="eleves", ttl=0)
    use_gsheets = True
    try:
        df_passages = conn.read(worksheet="passages_rfid", ttl=0)
    except Exception:
        df_passages = pd.DataFrame(columns=["Classe", "Seance", "Dossard", "Nom", "Scenario", "Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Niveau"])
except Exception:
    # Données de secours locales multi-classes si Google Sheets n'est pas branché
    if "eleves" not in st.session_state:
        classes_ref = ["6e4", "5e5", "5e7", "4e5", "3e5", "3eA"]
        noms_test = ["Arnaud Lucas", "Bernard Emma", "Bouvier Nathan", "Carre Manon", "David Hugo"]
        data_secours = []
        for cl in classes_ref:
            for idx, nom in enumerate(noms_test):
                data_secours.append({
                    "Classe": cl,
                    "Dossard": int(cl[0]) * 100 + idx + 1,
                    "Nom": f"{nom}",
                    "VMA": 12.0 + idx * 0.6,
                    "Objectif_pct": 80
                })
        st.session_state.eleves = pd.DataFrame(data_secours)
    df_eleves = st.session_state.eleves

    if "passages_local" not in st.session_state:
        st.session_state.passages_local = pd.DataFrame(columns=["Classe", "Seance", "Dossard", "Nom", "Scenario", "Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Niveau"])
    df_passages = st.session_state.passages_local

# --- MENU LATÉRAL : TOUR DE CONTRÔLE ---
st.sidebar.title("🧭 TempoLab - RFID")

# Vos 6 classes de référence
list_classes = ["6e4", "5e5", "5e7", "4e5", "3e5", "3eA"]
if "Classe" in df_eleves.columns:
    classes_dispo = sorted(df_eleves["Classe"].unique().tolist())
    list_classes = list(set(list_classes + classes_dispo))

classe_active = st.sidebar.selectbox("📂 Choisir la classe :", list_classes)

st.sidebar.markdown("---")
mode_navigation = st.sidebar.radio("Mode d'affichage :", [
    "📊 Tableau de Bord & Flux RFID",
    "🏃 Fiche Élève & Analyse Graphique",
    "🔒 Espace Professeur (Admin / Import)"
])

df_eleves_classe = df_eleves[df_eleves["Classe"] == classe_active] if "Classe" in df_eleves.columns else df_eleves

# Fonction d'évaluation aux 4 niveaux institutionnels
def evaluer_niveau(ecart):
    abs_e = abs(ecart)
    if abs_e <= 25:
        return "🟢 Acquis"
    elif abs_e <= 60:
        return "🟠 En cours d'acquisition"
    elif ecart > 60:
        return "🌟 Dépassé"
    else:
        return "🔴 Non acquis"

# =========================================================================
# 1. TABLEAU DE BORD & FLUX RFID (VUE GLOBALE CLASSE)
# =========================================================================
if mode_navigation == "📊 Tableau de Bord & Flux RFID":
    st.title(f"📊 Tableau de Bord - Classe : {classe_active}")
    st.info("Visualisez le récapitulatif global de la classe et filtrez par séance pour analyser les retours des balises et puces RFID.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        try:
            df_src = conn.read(worksheet="passages_rfid", ttl=0) if (use_gsheets and conn is not None) else st.session_state.get("passages_local", pd.DataFrame())
        except Exception:
            df_src = st.session_state.get("passages_local", pd.DataFrame())

        seances_dispo = ["Séance du jour (En direct)"]
        if not df_src.empty and "Seance" in df_src.columns:
            s_classe = df_src[df_src["Classe"] == classe_active]["Seance"].unique().tolist()
            seances_dispo = list(set(seances_dispo + s_classe))

        seance_filtre = st.selectbox("🎯 Filtrer par Séance :", seances_dispo)

    with col_f2:
        st.markdown("<br>", unsafe_allow_html=True)
        simuler_rfid = st.button("📡 Simuler un passage de puce RFID en direct")

    if simuler_rfid and not df_eleves_classe.empty:
        eleve_sample = df_eleves_classe.iloc[0]
        point_rfid = pd.DataFrame([{
            "Classe": classe_active,
            "Seance": "Séance du jour (En direct)",
            "Dossard": eleve_sample["Dossard"],
            "Nom": eleve_sample["Nom"],
            "Scenario": "Option 1 : 3/6/3 + 9 + 3",
            "Minute": 5,
            "Distance_Reelle": 650,
            "Distance_Ideale": 600,
            "Ecart_m": 50,
            "Niveau": evaluer_niveau(50)
        }])
        if use_gsheets and conn is not None:
            try:
                df_act = conn.read(worksheet="passages_rfid", ttl=0)
                conn.update(worksheet="passages_rfid", data=pd.concat([df_act, point_rfid], ignore_index=True))
            except Exception:
                pass
        st.session_state.passages_local = pd.concat([st.session_state.get("passages_local", pd.DataFrame()), point_rfid], ignore_index=True)
        st.success(f"Flux RFID capté pour {eleve_sample['Nom']} !")
        st.rerun()

    st.markdown("---")

    if not df_eleves_classe.empty:
        st.subheader("📋 Liste officielle de la classe")
        df_recap = df_eleves_classe.copy()
        df_recap["Vitesse Cible (km/h)"] = (df_recap["VMA"] * (df_recap["Objectif_pct"] / 100)).round(2)
        st.dataframe(df_recap[["Dossard", "Nom", "VMA", "Objectif_pct", "Vitesse Cible (km/h)"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader(f"📜 Historique des passages (Filtre : {seance_filtre})")
        
        if not df_src.empty:
            df_filtre = df_src[df_src["Classe"] == classe_active]
            if seance_filtre != "Séance du jour (En direct)":
                df_filtre = df_filtre[df_filtre["Seance"] == seance_filtre]
            
            if not df_filtre.empty:
                st.dataframe(df_filtre[["Dossard", "Nom", "Scenario", "Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Niveau"]], use_container_width=True, hide_index=True)
            else:
                st.info("Aucun passage enregistré pour ce filtre.")
        else:
            st.info("En attente des premiers flux de données des puces RFID...")
    else:
        st.warning("Aucun élève enregistré pour cette classe.")

# =========================================================================
# 2. FICHE ÉLÈVE & ANALYSE GRAPHIQUE (DOUBLE COURBE & CURSEUR VMA)
# =========================================================================
elif mode_navigation == "🏃 Fiche Élève & Analyse Graphique":
    st.title(f"🏃 Analyse Individuelle - Classe : {classe_active}")

    if not df_eleves_classe.empty:
        df_eleves_classe["Label"] = df_eleves_classe["Dossard"].astype(str) + " - " + df_eleves_classe["Nom"]
        choix_eleve = st.selectbox("🎯 Sélectionner l'élève :", df_eleves_classe["Label"])
        
        dossard_actif = int(choix_eleve.split(" - ")[0])
        eleve_info = df_eleves_classe[df_eleves_classe["Dossard"] == dossard_actif].iloc[0]

        st.markdown("---")

        scenario = st.selectbox(
            "🧩 Scénario de course choisi par l'élève :",
            [
                "Option 1 : 3/6/3 + 9 + 3 (Total 24 min)",
                "Option 2 : 3/6/3 + 12 (Total 24 min)",
                "Option 3 : 6/3 + 9 + 1.3 + 1.3 (Total ~22 min)",
                "Option 4 : 9 + 6 + 3 (Total 18 min)"
            ]
        )
        duree_max = 24 if "24 min" in scenario else (22 if "22 min" in scenario else 18)

        st.markdown("### ⚡ Réglage du Contrat & Intensité")
        vma_eleve = float(eleve_info["VMA"])
        pct_initial = int(eleve_info.get("Objectif_pct", 80))
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric("VMA de référence", f"{vma_eleve} km/h")
        with col_c2:
            pct_vma_curseur = st.slider("Curseur d'intensité (% VMA) :", min_value=50, max_value=110, value=pct_initial, step=5)

        vitesse_m_min = ((vma_eleve * (pct_vma_curseur / 100)) * 1000) / 3600 * 60
        st.info(f"📌 **Vitesse cible calculée :** {vitesse_m_min:.1f} mètres par minute.")

        st.markdown("---")

        st.subheader("⏱️ Simulation de passage RFID (Minute par minute)")
        min_test = st.selectbox("Minute test :", list(range(1, duree_max + 1)))
        dist_reelle_test = st.number_input("Distance réelle relevée par la puce RFID (m) :", min_value=0, max_value=5000, value=int(vitesse_m_min * min_test), step=25)
        
        if st.button("Enregistrer ce point RFID"):
            dist_ideale = vitesse_m_min * min_test
            ecart = dist_reelle_test - dist_ideale
            niveau_actuel = evaluer_niveau(ecart)
            
            nouveau_point = pd.DataFrame([{
                "Classe": classe_active,
                "Seance": f"Scénario ({scenario[:8]})",
                "Dossard": dossard_actif,
                "Nom": eleve_info["Nom"],
                "Scenario": scenario,
                "Minute": min_test,
                "Distance_Reelle": dist_reelle_test,
                "Distance_Ideale": dist_ideale,
                "Ecart_m": ecart,
                "Niveau": niveau_actuel
            }])
            
            if use_gsheets and conn is not None:
                try:
                    df_a = conn.read(worksheet="passages_rfid", ttl=0)
                    conn.update(worksheet="passages_rfid", data=pd.concat([df_a, nouveau_point], ignore_index=True))
                except Exception:
                    pass
            
            st.session_state.passages_local = pd.concat([st.session_state.get("passages_local", pd.DataFrame()), nouveau_point], ignore_index=True)
            st.success(f"Point de la minute {min_test} enregistré !")

        st.markdown("---")
        st.subheader(f"📈 Analyse & Courbe d'Allure - {eleve_info['Nom']}")

        try:
            df_src_eleve = conn.read(worksheet="passages_rfid", ttl=0) if (use_gsheets and conn is not None) else st.session_state.get("passages_local", pd.DataFrame())
        except Exception:
            df_src_eleve = st.session_state.get("passages_local", pd.DataFrame())

        if not df_src_eleve.empty:
            df_indiv = df_src_eleve[(df_src_eleve["Classe"] == classe_active) & (df_src_eleve["Dossard"] == dossard_actif)]
            
            if not df_indiv.empty:
                df_indiv = df_indiv.sort_values(by="Minute")
                dernier = df_indiv.iloc[-1]
                ecart_val = dernier["Ecart_m"]
                niveau_courant = dernier["Niveau"]

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Distance Réelle", f"{dernier['Distance_Reelle']} m")
                m2.metric("Distance Idéale", f"{int(dernier['Distance_Ideale'])} m")
                
                if ecart_val >= 0:
                    m3.metric("Écart au temps", f"+{int(ecart_val)} m", delta="En avance", delta_color="inverse")
                else:
                    m3.metric("Écart au temps", f"{int(ecart_val)} m", delta="En retard", delta_color="inverse")
                
                m4.metric("Niveau évalué", niveau_courant)

                st.markdown("##### 📉 Double Courbe (Allure Idéale vs Allure Réelle Puce RFID) :")
                df_graph = df_indiv.set_index("Minute")[["Distance_Reelle", "Distance_Ideale"]]
                st.line_chart(df_graph)
            else:
                st.info("Aucun passage RFID enregistré pour cet élève.")
        else:
            st.info("Base de données vide pour l'instant.")
    else:
        st.warning("Aucun élève dans cette classe.")

# =========================================================================
# 3. ESPACE PROFESSEUR (ADMIN / IMPORT)
# =========================================================================
elif mode_navigation == "🔒 Espace Professeur (Admin / Import)":
    st.title(f"🔒 Administration - Classe : {classe_active}")
    code_pin = st.text_input("Code professeur :", type="password")
    
    if code_pin == "EPS2026":
        st.success("Accès administrateur déverrouillé.")
        
        st.subheader("📥 Importer vos listes (6e4, 5e5, 5e7, 4e5, 3e5, 3eA)")
        uploaded_file = st.file_uploader("Fichier CSV ou Excel (Colonnes : Classe, Dossard, Nom, VMA, Objectif_pct)", type=["csv", "xlsx"])
        
        if uploaded_file is not None:
            try:
                df_upl = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                st.write("Aperçu :", df_upl.head(3))
                if st.button("Valider et injecter dans Google Sheets"):
                    if use_gsheets and conn is not None:
                        conn.update(worksheet="eleves", data=df_upl)
                        st.success("Base élèves mise à jour avec succès dans Sheets !")
                        st.rerun()
                    else:
                        st.session_state.eleves = df_upl
                        st.success("Base mise à jour en local !")
                        st.rerun()
            except Exception as e:
                st.error(f"Erreur : {e}")

        st.markdown("---")
        st.subheader(f"📊 Édition manuelle - Classe {classe_active}")
        edited = st.data_editor(df_eleves_classe, num_rows="dynamic")
        
        if st.button("Enregistrer les modifications"):
            df_autres = df_eleves[df_eleves["Classe"] != classe_active] if "Classe" in df_eleves.columns else pd.DataFrame()
            df_total = pd.concat([df_autres, edited], ignore_index=True)
            if use_gsheets and conn is not None:
                conn.update(worksheet="eleves", data=df_total)
                st.success("Synchronisé avec Google Sheets !")
            else:
                st.session_state.eleves = df_total
                st.success("Enregistré en local !")
            st.rerun()
    else:
        st.warning("Saisissez le code PIN (`EPS2026`) pour accéder aux réglages.")
