import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from otto_model import FLUIDOS_PREDEFINIDOS, resolver_ciclo_otto_molar

st.set_page_config(
    page_title="Simulador Ciclo Otto (Base Molar)",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Simulador Termodinámico del Ciclo Otto")
st.caption("Ingresa los datos de operación y propiedades del fluido para resolver el ciclo en tiempo real (bar, K, kJ/mol y kJ/(mol·K)).")

st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        white-space: normal !important;
        overflow-wrap: break-word !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        white-space: normal !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- BARRA LATERAL: ENTRADA DE DATOS EN TIEMPO REAL ---
st.sidebar.header("1. Fluido de Trabajo (Editable)")
fluido_sel = st.sidebar.selectbox("Fluido de referencia:", list(FLUIDOS_PREDEFINIDOS.keys()))
f_base = FLUIDOS_PREDEFINIDOS[fluido_sel]

cv = st.sidebar.number_input(
    "Calor específico molar Cv [kJ/(mol·K)]",
    min_value=0.001,
    max_value=0.200,
    value=float(f_base["cv"]),
    step=0.0005,
    format="%.5f",
)
k = st.sidebar.number_input(
    "Relación de calores específicos k = Cp/Cv",
    min_value=1.05,
    max_value=2.00,
    value=float(f_base["k"]),
    step=0.01,
    format="%.3f",
)
Rf = st.sidebar.number_input(
    "Constante del gas Rf [bar·m³/(mol·K)]",
    min_value=0.000001,
    max_value=0.001,
    value=float(f_base["Rf"]),
    step=0.000001,
    format="%.8f",
)

st.sidebar.header("2. Datos de Operación")
P1_bar = st.sidebar.number_input(
    "Presión inicial P₁ [bar]",
    min_value=0.01,
    max_value=50.0,
    value=1.0,
    step=0.1,
    format="%.2f",
)
T1_K = st.sidebar.number_input(
    "Temperatura inicial T₁ [K]",
    min_value=150.0,
    max_value=800.0,
    value=300.0,
    step=5.0,
    format="%.1f",
)
r = st.sidebar.number_input(
    "Relación de compresión (r = V₁/V₂)",
    min_value=1.5,
    max_value=25.0,
    value=8.0,
    step=0.2,
    format="%.2f",
)
q_in_kj_mol = st.sidebar.number_input(
    "Calor añadido q_entrada [kJ/mol]",
    min_value=0.01,
    max_value=500.0,
    value=25.0,
    step=1.0,
    format="%.2f",
)
n_mol = st.sidebar.number_input(
    "Cantidad de sustancia n [mol]",
    min_value=0.0001,
    max_value=10000.0,
    value=1.0,
    step=0.5,
    format="%.4f",
)
T0_K = st.sidebar.number_input(
    "Temperatura del entorno T₀ [K]",
    min_value=150.0,
    max_value=600.0,
    value=300.0,
    step=5.0,
    format="%.1f",
)

# Resolver con los valores ingresados
resumen, df_estados, df_procesos, curvas = resolver_ciclo_otto_molar(
    P1_bar=P1_bar,
    T1_K=T1_K,
    r=r,
    q_in_kj_mol=q_in_kj_mol,
    cv=cv,
    k=k,
    Rf_bar_m3_mol_K=Rf,
    n_mol=n_mol,
    T0_K=T0_K,
)

# --- INDICADORES PRINCIPALES ---
st.subheader("📊 Resultados del Ciclo")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Eficiencia térmica (η)", f"{resumen['eta_th']:.2f} %")
c2.metric("Trabajo neto (w_neto)", f"{resumen['w_neto']:.3f} kJ/mol")
c3.metric("Presión máxima (P₃)", f"{resumen['P_max_bar']:.2f} bar")
c4.metric("Temperatura máxima (T₃)", f"{resumen['T_max_K']:.1f} K")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Trabajo ideal (w_ideal)", f"{resumen['w_ideal']:.3f} kJ/mol")
c6.metric("Trabajo perdido (w_lost)", f"{resumen['w_lost']:.3f} kJ/mol")
c7.metric("Entropía generada (s_gen)", f"{resumen['s_gen']:.5f} kJ/(mol·K)")
c8.metric("PME", f"{resumen['pme_bar']:.2f} bar")

st.info(
    f"*Totales para n = {n_mol:.4f} mol:* "
    f"W_neto = *{resumen['W_neto']:.3f} kJ* | "
    f"W_ideal = *{resumen['W_ideal']:.3f} kJ* | "
    f"W_lost = *{resumen['W_lost']:.3f} kJ* | "
    f"S_G = *{resumen['S_G']:.5f} kJ/K*"
)

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Diagramas P-v y T-s",
    "📋 Tablas de Estados y Procesos",
    "🔬 Eficiencia vs. Relación r",
    "📐 Ecuaciones en Base Molar",
])

