import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="TempoLab - Course & Projets",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN COMPACT & HAUT CONTRASTE ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #111418 !important; border-right: 2px solid #262a33; padding-top: 10px; }
    h1 { font-size: 1.5rem !important; margin-bottom: 0px !important; padding-bottom: 0px !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.0rem !important; }
    p, span, label, div[data-testid="stSidebar"] * { color: #ffffff !important; font-size: 0.9rem; }
    [data-testid="stDataFrame"] *, [data-testid="stTable"] *, th, td { color: #000000 !important; font-size: 0.85rem !important; }
    div[data-testid="stMetric"] { background-color: #16181d; border: 1px solid #333842; border-radius: 8px; padding: 8px !important; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    .stAlert { padding: 8px 12px !important; font-size: 0.85rem !important; margin-bottom: 8px !important; }
    hr { margin: 10px 0px !important; border-color: #333842; }
    </style>
""", unsafe_allow_html=True)

# --- 1. INITIALISATION DE LA BASE DE DONNÉES GLOBALE ---
if "eleves_vma" not in st.session_state:
    st.session_state.eleves_vma = pd.DataFrame({
        "Classe": ["5ème"] * 20,
        "Dossard": [5501, 5502, 5503, 5504, 5505, 5506, 5507, 5508, 5509, 5510, 
                    5511, 5512, 5513, 5514, 5515, 5516, 5517, 5518, 5519, 5520],
        "Nom": [
            "Blanc Nathan", "Bonnet Chloé", "Brunet Lucas", "Chevalier Manon", 
            "Clement Hugo", "Colin Emma", "David Théo", "Dupond Sarah", 
            "Dupont Thomas", "Fabre Inès", "Faure Louis", "Fontaine Zoé", 
            "Fournier Lucas", "Garcia Léa", "Garnier Tom", "Gautier Camille", 
            "Girard Nathan", "Guerin Juliette", "Henry Hugo", "Laurent Maëlys"
        ],
        "VMA": [13.5, 11.5, 14.8, 12.0, 13.0, 12.8, 15.0, 10.5, 14.2, 13.2, 
                12.2, 14.0, 15.5, 11.8, 13.8, 12.5, 14.5, 13.6, 12.9, 14.1],
        "Type_Course": ["Course de 12 min (8 x 1'30)"] * 20,
        "Projet": ["Vert"] * 20,
        "Pauses": [[] for _ in range(20)]
    })
else:
    if "Type_Course" not in st.session_state.eleves_vma.columns:
        st.session_state.eleves_vma["Type_Course"] = "Course de 12 min (8 x 1'30)"
    if "Projet" not in st.session_state.eleves_vma.columns:
        st.session_state.eleves_vma["Projet"] = "Vert"
    if "Pauses" not in st.session_state.eleves_vma.columns:
        st.session_state.eleves_vma["Pauses"] = [[] for _ in range(len(st.session_state.eleves_vma))]

LABELS_12MIN = ["1'30", "3 min", "4'30", "6 min", "7'30", "9 min", "10'30", "12 min"]
LABELS_3030 = ["1 min", "2 min", "3 min", "4 min", "5 min (Rattrapage)", "6 min (Rattrapage)", "7 min (Rattrapage)"]

# --- MENU LATÉRAL DE NAVIGATION ---
st.sidebar.title("🏁 TempoLab")
mode_navigation = st.sidebar.radio("📍 Navigation :", [
    "🛠️ 1. Paramétrage Prof", 
    "🏃 2. Fiche Élève & Projets", 
    "👁️ 3. Poste Observateur (Terrain)"
])

classes_dispo = sorted(st.session_state.eleves_vma["Classe"].unique().tolist())
classe_choisie = st.sidebar.selectbox("📂 Classe active :", classes_dispo)
df_classe_idx = st.session_state.eleves_vma[st.session_state.eleves_vma["Classe"] == classe_choisie].index


# ==========================================
# MODE 1 : PARAMÉTRAGE PROF
# ==========================================
if mode_navigation == "🛠️ 1. Paramétrage Prof":
    st.title("🛠️ Espace Professeur - Suivi des Choix & Projets")
    st.write("Visualisez pour chaque élève le type de course choisi, son projet et les allures associées.")

    df_prof = st.session_state.eleves_vma.loc[df_classe_idx].copy()
    
    def get_vitesse_projet(row):
        vma = row["VMA"]
        proj = row["Projet"]
        tc = row["Type_Course"]
        if "30/30" in tc:
            return vma + 3.0, "VMA + 3 km/h (30/30)"
        else:
            if proj == "Vert":
                return max(4.0, vma - 3.0), "VMA - 3 km/h (Vert)"
            elif proj == "Jaune":
                return max(4.0, vma - 2.0), "VMA - 2 km/h (Jaune)"
            else:
                return max(4.0, vma - 1.0), "VMA - 1 km/h (Orange)"

    res = df_prof.apply(get_vitesse_projet, axis=1)
    df_prof["Vitesse_Calculee_kmh"] = [r[0] for r in res]
    df_prof["Regime"] = [r[1] for r in res]

    st.dataframe(
        df_prof[["Dossard", "Nom", "VMA", "Type_Course", "Projet", "Regime", "Vitesse_Calculee_kmh"]].rename(
            columns={
                "Type_Course": "Course Choisie",
                "Projet": "Projet",
                "Regime": "Règle Allure",
                "Vitesse_Calculee_kmh": "Allure (km/h)"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# MODE 2 : FICHE ÉLÈVE & PROJET
# ==========================================
elif mode_navigation == "🏃 2. Fiche Élève & Projets":
    st.title("🏃 Fiche Élève - Choix de l'Épreuve & du Contrat")
    st.write("Sélectionne ton nom, puis choisis ton épreuve et ton projet tactique.")

    df_classe = st.session_state.eleves_vma.loc[df_classe_idx].copy()
    df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
    nom_selectionne = st.selectbox("🎯 Sélectionne ton nom :", df_classe["Label"])

    if nom_selectionne:
        dossard_actif = int(nom_selectionne.split(" - ")[0])
        idx_eleve = st.session_state.eleves_vma[st.session_state.eleves_vma["Dossard"] == dossard_actif].index[0]
        infos_eleve = st.session_state.eleves_vma.loc[idx_eleve]

        st.markdown("<hr>", unsafe_allow_html=True)
        
        vma_eleve = float(infos_eleve["VMA"])
        course_actuelle = infos_eleve["Type_Course"]
        projet_actuel = infos_eleve["Projet"]
        pauses_actuelles = infos_eleve["Pauses"]

        # 1. SÉLECTION DU TYPE DE COURSE EN HAUT DE FICHE (Enregistré immédiatement)
        st.subheader("🎯 Choix de la course")
        types_courses_possibles = [
            "Course de 12 min (8 x 1'30)", 
            "Épreuve de Rattrapage 30/30 (VMA + 3)"
        ]
        
        idx_course_defaut = types_courses_possibles.index(course_actuelle) if course_actuelle in types_courses_possibles else 0
        nouvelle_course = st.selectbox("Sélectionne l'épreuve à réaliser :", types_courses_possibles, index=idx_course_defaut, key=f"select_course_{dossard_actif}")
        
        if nouvelle_course != course_actuelle:
            st.session_state.eleves_vma.at[idx_eleve, "Type_Course"] = nouvelle_course
            st.rerun()

        st.markdown("---")

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.metric("VMA de référence", f"{vma_eleve} km/h")

        # 2. CONFIGURATION SELON LA COURSE ENREGISTRÉE
        if "30/30" in nouvelle_course:
            with col_e2:
                st.metric("Format", "Intermittent 30/30")
            st.info("⚡ **Épreuve de Rattrapage (30/30) :** Alternance de 30s de course intense (VMA + 3 km/h) et 30s de marche[cite: 1].")
            allure_kmh = round(vma_eleve + 3.0, 1)
            
            if vma_eleve >= 18: plots_30s = 6.5
            elif vma_eleve >= 16: plots_30s = 6.0
            elif vma_eleve >= 14: plots_30s = 5.5
            elif vma_eleve >= 12: plots_30s = 5.0
            else: plots_30s = 4.5
            
            st.write(f"🎯 **Objectif :** Franchir au moins **{plots_30s} plots** par séquence de 30 secondes[cite: 1].")

        else:
            with col_e2:
                nouveau_projet = st.selectbox("Choix du Projet (12 min)[cite: 1] :", ["Vert", "Jaune", "Orange"], index=["Vert", "Jaune", "Orange"].index(projet_actuel) if projet_actuel in ["Vert", "Jaune", "Orange"] else 0, key=f"select_projet_{dossard_actif}")
                if nouveau_projet != projet_actuel:
                    st.session_state.eleves_vma.at[idx_eleve, "Projet"] = nouveau_projet
                    if nouveau_projet == "Vert":
                        st.session_state.eleves_vma.at[idx_eleve, "Pauses"] = []
                    elif nouveau_projet == "Jaune":
                        st.session_state.eleves_vma.at[idx_eleve, "Pauses"] = [3]
                    else:
                        st.session_state.eleves_vma.at[idx_eleve, "Pauses"] = [2, 5]
                    st.rerun()

            pauses_choisies = []
            if nouveau_projet == "Vert":
                st.success("🟢 **Projet Vert :** Course continue sur les 12 minutes (allure fixe à VMA - 3 km/h)[cite: 1].")
                pauses_choisies = []
            elif nouveau_projet == "Jaune":
                st.write("🟡 **Projet Jaune :** Choisis **1 séquence de marche** (1 min 30) parmi les 8 blocs[cite: 1].")
                choix_pause_1 = st.selectbox("Position de la pause d'1'30 :", options=range(8), format_func=lambda x: LABELS_12MIN[x], index=pauses_actuelles[0] if len(pauses_actuelles) > 0 else 3)
                pauses_choisies = [choix_pause_1]
                st.session_state.eleves_vma.at[idx_eleve, "Pauses"] = pauses_choisies
            else:
                st.write("🟠 **Projet Orange :** Choisis **2 séquences de marche** (3 min au total, consécutives ou non)[cite: 1].")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    p1 = st.selectbox("1ère pause d'1'30 :", options=range(8), format_func=lambda x: LABELS_12MIN[x], index=pauses_actuelles[0] if len(pauses_actuelles) > 0 else 2)
                with col_p2:
                    p2 = st.selectbox("2e pause d'1'30 :", options=range(8), format_func=lambda x: LABELS_12MIN[x], index=pauses_actuelles[1] if len(pauses_actuelles) > 1 else 5)
                pauses_choisies = sorted(list(set([p1, p2])))
                st.session_state.eleves_vma.at[idx_eleve, "Pauses"] = pauses_choisies

            if nouveau_projet == "Vert":
                allure_kmh = max(4.0, vma_eleve - 3.0)
            elif nouveau_projet == "Jaune":
                allure_kmh = max(4.0, vma_eleve - 2.0)
            else:
                allure_kmh = max(4.0, vma_eleve - 1.0)

            st.info(f"📌 **Contrat :** Projet **{nouveau_projet}** ➔ Allure cible : **{allure_kmh} km/h**[cite: 1].")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("📋 Grille de course (8 séquences d'1 min 30)")
            grille_df = pd.DataFrame(index=[f"Allure {allure_kmh} km/h"])
            for i, seq in enumerate(LABELS_12MIN):
                if i in pauses_choisies:
                    grille_df[seq] = "⏸️ MARCHE"
                else:
                    grille_df[seq] = "🏃 COURIR"
            st.dataframe(grille_df, use_container_width=True)


# ==========================================
# MODE 3 : POSTE OBSERVATEUR (TERRAIN)
# ==========================================
else:
    st.title("👁️ Poste Observateur - Suivi de l'Épreuve")
    st.write("Suivez le coureur sur sa course sélectionnée et décomptez ses écarts[cite: 1].")

    df_classe = st.session_state.eleves_vma.loc[df_classe_idx].copy()
    df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
    coureur_choisi = st.selectbox("🎯 Coureur observé :", df_classe["Label"])

    if coureur_choisi:
        dossard_obs = int(coureur_choisi.split(" - ")[0])
        infos_obs = st.session_state.eleves_vma[st.session_state.eleves_vma["Dossard"] == dossard_obs].iloc[0]
        
        course_obs = infos_obs["Type_Course"]
        projet_obs = infos_obs["Projet"]
        pauses_obs = infos_obs["Pauses"] if projet_obs != "Vert" else []

        st.markdown("<hr>", unsafe_allow_html=True)
        col_o1, col_o2, col_o3 = st.columns(3)
        col_o1.metric("Coureur", infos_obs["Nom"])
        col_o2.metric("Épreuve", course_obs)
        col_o3.metric("Projet", projet_obs if "30/30" not in course_obs else "Intensif (VMA+3)")

        st.subheader("📊 Tableau de saisie de l'observateur")

        if "30/30" in course_obs:
            obs_data = []
            for seq in LABELS_3030:
                obs_data.append({
                    "Séquence": seq,
                    "Format": "30s Course / 30s Marche[cite: 1]",
                    "Plots franchis": 5,
                    "Validé (Réussi)": "Oui"
                })
            df_obs_table = pd.DataFrame(obs_data)
            st.dataframe(df_obs_table, use_container_width=True, hide_index=True)
        else:
            obs_data = []
            for i, seq in enumerate(LABELS_12MIN):
                statut = "Pause (Marche)" if i in pauses_obs else "Course active"
                obs_data.append({
                    "Séquence": seq,
                    "Statut prévu": statut,
                    "Plots franchis": 5,
                    "Sortie de route (Cases vides)": 0 if i in pauses_obs else 1
                })
            df_obs_table = pd.DataFrame(obs_data)
            st.dataframe(df_obs_table, use_container_width=True, hide_index=True)
            
            total_sorties = sum([row["Sortie de route (Cases vides)"] for row in obs_data])
            st.metric("🚨 Total Sorties de Route", total_sorties)

        st.info("💡 **Rétroaction observateur :** Guide ton camarade en temps réel selon le type de course et son projet choisi[cite: 1].")
