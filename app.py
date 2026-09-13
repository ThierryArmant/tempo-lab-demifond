import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="TempoLab - Blocs & Contrats (Hanula)",
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
        "Objectif_pct": [80, 75, 85, 80, 80, 75, 90, 75, 80, 80, 
                         75, 85, 90, 80, 80, 75, 85, 80, 75, 80]
    })

# Format de course par défaut (ex: Bloc 3 min - Bloc 6 min - Bloc 3 min)
if "structure_course" not in st.session_state:
    st.session_state.structure_course = "3' - 6' - 3'"

# --- 2. GÉNÉRATION DES PASSAGES AUX BORNES ---
if "log_bornes_vma" not in st.session_state:
    logs = []
    np.random.seed(42)
    
    for _, eleve in st.session_state.eleves_vma.iterrows():
        dossard = eleve["Dossard"]
        vma = eleve["VMA"]
        pct = eleve["Objectif_pct"]
        
        vitesse_effective = (vma * (pct / 100) * 1000) / 3600 * np.random.uniform(0.97, 1.03)
        
        temps_cumule = 0
        for borne in range(25, 1201, 25):
            temps_intervalle = (25 / vitesse_effective) * np.random.uniform(0.98, 1.02)
            temps_cumule += temps_intervalle
            
            logs.append({
                "Dossard": dossard,
                "Borne_m": borne,
                "Temps_s": round(temps_cumule, 1)
            })
            
    st.session_state.log_bornes_vma = pd.DataFrame(logs)

df_eleves = st.session_state.eleves_vma
df_passages = st.session_state.log_bornes_vma

# --- MENU LATÉRAL DE NAVIGATION ---
st.sidebar.title("🏁 TempoLab (Blocs)")
mode_navigation = st.sidebar.radio("📍 Navigation :", [
    "🛠️ 1. Paramétrage Prof", 
    "🏃 2. Fiche Élève & Contrat", 
    "👁️ 3. Poste Observateur (Terrain)"
])

classes_dispo = sorted(df_eleves["Classe"].unique().tolist())
classe_choisie = st.sidebar.selectbox("📂 Classe active :", classes_dispo)
df_classe = df_eleves[df_eleves["Classe"] == classe_choisie]


