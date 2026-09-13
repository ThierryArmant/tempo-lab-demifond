import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="TempoLab - Tests Profils d'Allure",
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
    h3 { font-size: 1rem !important; }
    p, span, label, div[data-testid="stSidebar"] * { color: #ffffff !important; font-size: 0.9rem; }
    [data-testid="stDataFrame"] *, [data-testid="stTable"] *, th, td { color: #000000 !important; font-size: 0.85rem !important; }
    div[data-testid="stMetric"] { background-color: #16181d; border: 1px solid #333842; border-radius: 8px; padding: 8px !important; }
    div[data-testid="stMetricValue"] { font-size: 1.2rem !important; }
    .stAlert { padding: 8px 12px !important; font-size: 0.85rem !important; margin-bottom: 8px !important; }
    hr { margin: 10px 0px !important; border-color: #333842; }
    </style>
""", unsafe_allow_html=True)

# --- BASE ÉLÈVES (FOCUS SUR LES 4 PROFILS DE TEST) ---
if "eleves_vma" not in st.session_state:
    st.session_state.eleves_vma = pd.DataFrame({
        "Classe": ["5ème"] * 4,
        "Dossard": [5501, 5502, 5503, 5504],
        "Nom": [
            "Blanc Nathan (Stable)", 
            "Bonnet Chloé (Descendant - Trop vite)", 
            "Brunet Lucas (Montant - Progressif)", 
            "Chevalier Manon (Dent de scie - Yo-yo)"
        ],
        "VMA": [13.5, 11.5, 14.8, 12.0],
        "Objectif_pct": [80, 75, 85, 80]
    })

# --- GÉNÉRATION DES COURSES DE TEST SPÉCIFIQUES (600m / par pas de 25m) ---
if "log_bornes_vma" not in st.session_state:
    logs = []
    
    # 1. Nathan (STABLE) : Vitesse constante
    v_nathan = (13.5 * 0.80 * 1000) / 3600
    t = 0
    for b in range(25, 601, 25):
        t += (25 / v_nathan) * 1.01
        logs.append({"Dossard": 5501, "Borne_m": b, "Temps_s": round(t, 1)})

    # 2. Chloé (DESCENDANT) : Part très vite (avance énorme au début), puis craque complètement
    v_chloe = (11.5 * 0.75 * 1000) / 3600
    t = 0
    for i, b in enumerate(range(25, 601, 25)):
         facteur = 0.75 if i < 8 else (1.1 + (i * 0.05)) # rapide au début, lent à la fin
         t += (25 / v_chloe) * facteur
         logs.append({"Dossard": 5502, "Borne_m": b, "Temps_s": round(t, 1)})

    # 3. Lucas (MONTANT) : Part lentement (retard), puis accélère fort sur la fin
    v_lucas = (14.8 * 0.85 * 1000) / 3600
    t = 0
    for i, b in enumerate(range(25, 601, 25)):
        facteur = 1.2 if i < 10 else 0.85 # lent au début, très rapide à la fin
        t += (25 / v_lucas) * facteur
        logs.append({"Dossard": 5503, "Borne_m": b, "Temps_s": round(t, 1)})

    # 4. Manon (DENT DE SCIE) : Alterne accélérations et ralentissements brusques
    v_manon = (12.0 * 0.80 * 1000) / 3600
    t = 0
    alternance = [0.8, 1.3, 0.75, 1.25, 0.9, 1.2, 0.8, 1.3, 0.85, 1.15, 0.9, 1.2, 0.8, 1.2, 0.9, 1.1, 0.85, 1.15, 0.9, 1.1, 0.95, 1.05, 0.9, 1.1]
    for i, b in enumerate(range(25, 601, 25)):
        facteur = alternance[i % len(alternance)]
        t += (25 / v_manon) * facteur
        logs.append({"Dossard": 5504, "Borne_m": b, "Temps_s": round(t, 1)})

    st.session_state.log_bornes_vma = pd.DataFrame(logs)

df_eleves = st.session_state.eleves_vma
df_passages = st.session_state.log_bornes_vma

# --- MENU LATÉRAL DE NAVIGATION ---
st.sidebar.title("🏁 TempoLab Tests")
mode_navigation = st.sidebar.radio("📍 Mode :", [
    "🏃 Bilan & Contrat", 
    "👁️ Poste Observateur"
])

classes_dispo = sorted(df_eleves["Classe"].unique().tolist())
classe_choisie = st.sidebar.selectbox("📂 Classe :", classes_dispo)

df_classe = df_eleves[df_eleves["Classe"] == classe_choisie]

# ==========================================
# MODE 1 : BILAN INDIVIDUEL ET CONTRAT
# ==========================================
if mode_navigation == "🏃 Bilan & Contrat":
    st.title(f"🏃 Fiche Élève (Tests Profils) - {classe_choisie}")
    
    df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
    nom_selectionne = st.selectbox("🎯 Sélectionne ton profil de test :", df_classe["Label"])

    if nom_selectionne:
        dossard_actif = int(nom_selectionne.split(" - ")[0])
        idx_eleve = df_eleves[df_eleves["Dossard"] == dossard_actif].index[0]
        infos_eleve = df_eleves.loc[idx_eleve]

        st.markdown("<hr>", unsafe_allow_html=True)
        
        vma_eleve = float(infos_eleve["VMA"])
        pct_actuel = int(infos_eleve["Objectif_pct"])

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.metric("VMA Réf.", f"{vma_eleve} km/h")
        with col_v2:
            nouveau_pct = st.slider("Contrat (% VMA) :", min_value=50, max_value=110, value=pct_actuel, step=5)
            if nouveau_pct != pct_actuel:
                st.session_state.eleves_vma.loc[idx_eleve, "Objectif_pct"] = nouveau_pct
                st.rerun()

        vitesse_ms = (vma_eleve * (nouveau_pct / 100) * 1000) / 3600
        st.info(f"📌 Vitesse cible : **{vitesse_ms:.2f} m/s** ({(vitesse_ms*60):.1f} m/min)")

        df_ses_bornes = df_passages[df_passages["Dossard"] == dossard_actif].copy()

        if not df_ses_bornes.empty:
            df_ses_bornes["Distance_Cible_m"] = (vitesse_ms * df_ses_bornes["Temps_s"]).round(1)
            
            distance_max_reelle = df_ses_bornes["Borne_m"].max()
            dernier_temps_s = df_ses_bornes.iloc[-1]["Temps_s"]
            distance_cible_finale = vitesse_ms * dernier_temps_s

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("📏 Dist. Réelle", f"{distance_max_reelle} m")
            col_m2.metric("🎯 Dist. Cible", f"{distance_cible_finale:.1f} m")
            col_m3.metric("⏱️ Temps Total", f"{dernier_temps_s} s")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("📋 Passages & Distances Cibles")

            st.dataframe(
                df_ses_bornes[["Borne_m", "Temps_s", "Distance_Cible_m"]].rename(
                    columns={
                        "Borne_m": "Borne (m)",
                        "Temps_s": "Temps (s)",
                        "Distance_Cible_m": "Cible (m)"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

            st.subheader("📉 Graphique Comparatif")
            df_graph = df_ses_bornes[["Borne_m", "Distance_Cible_m"]].set_index("Borne_m")
            df_graph["Distance_Réelle"] = df_graph.index
            st.line_chart(df_graph, height=200)

# ==========================================
# MODE 2 : LOGIQUE DE L'OBSERVATEUR (TERRAIN)
# ==========================================
else:
    st.title(f"👁️ Poste Observateur (Tests Profils) - {classe_choisie}")

    df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
    coureur_choisi = st.selectbox("🎯 Coureur de test observé :", df_classe["Label"])

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
        col_info3.metric("Contrat", f"{pct_obs}%")

        st.subheader("📊 Suivi & Profil d'Allure de Course")

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
                    return "🟠 ORANGE", "Montant (Progressif / Fin de course)"
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
                        "Ecart_s": "Écart",
                        "Rétroaction_Code": "Code",
                        "Profil_Allure": "Profil d'allure"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

            st.info("💡 **Testez les 4 profils dans le menu déroulant :** Nathan (Stable), Chloé (Descendant), Lucas (Montant) et Manon (Dent de scie) réagissent instantanément !")
