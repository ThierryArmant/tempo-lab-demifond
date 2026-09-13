import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="TempoLab - Projet Hanula (12 min & Projets)",
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
        "Projet": ["Vert"] * 20, # Vert, Jaune ou Orange
        "Pauses": [[] for _ in range(20)] # Liste des index de colonnes (0 à 7) choisis pour la marche
    })

# Intitulés des 8 séquences d'1'30 de l'épreuve de 12 minutes
LABELS_SEQUENCES = ["1'30", "3 min", "4'30", "6 min", "7'30", "9 min", "10'30", "12 min"]

# --- MENU LATÉRAL DE NAVIGATION ---
st.sidebar.title("🏁 TempoLab (Hanula)")
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
    st.title("🛠️ Espace Professeur - Suivi des Projets (12 min)")
    st.write("Visualisez les choix de projets (Vert, Jaune, Orange)[cite: 1] et les allures associées pour l'ensemble de la classe.")

    df_prof = st.session_state.eleves_vma.loc[df_classe_idx].copy()
    
    # Calcul dynamique de l'allure et de la vitesse selon le projet choisi
    def get_vitesse_projet(row):
        vma = row["VMA"]
        proj = row["Projet"]
        if proj == "Vert":
            return max(4.0, vma - 3.0), "VMA - 3 km/h"
        elif proj == "Jaune":
            return max(4.0, vma - 2.0), "VMA - 2 km/h"
        else: # Orange
            return max(4.0, vma - 1.0), "VMA - 1 km/h"

    res = df_prof.apply(get_vitesse_projet, axis=1)
    df_prof["Vitesse_Calculee_kmh"] = [r[0] for r in res]
    df_prof["Regime"] = [r[1] for r in res]
    df_prof["Vitesse_ms"] = (df_prof["Vitesse_Calculee_kmh"] * 1000) / 3600
    
    # Distance totale en 12 min (720 secondes) en tenant compte des pauses (0 m pendant les pauses d'1'30)
    def calc_distance_12min(row):
        v_ms = row["Vitesse_ms"]
        nb_pauses = len(row["Pauses"])
        temps_course_s = (8 - nb_pauses) * 90 # 8 séquences d'1'30 (90s) moins les pauses
        return round(v_ms * temps_course_s, 1)

    df_prof["Distance_Cible_12min_m"] = df_prof.apply(calc_distance_12min, axis=1)

    st.dataframe(
        df_prof[["Dossard", "Nom", "VMA", "Projet", "Regime", "Vitesse_Calculee_kmh", "Distance_Cible_12min_m"]].rename(
            columns={
                "Projet": "Projet Choisi",
                "Regime": "Règle Allure",
                "Vitesse_Calculee_kmh": "Allure (km/h)",
                "Distance_Cible_12min_m": "Distance Cible 12min (m)"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# MODE 2 : FICHE ÉLÈVE & PROJET
# ==========================================
elif mode_navigation == "🏃 2. Fiche Élève & Projets":
    st.title("🏃 Fiche Élève - Ma Course de 12 Minutes")
    st.write("Choisis ton projet de course ([cite: 1] Vert, Jaune ou Orange) et positionne tes pauses si tu choisis le jaune ou l'orange.")

    df_classe = st.session_state.eleves_vma.loc[df_classe_idx].copy()
    df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
    nom_selectionne = st.selectbox("🎯 Sélectionne ton nom :", df_classe["Label"])

    if nom_selectionne:
        dossard_actif = int(nom_selectionne.split(" - ")[0])
        idx_eleve = st.session_state.eleves_vma[st.session_state.eleves_vma["Dossard"] == dossard_actif].index[0]
        infos_eleve = st.session_state.eleves_vma.loc[idx_eleve]

        st.markdown("<hr>", unsafe_allow_html=True)
        
        vma_eleve = float(infos_eleve["VMA"])
        projet_actuel = infos_eleve["Projet"]
        pauses_actuelles = infos_eleve["Pauses"]

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.metric("VMA de référence", f"{vma_eleve} km/h")
        with col_e2:
            nouveau_projet = st.selectbox("Choix du Projet[cite: 1] :", ["Vert", "Jaune", "Orange"], index=["Vert", "Jaune", "Orange"].index(projet_actuel))
            if nouveau_projet != projet_actuel:
                st.session_state.eleves_vma.loc[idx_eleve, "Projet"] = nouveau_projet
                # Réinitialiser les pauses selon le projet
                if nouveau_projet == "Vert":
                    st.session_state.eleves_vma.loc[idx_eleve, "Pauses"] = []
                elif nouveau_projet == "Jaune":
                    st.session_state.eleves_vma.loc[idx_eleve, "Pauses"] = [3] # par défaut 6e minute
                else:
                    st.session_state.eleves_vma.loc[idx_eleve, "Pauses"] = [2, 5] # par défaut 4'30 et 9 min
                st.rerun()

        # Configuration des pauses pour Jaune ou Orange
        pauses_choisies = pauses_actuelles
        if nouveau_projet == "Jaune":
            st.write("🟡 **Projet Jaune :** Choisis **1 séquence de marche** (1 min 30) parmi les 8 blocs[cite: 1].")
            choix_pause_1 = st.selectbox("Position de la pause d'1'30 :", options=range(8), format_func=lambda x: LABELS_SEQUENCES[x], index=pauses_actuelles[0] if pauses_actuelles else 3)
            pauses_choisies = [choix_pause_1]
            st.session_state.eleves_vma.loc[idx_eleve, "Pauses"] = pauses_choisies

        elif nouveau_projet == "Orange":
            st.write("🟠 **Projet Orange :** Choisis **2 séquences de marche** (3 min au total, consécutives ou non)[cite: 1].")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p1 = st.selectbox("1ère pause d'1'30 :", options=range(8), format_func=lambda x: LABELS_SEQUENCES[x], index=pauses_actuelles[0] if len(pauses_actuelles)>0 else 2)
            with col_p2:
                p2 = st.selectbox("2e pause d'1'30 :", options=range(8), format_func=lambda x: LABELS_SEQUENCES[x], index=pauses_actuelles[1] if len(pauses_actuelles)>1 else 5)
            pauses_choisies = sorted(list(set([p1, p2])))
            st.session_state.eleves_vma.loc[idx_eleve, "Pauses"] = pauses_choisies

        # Calcul de l'allure contractuelle
        if nouveau_projet == "Vert":
            allure_kmh = max(4.0, vma_eleve - 3.0)
            regime_txt = "VMA - 3 km/h (12 min continues)"[cite: 1]
        elif nouveau_projet == "Jaune":
            allure_kmh = max(4.0, vma_eleve - 2.0)
            regime_txt = "VMA - 2 km/h (1 pause d'1'30)"[cite: 1]
        else:
            allure_kmh = max(4.0, vma_eleve - 1.0)
            regime_txt = "VMA - 1 km/h (2 pauses d'1'30)"[cite: 1]

        v_ms = (allure_kmh * 1000) / 3600
        dist_12min = v_ms * ((8 - len(pauses_choisies)) * 90)

        st.info(f"📌 **Ton contrat :** Projet **{nouveau_projet}** ➔ Allure cible : **{allure_kmh} km/h** ({regime_txt}). Distance totale visée : **{dist_12min:.1f} m**.")

        # Visualisation des 8 colonnes (style grille Hanula)
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("📋 Grille de course (8 séquences d'1 min 30)")
        
        grille_df = pd.DataFrame(index=[f"Allure {allure_kmh} km/h (Cible)"])
        for i, seq in enumerate(LABELS_SEQUENCES):
            if i in pauses_choisies:
                grille_df[seq] = "⏸️ MARCHE (Pause)"
            else:
                grille_df[seq] = "🏃 COURIR"
        
        st.dataframe(grille_df, use_container_width=True)


# ==========================================
# MODE 3 : POSTE OBSERVATEUR (TERRAIN)
# ==========================================
else:
    st.title("👁️ Poste Observateur - Suivi de la Course (12 min)")
    st.write("Suivez le coureur, validez ses passages par blocs d'1'30 et décomptez ses sorties de route hors des zones de pause[cite: 1].")

    df_classe = st.session_state.eleves_vma.loc[df_classe_idx].copy()
    df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
    coureur_choisi = st.selectbox("🎯 Coureur observé :", df_classe["Label"])

    if coureur_choisi:
        dossard_obs = int(coureur_choisi.split(" - ")[0])
        infos_obs = st.session_state.eleves_vma[st.session_state.eleves_vma["Dossard"] == dossard_obs].iloc[0]
        
        vma_obs = float(infos_obs["VMA"])
        projet_obs = infos_obs["Projet"]
        pauses_obs = infos_obs["Pauses"]

        if projet_obs == "Vert":
            allure_obs = max(4.0, vma_obs - 3.0)
        elif projet_obs == "Jaune":
            allure_obs = max(4.0, vma_obs - 2.0)
        else:
            allure_obs = max(4.0, vma_obs - 1.0)

        st.markdown("<hr>", unsafe_allow_html=True)
        col_o1, col_o2, col_o3 = st.columns(3)
        col_o1.metric("Coureur", infos_obs["Nom"])
        col_o2.metric("Projet / Allure", f"{projet_obs} ({allure_obs} km/h)")
        col_o3.metric("Pauses prévues", f"{len(pauses_obs)} pause(s)")

        st.subheader("📊 Tableau de saisie de l'observateur (8 colonnes d'1'30)")
        st.write("*(Cochez les plots franchis par séquence. Les colonnes de pause sont neutralisées)*[cite: 1]")

        # Création d'un tableau interactif par blocs d'1'30 pour l'observateur
        obs_data = []
        for i, seq in enumerate(LABELS_SEQUENCES):
            statut = "Pause (Marche)" if i in pauses_obs else "Course active"
            obs_data.append({
                "Séquence": seq,
                "Statut prévu": statut,
                "Plots franchis": 5, # Valeur de test modifiable
                "Sortie de route (Cases vides)": 0 if i in pauses_obs else 1
            })
        
        df_obs_table = pd.DataFrame(obs_data)
        st.dataframe(df_obs_table, use_container_width=True, hide_index=True)

        total_sorties_route = sum([row["Sortie de route (Cases vides)"] for row in obs_data])
        st.metric("🚨 Total Sorties de Route provisoires", total_sorties_route)
        
        st.info("💡 **Rétroaction observateur :** Guide le coureur selon son projet. S'il est dans une zone de course active, vérifie qu'il tient son allure cible[cite: 1]. S'il est dans sa zone de pause, rappelle-lui qu'il a le droit de marcher[cite: 1] !")