with tab1:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(curvas["pv"]["v"], curvas["pv"]["P"], color="#1f77b4", linewidth=2.2)
    ax1.scatter(curvas["pv"]["estados_v"], curvas["pv"]["estados_P"], color="#d62728", zorder=5)
    for i, etq in enumerate(["1", "2", "3", "4"]):
        ax1.annotate(f"  {etq}", (curvas["pv"]["estados_v"][i], curvas["pv"]["estados_P"][i]), fontsize=11, fontweight="bold")
    ax1.set_title("Diagrama P - v (Presión en bar)", fontweight="bold")
    ax1.set_xlabel("Volumen molar v [m³/mol]")
    ax1.set_ylabel("Presión P [bar]")
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2.plot(curvas["ts"]["s"], curvas["ts"]["T"], color="#ff7f0e", linewidth=2.2)
    ax2.scatter(curvas["ts"]["estados_s"], curvas["ts"]["estados_T"], color="#d62728", zorder=5)
    for i, etq in enumerate(["1", "2", "3", "4"]):
        ax2.annotate(f"  {etq}", (curvas["ts"]["estados_s"][i], curvas["ts"]["estados_T"][i]), fontsize=11, fontweight="bold")
    ax2.set_title("Diagrama T - Δs (Entropía en kJ/(mol·K))", fontweight="bold")
    ax2.set_xlabel("Cambio de entropía molar Δs [kJ/(mol·K)]")
    ax2.set_ylabel("Temperatura T [K]")
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    st.pyplot(fig)

with tab2:
    st.markdown("### Propiedades por Estado Termodinámico")
    st.dataframe(
        df_estados.style.format({
            "Presión [bar]": "{:.3f}",
            "Temperatura [K]": "{:.2f}",
            "Volumen molar [m³/mol]": "{:.6f}",
            "Volumen total [m³]": "{:.6f}",
            "Entropía rel. Δs [kJ/(mol·K)]": "{:.5f}",
        }),
        use_container_width=True,
    )

    st.markdown("### Calor, Trabajo y Totales por Etapa")
    st.dataframe(
        df_procesos.style.format({
            "Calor molar q [kJ/mol]": "{:.3f}",
            "Trabajo molar w [kJ/mol]": "{:.3f}",
            "Calor total Q [kJ]": "{:.3f}",
            "Trabajo total W [kJ]": "{:.3f}",
        }),
        use_container_width=True,
    )

    csv_estados = df_estados.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar Tabla de Estados (.csv)",
        data=csv_estados,
        file_name="ciclo_otto_molar_estados.csv",
        mime="text/csv",
    )

with tab3:
    r_vals = np.linspace(2.0, 20.0, 100)
    eta_vals = (1.0 - 1.0 / (r_vals ** (k - 1.0))) * 100.0

    fig2, ax = plt.subplots(figsize=(8, 4))
    ax.plot(r_vals, eta_vals, color="#2ca02c", linewidth=2.2, label=f"k = {k:.3f}")
    ax.scatter([r], [resumen["eta_th"]], color="red", s=80, zorder=5, label=f"Actual: r={r:.2f}, η={resumen['eta_th']:.1f}%")
    ax.set_title("Eficiencia Térmica Ideal vs. Relación de Compresión", fontweight="bold")
    ax.set_xlabel("Relación de compresión (r)")
    ax.set_ylabel("Eficiencia térmica η [%]")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()
    st.pyplot(fig2)

with tab4:
    st.markdown("### Ecuaciones en Base Molar y Presión en bar")
    st.latex(r"v_i = \frac{R_f T_i}{P_i}, \qquad r = \frac{v_1}{v_2}")
    st.latex(r"T_2 = T_1 r^{k-1}, \qquad P_2 = P_1 r^k")
    st.latex(r"q_{\text{entrada}} = c_v (T_3 - T_2), \qquad P_3 = P_2 \left(\frac{T_3}{T_2}\right)")
    st.latex(r"T_4 = T_3 \left(\frac{1}{r}\right)^{k-1}, \qquad P_4 = P_3 \left(\frac{1}{r}\right)^k")
    st.latex(r"\eta_{\text{th}} = \frac{w_{\text{neto}}}{q_{\text{entrada}}} = 1 - \frac{1}{r^{k-1}}")
    st.latex(r"w_{\text{ideal}} = q_{\text{entrada}}\left(1 - \frac{T_0}{T_3}\right), \qquad s_{\text{gen}} = -\frac{q_{\text{entrada}}}{T_3} + \frac{q_{\text{salida}}}{T_0}, \qquad w_{\text{lost}} = T_0 s_{\text{gen}}")