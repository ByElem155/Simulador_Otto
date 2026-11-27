import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from otto_model import (
    FLUIDOS_MOLAR,
    FLUIDOS_MASICO,
    resolver_ciclo_otto_unificado,
)

st.set_page_config(
    page_title="Simulador Ciclo Termodinámico de Otto",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ Simulador del Ciclo Termodinámico de Otto")
st.caption("Resuelve problemas en tiempo real en base molar (bar, kJ/mol) o base másica (kPa, kJ/kg).")

# Ajuste CSS
st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
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

# --- 1. MODO DE BASE Y FLUIDO DE TRABAJO ---
st.sidebar.header("1. Base y Fluido de Trabajo")
modo_base = st.sidebar.selectbox(
    "Sistema de unidades / base:",
    ["Molar (bar, kJ/mol)", "Másico (kPa, kJ/kg)"],
)

if modo_base.startswith("Molar"):
    fluido_sel = st.sidebar.selectbox("Seleccionar fluido de trabajo", list(FLUIDOS_MOLAR.keys()))
    f_ref = FLUIDOS_MOLAR[fluido_sel]
    Rf = st.sidebar.number_input(
        "Constante Rf [bar·m³/(mol·K)]",
        min_value=0.000001,
        max_value=0.01,
        value=float(f_ref["Rf_bar"]),
        step=0.000001,
        format="%.8f",
    )
    cv = st.sidebar.number_input(
        "Calor específico Cv [kJ/(mol·K)]",
        min_value=0.001,
        max_value=0.5,
        value=float(f_ref["cv"]),
        step=0.0005,
        format="%.5f",
    )
    k = st.sidebar.number_input(
        "Relación de calores específicos (k)",
        min_value=1.05,
        max_value=2.00,
        value=float(f_ref["k"]),
        step=0.01,
        format="%.3f",
    )

    st.sidebar.header("2. Entrada de Datos")
    P1 = st.sidebar.number_input("Presión inicial P₁ (bar)", min_value=0.01, max_value=100.0, value=1.0, step=0.1, format="%.3f")
    T1 = st.sidebar.number_input("Temperatura inicial T₁ (K)", min_value=150.0, max_value=1000.0, value=300.0, step=5.0, format="%.2f")
    r = st.sidebar.number_input("Relación de compresión (r = V₁/V₂)", min_value=1.5, max_value=25.0, value=8.0, step=0.5, format="%.2f")
    q_in = st.sidebar.number_input("Calor agregado q_entrada (kJ/mol)", min_value=0.01, max_value=500.0, value=25.0, step=1.0, format="%.3f")
    cantidad = st.sidebar.number_input("Cantidad de sustancia n (mol)", min_value=0.0001, max_value=10000.0, value=1.0, step=0.5, format="%.4f")
    T0 = st.sidebar.number_input("Temperatura entorno T₀ (K)", min_value=150.0, max_value=800.0, value=300.0, step=5.0, format="%.2f")

else:
    fluido_sel = st.sidebar.selectbox("Seleccionar fluido de trabajo", list(FLUIDOS_MASICO.keys()))
    f_ref = FLUIDOS_MASICO[fluido_sel]
    Rf = st.sidebar.number_input(
        "Constante del gas R [kJ/(kg·K)]",
        min_value=0.01,
        max_value=10.0,
        value=float(f_ref["Rf"]),
        step=0.001,
        format="%.3f",
    )
    cv = st.sidebar.number_input(
        "Calor específico Cv [kJ/(kg·K)]",
        min_value=0.01,
        max_value=20.0,
        value=float(f_ref["cv"]),
        step=0.001,
        format="%.3f",
    )
    k = st.sidebar.number_input(
        "Relación de calores específicos (k)",
        min_value=1.05,
        max_value=2.00,
        value=float(f_ref["k"]),
        step=0.01,
        format="%.2f",
    )

    st.sidebar.header("2. Entrada de Datos")
    P1 = st.sidebar.number_input("Presión inicial P₁ (kPa)", min_value=0.1, max_value=10000.0, value=100.0, step=5.0, format="%.2f")
    T1 = st.sidebar.number_input("Temperatura inicial T₁ (K)", min_value=150.0, max_value=1000.0, value=290.15, step=10.0, format="%.2f")
    r = st.sidebar.number_input("Relación de compresión (r = V₁/V₂)", min_value=1.5, max_value=25.0, value=8.0, step=0.5, format="%.2f")
    q_in = st.sidebar.number_input("Calor agregado q_entrada (kJ/kg)", min_value=0.1, max_value=10000.0, value=800.0, step=50.0, format="%.2f")
    cantidad = st.sidebar.number_input("Masa m (kg)", min_value=0.0001, max_value=10000.0, value=1.0, step=0.5, format="%.4f")
    T0 = st.sidebar.number_input("Temperatura entorno T₀ (K)", min_value=150.0, max_value=800.0, value=290.15, step=5.0, format="%.2f")

# --- RESOLVER EN TIEMPO REAL ---
resumen, df_estados, df_procesos, curvas = resolver_ciclo_otto_unificado(
    modo_base=modo_base,
    P1=P1,
    T1=T1,
    r=r,
    q_in=q_in,
    cv=cv,
    k=k,
    Rf=Rf,
    cantidad=cantidad,
    T0=T0,
)

u_P = resumen["u_P"]
u_e = resumen["u_e"]
u_s = resumen["u_s"]
u_cant = resumen["u_cant"]

# --- RESULTADOS PRINCIPALES ---
st.subheader("📊 Resultados del Ciclo")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Eficiencia térmica (η)", f"{resumen['eta_th']:.2f} %")
c2.metric("Trabajo neto", f"{resumen['w_neto']:.3f} {u_e}")
c3.metric("Presión máx. P₃", f"{resumen['P_max']:.2f} {u_P}")
c4.metric("Temp. máx. T₃", f"{resumen['T_max']:.2f} K")

c5, c6, c7, c8 = st.columns(4)
c5.metric("Trabajo ideal", f"{resumen['w_ideal']:.3f} {u_e}")
c6.metric("Trabajo perdido", f"{resumen['w_lost']:.3f} {u_e}")
c7.metric("Entropía generada", f"{resumen['s_gen']:.5f} {u_s}")
c8.metric("PME", f"{resumen['pme']:.2f} {u_P}")

st.info(
    f"**Totales para {cantidad:.4f} {u_cant}:** "
    f"W_neto = **{resumen['W_neto_total']:.3f} kJ** | "
    f"W_ideal = **{resumen['W_ideal_total']:.3f} kJ** | "
    f"W_lost = **{resumen['W_lost_total']:.3f} kJ** | "
    f"S_G = **{resumen['S_G_total']:.5f} kJ/K**"
)

# --- TABLAS ---
st.subheader("📋 Propiedades por Estado")
st.dataframe(df_estados, use_container_width=True, hide_index=True)

st.subheader("Calor, Trabajo, Entropía y Totales por Proceso")
st.dataframe(df_procesos, use_container_width=True, hide_index=True)

csv_estados = df_estados.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Descargar Tabla de Estados (.csv)",
    data=csv_estados,
    file_name="estados_ciclo_otto.csv",
    mime="text/csv",
)

