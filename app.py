import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="TempoLabDemifond - Analyse d'Effort",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN HAUT CONTRASTE (Fond noir, texte blanc, tableaux lisibles) ---
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

# --- INITIALISATION DES DONNÉES (MODE HYBRIDE) ---
conn = None
use_gsheets = False

try:
    conn = st.connection("gsheets", type="gsheets")
    df_eleves = conn.read(worksheet="eleves", ttl=0)
    use_gsheets = True
    try:
        df_passages = conn.read(worksheet="passages_demifond", ttl=0)
    except Exception:
        df_passages = pd.DataFrame(columns=["Classe", "Dossard", "Nom", "Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Temps"])
except Exception:
    if "eleves" not in st.session_state:
        # Données de test pour la classe
        st.session_state.eleves = pd.DataFrame({
            "Classe": ["5ème 5"] * 5,
            "Dossard": [501, 502, 503, 504, 505],
            "Nom": ["Blanc Nathan", "Bonnet Chloé", "Brunet Lucas", "Chevalier Manon", "Clement Hugo"],
            "VMA": [13.5, 11.5, 14.8, 12.0, 13.0],
            "Objectif_pct": [80, 75, 85, 80, 80]
        })
    df_eleves = st.session_state.eleves

    if "passages_local" not in st.session_state:
        st.session_state.passages_local = pd.DataFrame(columns=["Classe", "Dossard", "Nom", "Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Temps"])
    df_passages = st.session_state.passages_local

# --- BARRE LATÉRALE ---
st.sidebar.title("🧭 TempoLab - Demi-fond")
list_classes = sorted(df_eleves["Classe"].unique().tolist()) if "Classe" in df_eleves.columns else ["5ème 5"]
classe_active = st.sidebar.selectbox("📂 Choisir la classe :", list_classes)

df_eleves_classe = df_eleves[df_eleves["Classe"] == classe_active] if "Classe" in df_eleves.columns else df_eleves

st.sidebar.markdown("---")
st.sidebar.info("🎯 **Objectif :** Gestion d'effort, fractions (3min/6min/3min ou 9min) et analyse des écarts en temps réel.")

st.title(f"🏃 Analyse de Course & Écarts - Classe : {classe_active}")

