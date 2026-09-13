import streamlit as st
import pandas as pd
import datetime

st.set_page_config(
    page_title="TempoLabDemifond - Profils Énergétiques",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN HAUT CONTRASTE ---
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
st.sidebar.info("🎯 **Analyse de course :** Choix des scénarios, registres physiologiques et suivi des écarts en temps réel.")

st.title(f"🏃 Gestion d'Allure & Profils Énergétiques - Classe : {classe_active}")

if not df_eleves_classe.empty:
    # 1. Choix de la combinaison stratégique de l'élève
    combinaison_choisie = st.selectbox(
        "🧩 Choisir la combinaison / scénario de course de l'élève :",
        [
            "Option 1 : 3/6/3 + 9 + 3 (Total 24 min)",
            "Option 2 : 3/6/3 + 12 (Total 24 min)",
            "Option 3 : 6/3 + 9 + 1.3 + 1.3 (Total ~21.6 min)",
            "Option 4 : 9 + 6 + 3 (Total 18 min)"
        ]
    )

    # --- ENCADRÉ PÉDAGOGIQUE DU PROFIL ÉNERGÉTIQUE ---
    if "Option 1" in combinaison_choisie:
        duree_totale_min = 24
        st.info(
            "🧠 **Profil Physiologique : Endurance de Longue Durée & Résistance Souple**\n\n"
            "• **Ce que tu travailles :** Ton capital aérobie global et ta capacité à maintenir un effort prolongé (24 min) malgré la fatigue musculaire et nerveuse qui s'installe par paliers.\n"
            "• **Stratégie :** Ne pars pas trop vite sur les blocs de 3 ou 6 min initiaux. L'enjeu est la régularité sur le bloc central de 9 minutes."
        )
    elif "Option 2" in combinaison_choisie:
        duree_totale_min = 24
        st.info(
            "🧠 **Profil Physiologique : Endurance Fondamentale & Maintien Prolongé**\n\n"
            "• **Ce que tu travailles :** La gestion d'une longue séquence finale de 12 minutes après un échauffement fractionné (3/6/3).\n"
            "• **Stratégie :** Le gros morceau se situe sur la fin. Tu dois lisser ton effort pour ne pas t'écrouler dans la dernière demi-heure virtuelle."
        )
    elif "Option 3" in combinaison_choisie:
        duree_totale_min = 22
        st.info(
            "🧠 **Profil Physiologique : Puissance Aérobie & Variations d'Allure (Fartlek)**\n\n"
            "• **Ce que tu travailles :** Ta capacité à encaisser des changements de rythme répétés (fractions courtes et longues alternées) tout en gérant de micro-efforts (1.3 min).\n"
            "• **Stratégie :** Sois très vigilant sur tes transitions : ne récupère pas en marchant trop lentement pour ne pas casser ta dynamique."
        )
    else:  # Option 4
        duree_totale_min = 18
        st.info(
            "🧠 **Profil Physiologique : Résistance Dure & Dégressivité d'Effort**\n\n"
            "• **Ce que tu travailles :** Un effort intense et ramassé (18 min) qui commence par le bloc le plus long (9 min) alors que tu es frais, pour finir en dégressif (6 min puis 3 min).\n"
            "• **Stratégie :** C'est un profil difficile au démarrage car le bloc de 9 min à froid demande de bien caler sa vitesse dès la 1ère minute !"
        )

    st.markdown("---")

    # 2. Sélection de l'élève
    df_eleves_classe["Label"] = df_eleves_classe["Dossard"].astype(str) + " - " + df_eleves_classe["Nom"]
    choix_eleve = st.selectbox("🎯 Sélectionner l'élève :", df_eleves_classe["Label"])
    
    dossard_actif = int(choix_eleve.split(" - ")[0])
    eleve_info = df_eleves_classe[df_eleves_classe["Dossard"] == dossard_actif].iloc[0]

    vma = float(eleve_info["VMA"])
    pct_vma = int(eleve_info["Objectif_pct"])
    
    vitesse_ms = (vma * (pct_vma / 100) * 1000) / 3600
    vitesse_m_min = vitesse_ms * 60

    col1, col2, col3 = st.columns(3)
    col1.metric("Élève", eleve_info["Nom"])
    col2.metric("VMA / Contrat", f"{vma} km/h ({pct_vma}%)")
    col3.metric("Vitesse Cible", f"{vitesse_m_min:.1f} m / minute")

    st.markdown("---")

    # 3. Saisie minute par minute selon la durée totale de la combinaison
    st.subheader("⏱️ Saisie des passages minute par minute (Suivi d'effort)")
    
    minutes_list = list(range(1, duree_totale_min + 1))
    minute_active = st.selectbox("Minute de course en cours :", minutes_list)
    
    distance_ideale_cumulee = vitesse_m_min * minute_active

    col_saisie1, col_saisie2 = st.columns(2)
    with col_saisie1:
        distance_reelle_cumulee = st.number_input(
            f"Distance réelle cumulée (m) à la minute {minute_active} :", 
            min_value=0, max_value=6000, value=int(distance_ideale_cumulee), step=25
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
        
        if "passages_local" not in st.session_state:
            st.session_state.passages_local = pd.DataFrame(columns=["Classe", "Dossard", "Nom", "Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Temps"])
        
        st.session_state.passages_local = st.session_state.passages_local[
            ~((st.session_state.passages_local["Dossard"] == dossard_actif) & (st.session_state.passages_local["Minute_num"] == minute_active))
        ]
        st.session_state.passages_local = pd.concat([st.session_state.passages_local, nouveau_point], ignore_index=True)
        st.success(f"Minute {minute_active} enregistrée !")

    # --- 4. FEEDBACK EN TEMPS RÉEL (ÉCARTS & COURBES) ---
    st.markdown("---")
    st.subheader(f"📈 Analyse des Écarts et Courbe d'Allure - {eleve_info['Nom']}")

    try:
        df_source = conn.read(worksheet="passages_demifond", ttl=0) if (use_gsheets and conn is not None) else st.session_state.get("passages_local", pd.DataFrame())
    except Exception:
        df_source = st.session_state.get("passages_local", pd.DataFrame())

    if not df_source.empty:
        df_eleve_cours = df_source[(df_source["Classe"] == classe_active) & (df_source["Dossard"] == dossard_actif)]
        
        if not df_eleve_cours.empty and "Minute_num" in df_eleve_cours.columns:
            df_eleve_cours = df_eleve_cours.sort_values(by="Minute_num")
            
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

            st.markdown("##### 📋 Tableau de marche détaillé par minute :")
            st.dataframe(df_eleve_cours[["Minute", "Distance_Reelle", "Distance_Ideale", "Ecart_m", "Temps"]], use_container_width=True, hide_index=True)

            st.markdown("##### 📉 Graphique comparatif (Allure Réelle vs Allure Idéale) :")
            df_graph = df_eleve_cours.set_index("Minute")[["Distance_Reelle", "Distance_Ideale"]]
            st.line_chart(df_graph)
        else:
            st.info("Aucun point de passage enregistré pour cet élève sur cette séance.")
    else:
        st.info("Aucun enregistrement pour l'instant dans la base.")
else:
    st.warning("Aucun élève trouvé dans cette classe.")