# --- PESTAÑAS DE DIAGRAMAS Y ECUACIONES ---
tab1, tab2, tab3 = st.tabs(["📈 Diagramas P-v y T-s", "🔬 Eficiencia vs. r", "📐 Ecuaciones"])

with tab1:
    st.subheader("Diagramas Termodinámicos del Ciclo")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        fig1, ax1 = plt.subplots(figsize=(5.5, 4.2))
        pv = curvas["pv"]
        ax1.plot(pv["v_12"], pv["P_12"], "b-", linewidth=2, label="1→2 Compresión")
        ax1.plot(pv["v_23"], pv["P_23"], "r-", linewidth=2, label="2→3 Adición Q")
        ax1.plot(pv["v_34"], pv["P_34"], "g-", linewidth=2, label="3→4 Expansión")
        ax1.plot(pv["v_41"], pv["P_41"], "c-", linewidth=2, label="4→1 Rechazo Q")
        ax1.scatter(pv["estados_v"], pv["estados_P"], color="black", zorder=5, s=30)

        offsets_pv = [(4, -10), (4, 4), (4, 4), (4, 4)]
        for i, txt in enumerate(["1", "2", "3", "4"]):
            ax1.annotate(
                txt,
                (pv["estados_v"][i], pv["estados_P"][i]),
                textcoords="offset points",
                xytext=offsets_pv[i],
                fontsize=10,
                fontweight="bold",
            )

        ax1.set_title(f"Diagrama P - v ({pv['u_P']})", fontsize=11, fontweight="bold")
        ax1.set_xlabel(f"Volumen ({pv['u_v']})", fontsize=9)
        ax1.set_ylabel(f"Presión P ({pv['u_P']})", fontsize=9)
        ax1.tick_params(labelsize=8)
        ax1.margins(x=0.12, y=0.12)
        ax1.grid(True, linestyle="--", alpha=0.5)
        ax1.legend(fontsize=8, loc="upper right")
        plt.tight_layout()
        st.pyplot(fig1)

    with col_g2:
        fig2, ax2 = plt.subplots(figsize=(5.5, 4.2))
        ts = curvas["ts"]
        ax2.plot(ts["s_12"], ts["T_12"], "b-", linewidth=2, label="1→2 Compresión")
        ax2.plot(ts["s_23"], ts["T_23"], "r-", linewidth=2, label="2→3 Adición Q")
        ax2.plot(ts["s_34"], ts["T_34"], "g-", linewidth=2, label="3→4 Expansión")
        ax2.plot(ts["s_41"], ts["T_41"], "c-", linewidth=2, label="4→1 Rechazo Q")
        ax2.scatter(ts["estados_s"], ts["estados_T"], color="black", zorder=5, s=30)

        offsets_ts = [(-10, -8), (-10, 4), (4, 4), (4, -8)]
        for i, txt in enumerate(["1", "2", "3", "4"]):
            ax2.annotate(
                txt,
                (ts["estados_s"][i], ts["estados_T"][i]),
                textcoords="offset points",
                xytext=offsets_ts[i],
                fontsize=10,
                fontweight="bold",
            )

        ax2.set_title("Diagrama T - s", fontsize=11, fontweight="bold")
        ax2.set_xlabel(f"Cambio de Entropía Δs ({ts['u_s']})", fontsize=9)
        ax2.set_ylabel("Temperatura T (K)", fontsize=9)
        ax2.tick_params(labelsize=8)
        ax2.margins(x=0.12, y=0.12)
        ax2.grid(True, linestyle="--", alpha=0.5)
        ax2.legend(fontsize=8, loc="upper left")
        plt.tight_layout()
        st.pyplot(fig2)