if not df_eleves_classe.empty:
    # 1. Choix du format de course pédagogique
    format_course = st.selectbox(
        "⏱️ Choisir la structure de la séance / format d'effort :",
        [
            "Option A : 9 minutes en continu (Bloc unique)",
            "Option B : 6 minutes puis 3 minutes (Fractionné progressif)",
            "Option C : 3 min / 6 min / 3 min (Alternance)"
        ]
    )

    st.markdown("---")

    # 2. Sélection de l'élève
    df_eleves_classe["Label"] = df_eleves_classe["Dossard"].astype(str) + " - " + df_eleves_classe["Nom"]
    choix_eleve = st.selectbox("🎯 Sélectionner l'élève à analyser / chronométrer :", df_eleves_classe["Label"])
    
    dossard_actif = int(choix_eleve.split(" - ")[0])
    eleve_info = df_eleves_classe[df_eleves_classe["Dossard"] == dossard_actif].iloc[0]

    vma = float(eleve_info["VMA"])
    pct_vma = int(eleve_info["Objectif_pct"])
    
    # Vitesse en m/min (très pratique pour le suivi minute par minute en demi-fond)
    vitesse_ms = (vma * (pct_vma / 100) * 1000) / 3600
    vitesse_m_min = vitesse_ms * 60

    col1, col2, col3 = st.columns(3)
    col1.metric("Élève", eleve_info["Nom"])
    col2.metric("VMA", f"{vma} km/h")
    col3.metric("Vitesse Cible", f"{vitesse_m_min:.1f} m / minute")

    st.markdown("---")

    # 3. Saisie des relevés minute par minute sur le terrain
    st.subheader("⏱️ Saisie des passages minute par minute (Suivi d'effort)")
    
    # Détermination du nombre de minutes total selon le format choisi
    max_minutes = 9
    if "Option B" in format_course: minutes_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    elif "Option C" in format_course: minutes_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    else: minutes_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    # Interface de saisie rapide pour la minute active
    minute_active = st.selectbox("Minute de course en cours :", minutes_list)
    
    # Distance idéale cumulée à cette minute précise selon la VMA et le %
    distance_ideale_cumulee = vitesse_m_min * minute_active

    col_saisie1, col_saisie2 = st.columns(2)
    with col_saisie1:
        distance_reelle_cumulee = st.number_input(
            f"Distance réelle cumulée (m) à la minute {minute_active} :", 
            min_value=0, max_value=3000, value=int(distance_ideale_cumulee), step=25
        )
    
    with col_saisie2:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_valider = st.button(f"Enregistrer le point de la minute {minute_active}")

    ecart = distance_reelle_cumulee - distance_ideale_cumulee

    if btn_valider:
        nouveau_point = pd.DataFrame([{
            "Classe": classe_active,
            "Dossard": dossard_actif,
            "Nom": eleve_info["Nom"],
            "Minute": f"Min {minute_active}",
            "Minute_num": minute_active,
            "Distance_Reelle": distance_reelle_cumulee,
            "Distance_Ideale": distance_ideale_cumulee,
            "Ecart_m": ecart,
            "Temps": datetime.datetime.now().strftime("%H:%M:%S")
        }])

        if use_gsheets and conn is not None:
            try:
                df_actuel = conn.read(worksheet="passages_demifond", ttl=0)
                df_maj = pd.concat([df_actuel, nouveau_point], ignore_index=True)
                conn.update(worksheet="passages_demifond", data=df_maj)
            except Exception:
                pass
        
        # Sauvegarde session locale
        if "passages_local" not in st.session_state:
            st.session_state.passages_local = pd.DataFrame(columns=["Classe", "Dossard", "Nom", "Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Temps"])
        
        # Éviter les doublons pour la même minute sur le même élève
        st.session_state.passages_local = st.session_state.passages_local[
            ~((st.session_state.passages_local["Dossard"] == dossard_actif) & (st.session_state.passages_local["Minute_num"] == minute_active))
        ]
        st.session_state.passages_local = pd.concat([st.session_state.passages_local, nouveau_point], ignore_index=True)
        st.success(f"Minute {minute_active} enregistrée !")

    # --- 4. AFFICHAGE DU FEEDBACK EN TEMPS RÉEL (COURBES & ÉCARTS) ---
    st.markdown("---")
    st.subheader(f"📈 Courbe d'allure et Écarts au contrat - {eleve_info['Nom']}")

    # Récupération des données enregistrées pour cet élève
    try:
        df_source = conn.read(worksheet="passages_demifond", ttl=0) if (use_gsheets and conn is not None) else st.session_state.get("passages_local", pd.DataFrame())
    except Exception:
        df_source = st.session_state.get("passages_local", pd.DataFrame())

    if not df_source.empty:
        df_eleve_cours = df_source[(df_source["Classe"] == classe_active) & (df_source["Dossard"] == dossard_actif)]
        
        if not df_eleve_cours.empty and "Minute_num" in df_eleve_cours.columns:
            df_eleve_cours = df_eleve_cours.sort_values(by="Minute_num")
            
            # Affichage de l'écart en temps réel sous forme de métrique choc
 dernier_point = df_eleve_cours.iloc[-1]
            ecart_actuel = dernier_point["Ecart_m"]
            
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Distance Réelle", f"{dernier_point['Distance_Reelle']} m")
            col_m2.metric("Distance Idéale (Contrat)", f"{int(dernier_point['Distance_Ideale'])} m")
            
            if ecart_actuel > 0:
                col_m3.metric("Écart au temps", f"+{int(ecart_actuel)} mètres", delta="En avance (Trop rapide)", delta_color="inverse")
            elif ecart_actuel < 0:
                col_m3.metric("Écart au temps", f"{int(ecart_actuel)} mètres", delta="En retard (Trop lent)", delta_color="inverse")
            else:
                col_m3.metric("Écart au temps", "0 mètre", delta="Parfait aligné sur le contrat !")

            # Tableau récapitulatif des passages de l'élève
            st.markdown("##### 📋 Tableau de marche détaillé :")
            st.dataframe(df_eleve_cours[["Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Temps"]], use_container_width=True, hide_index=True)

            # Courbe comparative (Distance Réelle vs Distance Idéale)
            st.markdown("##### 📉 Graphique comparatif (Allure Réelle vs Allure Idéale) :")
            df_graph = df_eleve_cours.set_index("Minute")[["Distance_Reelle", "Distance_Ideale"]]
            st.line_chart(df_graph)
        else:
            st.info("Aucun point de passage enregistré pour cet élève sur cette séance. Saisissez la première minute ci-dessus.")
    else:
        st.info("Aucun enregistrement pour l'instant dans la base.")
else:
    st.warning("Aucun élève trouvé dans cette classe.")