# ==========================================
# MODE 1 : PARAMÉTRAGE PROF
# ==========================================
if mode_navigation == "🛠️ 1. Paramétrage Prof":
    st.title("🛠️ Espace Professeur - Choix du Format de Course")
    st.write("Définissez la structure de la séance par blocs (ex: format 3'-6'-3' ou continu) et consultez les contrats attendus.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        formats_possibles = ["Continu (6 min)", "Continu (12 min)", "3' - 6' - 3'", "2' - 4' - 2'", "Personnalisé (Libre)"]
        choix_format = st.selectbox("⏱️ Structure des blocs de course :", formats_possibles, index=2)
        if choix_format != st.session_state.structure_course:
            st.session_state.structure_course = choix_format
            st.success(f"Format mis à jour : {choix_format}")

    with col_p2:
        st.metric("Mode Pédagogique", f"Sélection : {st.session_state.structure_course}")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader(f"📋 Contrats VMA - Classe {classe_choisie}")
    
    df_suivi_prof = df_classe.copy()
    # Calcul de la vitesse cible
    df_suivi_prof["Vitesse_Cible_ms"] = (df_suivi_prof["VMA"] * (df_suivi_prof["Objectif_pct"] / 100) * 1000) / 3600
    
    # Estimation de la distance selon le format choisi
    if "3' - 6' - 3'" in st.session_state.structure_course:
        duree_totale_min = 12
    elif "12 min" in st.session_state.structure_course:
        duree_totale_min = 12
    elif "2' - 4' - 2'" in st.session_state.structure_course:
        duree_totale_min = 8
    else:
        duree_totale_min = 6

    df_suivi_prof["Distance_Theorique_m"] = (df_suivi_prof["Vitesse_Cible_ms"] * (duree_totale_min * 60)).round(1)

    st.dataframe(
        df_suivi_prof[["Dossard", "Nom", "VMA", "Objectif_pct", "Distance_Theorique_m"]].rename(
            columns={
                "Objectif_pct": "Contrat (% VMA)",
                "Distance_Theorique_m": f"Distance Cible ({duree_totale_min} min cumulées)"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


# ==========================================
# MODE 2 : FICHE ÉLÈVE & CONTRAT
# ==========================================
elif mode_navigation == "🏃 2. Fiche Élève & Contrat":
    st.title(f"🏃 Fiche Élève - Format : {st.session_state.structure_course}")
    st.write("Sélectionne ton nom, ajuste ton contrat (% VMA) et visualise tes objectifs par blocs.")

    df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
    nom_selectionne = st.selectbox("🎯 Sélectionne ton nom :", df_classe["Label"])

    if nom_selectionne:
        dossard_actif = int(nom_selectionne.split(" - ")[0])
        idx_eleve = df_eleves[df_eleves["Dossard"] == dossard_actif].index[0]
        infos_eleve = df_eleves.loc[idx_eleve]

        st.markdown("<hr>", unsafe_allow_html=True)
        
        vma_eleve = float(infos_eleve["VMA"])
        pct_actuel = int(infos_eleve["Objectif_pct"])

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.metric("VMA de référence", f"{vma_eleve} km/h")
        with col_v2:
            nouveau_pct = st.slider("Choix de ton Contrat (% VMA) :", min_value=50, max_value=110, value=pct_actuel, step=5)
            if nouveau_pct != pct_actuel:
                st.session_state.eleves_vma.loc[idx_eleve, "Objectif_pct"] = nouveau_pct
                st.rerun()

        vitesse_ms = (vma_eleve * (nouveau_pct / 100) * 1000) / 3600
        
        # Gestion des repères par blocs (ex: 3' - 6' - 3')
        st.info(f"📌 **Vitesse cible :** {vitesse_ms:.2f} m/s. Respecte les consignes de changement d'allure selon les blocs de ta fiche !")

        df_ses_bornes = df_passages[df_passages["Dossard"] == dossard_actif].copy()

        if not df_ses_bornes.empty:
            df_ses_bornes["Distance_Cible_m"] = (vitesse_ms * df_ses_bornes["Temps_s"]).round(1)
            
            distance_max_reelle = df_ses_bornes["Borne_m"].max()
            dernier_temps_s = df_ses_bornes.iloc[-1]["Temps_s"]

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("📏 Dist. Réelle Validée", f"{distance_max_reelle} m")
            col_m2.metric("⏱️ Temps Écoulé", f"{dernier_temps_s} s")
            col_m3.metric("🎯 Vitesse Contrat", f"{(vitesse_ms*3.6):.1f} km/h")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("📋 Passages intermédiaires aux bornes (Tous les 25m)")

            st.dataframe(
                df_ses_bornes[["Borne_m", "Temps_s", "Distance_Cible_m"]].rename(
                    columns={
                        "Borne_m": "Borne (m)",
                        "Temps_s": "Temps Réel (s)",
                        "Distance_Cible_m": "Distance Cible (m)"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

            st.subheader("📉 Graphique Comparatif de Régularité")
            df_graph = df_ses_bornes[["Borne_m", "Distance_Cible_m"]].set_index("Borne_m")
            df_graph["Distance_Réelle"] = df_graph.index
            st.line_chart(df_graph, height=200)


# ==========================================
# MODE 3 : POSTE OBSERVATEUR (TERRAIN)
# ==========================================
else:
    st.title(f"👁️ Poste Observateur - Format : {st.session_state.structure_course}")
    st.write("Suivez votre coureur à chaque borne, analysez l'écart par rapport au contrat et qualifiez son profil d'allure.")

    df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
    coureur_choisi = st.selectbox("🎯 Coureur observé :", df_classe["Label"])

    if coureur_choisi:
        dossard_obs = int(coureur_choisi.split(" - ")[0])
        infos_obs = df_classe[df_classe["Dossard"] == dossard_obs].iloc[0]
        
        vma_obs = float(infos_obs["VMA"])
        pct_obs = int(infos_obs["Objectif_pct"])
        vitesse_c_obs = (vma_obs * (pct_obs / 100) * 1000) / 3600

        st.markdown("<hr>", unsafe_allow_html=True)
        col_info1, col_info2, col_info3 = st.columns(3)
        col_info1.metric("Coureur", infos_obs["Nom"])
        col_info2.metric("VMA", f"{vma_obs} km/h")
        col_info3.metric("Contrat Choisi", f"{pct_obs}% VMA")

        st.subheader("📊 Suivi Temps Réel & Qualification du Profil d'Allure")

        df_bornes_obs = df_passages[df_passages["Dossard"] == dossard_obs].copy()

        if not df_bornes_obs.empty:
            df_bornes_obs["Temps_Theorique_s"] = (df_bornes_obs["Borne_m"] / vitesse_c_obs).round(1)
            df_bornes_obs["Ecart_s"] = (df_bornes_obs["Temps_s"] - df_bornes_obs["Temps_Theorique_s"]).round(1)

            def eval_profil_allure(row):
                ecart = row["Ecart_s"]
                if abs(ecart) <= 2.0:
                    return "🟢 VERT", "Stable (Régulier)"
                elif ecart < -2.0:
                    return "🔴 ROUGE", "Descendant (Parti trop vite)"
                elif ecart > 2.0:
                    return "🟠 ORANGE", "Montant (Progressif / Fin de bloc)"
                else:
                    return "🔵 BLEU", "Dent de scie (Irrégulier / Yo-yo)"

            resultats_evaluation = df_bornes_obs.apply(eval_profil_allure, axis=1)
            df_bornes_obs["Rétroaction_Code"] = [r[0] for r in resultats_evaluation]
            df_bornes_obs["Profil_Allure"] = [r[1] for r in resultats_evaluation]

            st.dataframe(
                df_bornes_obs[["Borne_m", "Temps_s", "Temps_Theorique_s", "Ecart_s", "Rétroaction_Code", "Profil_Allure"]].rename(
                    columns={
                        "Borne_m": "Borne",
                        "Temps_s": "Réel (s)",
                        "Temps_Theorique_s": "Cible (s)",
                        "Ecart_s": "Écart (s)",
                        "Rétroaction_Code": "Code",
                        "Profil_Allure": "Profil d'allure"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

            st.info("💡 **Rétroaction verbale :** Annoncez la couleur et le profil pour aider le coureur à ajuster son allure selon les consignes du bloc en cours.")
