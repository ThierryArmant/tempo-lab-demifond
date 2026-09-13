import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="TempoLab - Curseur VMA & Distance Cible",
    page_icon="⏱️",
    layout="wide"
)

# --- DESIGN HAUT CONTRASTE (Plein soleil) ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #111418 !important; border-right: 2px solid #262a33; }
    h1, h2, h3, h4, h5, h6, p, span, label, div[data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stDataFrame"] *, [data-testid="stTable"] *, th, td { color: #000000 !important; }
    div[data-testid="stMetric"] { background-color: #16181d; border: 2px solid #333842; border-radius: 10px; padding: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- BASE ÉLÈVES (AVEC VMA ET % DE CONTRAT INITIAL) ---
if "eleves_vma" not in st.session_state:
    st.session_state.eleves_vma = pd.DataFrame({
        "Classe": ["5e5", "5e5", "5e7"],
        "Dossard": [501, 502, 701],
        "Nom": ["Nathan Blanc", "Chloé Bonnet", "Lucas Brunet"],
        "VMA": [13.5, 11.5, 14.2],
        "Objectif_pct": [80, 75, 85]
    })

# --- SIMULATION DES PASSAGES AUX BORNES RFID (Tous les 25m) AVEC TEMPS EN SECONDES ---
if "log_bornes_vma" not in st.session_state:
    st.session_state.log_bornes_vma = pd.DataFrame([
        # Nathan Blanc (Dossard 501)
        {"Dossard": 501, "Borne_m": 25, "Temps_s": 10},
        {"Dossard": 501, "Borne_m": 50, "Temps_s": 21},
        {"Dossard": 501, "Borne_m": 75, "Temps_s": 32},
        {"Dossard": 501, "Borne_m": 100, "Temps_s": 43},
        {"Dossard": 501, "Borne_m": 125, "Temps_s": 54},
        {"Dossard": 501, "Borne_m": 150, "Temps_s": 65},
        {"Dossard": 501, "Borne_m": 175, "Temps_s": 76},
        {"Dossard": 501, "Borne_m": 200, "Temps_s": 88},
        # Chloé Bonnet (Dossard 502)
        {"Dossard": 502, "Borne_m": 25, "Temps_s": 12},
        {"Dossard": 502, "Borne_m": 50, "Temps_s": 25},
        {"Dossard": 502, "Borne_m": 75, "Temps_s": 38},
        {"Dossard": 502, "Borne_m": 100, "Temps_s": 52},
    ])

df_eleves = st.session_state.eleves_vma
df_passages = st.session_state.log_bornes_vma

# --- MENU LATÉRAL ---
st.sidebar.title("🏁 TempoLab - VMA & Bornes")
classes_dispo = sorted(df_eleves["Classe"].unique().tolist())
classe_choisie = st.sidebar.selectbox("📂 Choisir la classe :", classes_dispo)

df_classe = df_eleves[df_eleves["Classe"] == classe_choisie]

st.title(f"🏃 Bilan Individuel & Curseur VMA - Classe {classe_choisie}")
st.write("Sélectionne ton nom, ajuste si besoin ton intensité (% VMA) et analyse ta distance cible par rapport au réel des bornes RFID.")

st.markdown("---")

# --- SÉLECTION DE L'ÉLÈVE ---
df_classe["Label"] = df_classe["Dossard"].astype(str) + " - " + df_classe["Nom"]
nom_selectionne = st.selectbox("🎯 Sélectionne ton nom :", df_classe["Label"])

if nom_selectionne:
    dossard_actif = int(nom_selectionne.split(" - ")[0])
    infos_eleve = df_classe[df_classe["Dossard"] == dossard_actif].iloc[0]

    st.markdown("---")
    
    # --- CURSEUR D'INTENSITÉ / VMA ---
    st.subheader(f"⚡ Réglage du Contrat - {infos_eleve['Nom']}")
    
    vma_eleve = float(infos_eleve["VMA"])
    pct_initial = int(infos_eleve["Objectif_pct"])

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.metric("VMA de référence", f"{vma_eleve} km/h")
    with col_v2:
        # Le curseur pour ajuster l'intensité en direct
        pct_vma_curseur = st.slider("Curseur d'intensité (% VMA) :", min_value=50, max_value=110, value=pct_initial, step=5)

    # Calcul de la vitesse en mètres par seconde (m/s) et mètres par minute (m/min)
    vitesse_ms = (vma_eleve * (pct_vma_curseur / 100) * 1000) / 3600
    
    st.info(f"📌 **Vitesse cible :** {vitesse_ms:.2f} m/s (soit environ {(vitesse_ms*60):.1f} m par minute).")

    st.markdown("---")

    # Récupérer les passages RFID de l'élève
    df_ses_bornes = df_passages[df_passages["Dossard"] == dossard_actif].copy()

    if not df_ses_bornes.empty:
        # Calcul dynamique de la distance idéale / cible pour chaque temps de passage enregistré par les bornes
        # Distance Cible = Vitesse (m/s) * Temps écoulé (secondes)
        df_ses_bornes["Distance_Cible_m"] = (vitesse_ms * df_ses_bornes["Temps_s"]).round(1)
        
        # Écart = Distance Réelle (la borne fixe, ex: 25m, 50m...) - Distance Cible théorique calculée avec la VMA/Curseur
        # Note : Sur une borne fixe (ex: la borne des 100m), la distance réelle est fixe (100m). 
        # L'écart se lit donc plutôt sur le temps ou sur la distance parcourue au bout d'un temps donné.
        # Ajustons la logique : comparons ce qu'il a parcouru au temps t par rapport à la cible.
        
        distance_max_reelle = df_ses_bornes["Borne_m"].max()
        dernier_temps_s = df_ses_bornes.iloc[-1]["Temps_s"]
        distance_cible_finale = vitesse_ms * dernier_temps_s

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("📏 Distance Réelle Validée", f"{distance_max_reelle} m")
        col_m2.metric("🎯 Distance Cible Théorique", f"{distance_cible_finale:.1f} m")
        col_m3.metric("⏱️ Temps Total", f"{dernier_temps_s} secondes")

        st.markdown("---")

        st.subheader("📋 Tableau des passages aux bornes (25m, 50m, 75m...) et Distances Cibles")
        st.write("*(Ce tableau recalcule dynamiquement ta distance cible théorique selon la position du curseur % VMA ci-dessus)*")

        # Affichage du tableau propre
        st.dataframe(
            df_ses_bornes[["Borne_m", "Temps_s", "Distance_Cible_m"]].rename(
                columns={
                    "Borne_m": "Borne RFID (m)",
                    "Temps_s": "Temps (secondes)",
                    "Distance_Cible_m": "Distance Cible (m)"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        # Graphique comparatif
        st.subheader("📉 Comparatif Borne Réelle vs Distance Cible")
        df_graph = df_ses_bornes.set_index("Borne_m")[["Borne_m", "Distance_Cible_m"]]
        st.line_chart(df_graph)

    else:
        st.info("Aucun passage enregistré pour cet élève.")