with tab2:
    r_vals = np.linspace(2.0, 20.0, 100)
    eta_vals = (1.0 - 1.0 / (r_vals ** (k - 1.0))) * 100.0

    fig3, ax3 = plt.subplots(figsize=(7.5, 4))
    ax3.plot(r_vals, eta_vals, color="#2ca02c", linewidth=2.2, label=f"k = {k:.3f}")
    ax3.scatter([r], [resumen["eta_th"]], color="red", s=70, zorder=5, label=f"Actual: r={r:.2f}, η={resumen['eta_th']:.1f}%")
    ax3.set_title("Eficiencia Térmica Ideal vs. Relación de Compresión", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Relación de compresión (r)", fontsize=9)
    ax3.set_ylabel("Eficiencia térmica η (%)", fontsize=9)
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(fontsize=8)
    plt.tight_layout()
    st.pyplot(fig3)

with tab3:
    st.markdown("### Ecuaciones Fundamentales Implementadas")
    st.latex(r"r = \frac{V_1}{V_2} = \frac{v_1}{v_2}, \qquad v_i = \frac{R_f T_i}{P_i}")
    st.latex(r"T_2 = T_1 r^{k-1}, \qquad P_2 = P_1 r^k")
    st.latex(r"q_{\text{entrada}} = c_v (T_3 - T_2), \qquad P_3 = P_2 \left(\frac{T_3}{T_2}\right)")
    st.latex(r"T_4 = T_3 \left(\frac{1}{r}\right)^{k-1}, \qquad P_4 = P_3 \left(\frac{1}{r}\right)^k")
    st.latex(r"\eta_{\text{th}} = \frac{w_{\text{neto}}}{q_{\text{entrada}}} = 1 - \frac{1}{r^{k-1}}")
    st.latex(r"w_{\text{ideal}} = q_{\text{entrada}}\left(1 - \frac{T_0}{T_3}\right), \qquad s_{\text{gen}} = -\frac{q_{\text{entrada}}}{T_3} + \frac{q_{\text{salida}}}{T_0}, \qquad w_{\text{lost}} = T_0 s_{\text{gen}}")