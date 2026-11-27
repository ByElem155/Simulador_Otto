import numpy as np
import pandas as pd

# Constantes de referencia:
# Base molar: R_KJ_MOL_K = 0.008314 kJ/(mol·K), Rf_BAR = 0.00008314 bar·m³/(mol·K)
# Base másica (aire): R_KJ_KG_K = 0.287 kJ/(kg·K), cv_aire = 0.718 kJ/(kg·K)
FLUIDOS_MOLAR = {
    "Aire (gas ideal estándar)": {"cv": 0.0208, "k": 1.400, "Rf_bar": 0.00008314},
    "Mezcla aire-combustible": {"cv": 0.0238, "k": 1.350, "Rf_bar": 0.00008314},
    "Gas monoatómico (ej. Ar)": {"cv": 0.01247, "k": 1.667, "Rf_bar": 0.00008314},
    "Dióxido de carbono (CO2)": {"cv": 0.0289, "k": 1.289, "Rf_bar": 0.00008314},
}

FLUIDOS_MASICO = {
    "Aire": {"Rf": 0.287, "cv": 0.718, "k": 1.400},
    "Mezcla aire-combustible": {"Rf": 0.290, "cv": 0.821, "k": 1.350},
    "Personalizado": {"Rf": 0.287, "cv": 0.718, "k": 1.400},
}


def resolver_ciclo_otto_unificado(
    modo_base: str,          # "Molar (bar, kJ/mol)" o "Másico (kPa, kJ/kg)"
    P1: float,               # bar en molar | kPa en másico
    T1: float,               # K
    r: float,                # relación de compresión V1/V2
    q_in: float,             # kJ/mol en molar | kJ/kg en másico
    cv: float,               # kJ/(mol·K) o kJ/(kg·K)
    k: float,                # adimensional
    Rf: float,               # bar·m³/(mol·K) o kJ/(kg·K)
    cantidad: float = 1.0,   # mol en molar | kg en másico
    T0: float = None,        # temperatura entorno (K)
):
    """
    Resuelve el ciclo Otto ideal en base molar (con presión en bar)
    o en base másica (con presión en kPa).
    """
    if T0 is None:
        T0 = T1

    es_molar = modo_base.startswith("Molar")
    u_P = "bar" if es_molar else "kPa"
    u_v = "m³/mol" if es_molar else "m³/kg"
    u_V = "m³"
    u_s = "kJ/(mol·K)" if es_molar else "kJ/(kg·K)"
    u_e = "kJ/mol" if es_molar else "kJ/kg"
    u_cant = "mol" if es_molar else "kg"

    # En base másica, 1 kJ/m³ = 1 kPa; en base molar con P = bar, 1 kJ/m³ = 0.01 bar
    factor_pme = 0.01 if es_molar else 1.0

    # --- ESTADO 1 (Inicio de compresión) ---
    v1 = (Rf * T1) / P1
    V1 = cantidad * v1
    s1 = 0.0

    # --- PROCESO 1 -> 2 (Compresión isentrópica) ---
    v2 = v1 / r
    V2 = V1 / r
    T2 = T1 * (r ** (k - 1.0))
    P2 = P1 * (r ** k)
    s2 = s1
    q12 = 0.0
    w12 = cv * (T2 - T1)
    ds12 = s2 - s1

    # --- PROCESO 2 -> 3 (Adición de calor isocórica) ---
    v3 = v2
    V3 = V2
    T3 = T2 + (q_in / cv)
    P3 = P2 * (T3 / T2)
    s3 = s2 + cv * np.log(T3 / T2)
    q23 = q_in
    w23 = 0.0
    ds23 = s3 - s2

    # --- PROCESO 3 -> 4 (Expansión isentrópica) ---
    v4 = v1
    V4 = V1
    T4 = T3 * ((1.0 / r) ** (k - 1.0))
    P4 = P3 * ((1.0 / r) ** k)
    s4 = s3
    q34 = 0.0
    w34 = cv * (T4 - T3)
    ds34 = s4 - s3

    # --- PROCESO 4 -> 1 (Rechazo de calor isocórica) ---
    q41 = cv * (T4 - T1)      # negativo al rechazar calor (T4 > T1)
    q_out_mag = abs(q41)      # magnitud positiva del calor rechazado
    w41 = 0.0
    ds41 = s1 - s4

    # --- MÉTRICAS DEL CICLO ---
    w_neto = w12 + w23 + w34 + w41
    q_neto = q12 + q23 + q34 - q41
    ds_neto = ds12 + ds23 + ds34 + ds41

    W_neto_total = cantidad * w_neto
    Q_neto_total = cantidad * q_neto

    eta_th = (w_neto / q23) * 100.0 if q23 != 0 else 0.0
    eta_otto_ideal = (1.0 - 1.0 / (r ** (k - 1.0))) * 100.0
    pme = ((w_neto / (v1 - v2)) * factor_pme) if (v1 - v2) != 0 else 0.0

# Eficiencias de referencia por etapa (para tabla de procesos)
    n12 = (abs(w12) / (cv * (T2 - T1))) * 100.0 if (T2 - T1) != 0 else 0.0
    n23 = (q23 / q_in) * 100.0 if q_in != 0 else 0.0
    n34 = (w34 / (cv * T3)) * 100.0 if (cv * T3) != 0 else 0.0
    n41 = (abs(q41) / q23) * 100.0 if q23 != 0 else 0.0

    # --- TRABAJO IDEAL, TRABAJO PERDIDO Y GENERACIÓN DE ENTROPÍA ---
    # Tomando T3 como temperatura máxima de fuente térmica y T0 como sumidero/entorno
    w_ideal = q23 * (1.0 - (T0 / T3)) if T3 != 0 else 0.0
    s_gen = (-q23 / T3) + (q_out_mag / T0) if (T3 != 0 and T0 != 0) else 0.0
    w_lost = T0 * s_gen

    df_estados = pd.DataFrame({
        "Estado": [
            "1 (Inicio compresión)",
            "2 (Fin compresión)",
            "3 (Fin combustión)",
            "4 (Fin expansión)",
        ],
        f"Presión ({u_P})": [P1, P2, P3, P4],
        "Temperatura (K)": [T1, T2, T3, T4],
        f"Volumen esp. ({u_v})": [v1, v2, v3, v4],
        f"Volumen total ({u_V})": [V1, V2, V3, V4],
        f"Entropía rel. Δs ({u_s})": [s1, s2, s3, s4],
    })

    df_procesos = pd.DataFrame({
        "Proceso": [
            "1 → 2 (Compresión isentrópica)",
            "2 → 3 (Adición calor isocórica)",
            "3 → 4 (Expansión isentrópica)",
            "4 → 1 (Rechazo calor isocórico)",
            "Total del Ciclo",
        ],
        f"Calor ({u_e})": [q12, q23, q34, q41, q_neto],
        f"Trabajo ({u_e})": [w12, w23, w34, w41, w_neto],
        f"Cambio Entropía Δs ({u_s})": [ds12, ds23, ds34, ds41, ds_neto],
        "Eficiencia (%)": [n12, n23, n34, n41, eta_th],
        f"Total {u_cant} (kJ)": [
            cantidad * q12,
            cantidad * q23,
            cantidad * q34,
            cantidad * q41,
            Q_neto_total,
        ],
    })

    # --- CURVAS PARA GRÁFICAS ---
    v_12 = np.linspace(v1, v2, 100)
    P_12 = P1 * ((v1 / v_12) ** k)

    v_34 = np.linspace(v3, v4, 100)
    P_34 = P3 * ((v3 / v_34) ** k)

    T_23 = np.linspace(T2, T3, 100)
    s_23 = s2 + cv * np.log(T_23 / T2)

    T_41 = np.linspace(T4, T1, 100)
    s_41 = s4 + cv * np.log(T_41 / T4)

    curvas = {
        "pv": {
            "v_12": v_12, "P_12": P_12,
            "v_23": [v2, v3], "P_23": [P2, P3],
            "v_34": v_34, "P_34": P_34,
            "v_41": [v4, v1], "P_41": [P4, P1],
            "estados_v": [v1, v2, v3, v4],
            "estados_P": [P1, P2, P3, P4],
            "u_P": u_P,
            "u_v": u_v,
        },
        "ts": {
            "s_12": [s1, s2], "T_12": [T1, T2],
            "s_23": s_23, "T_23": T_23,
            "s_34": [s3, s4], "T_34": [T3, T4],
            "s_41": s_41, "T_41": T_41,
            "estados_s": [s1, s2, s3, s4],
            "estados_T": [T1, T2, T3, T4],
            "u_s": u_s,
        },
    }

    resumen = {
        "u_P": u_P,
        "u_e": u_e,
        "u_s": u_s,
        "u_cant": u_cant,
        "P_max": P3,
        "T_max": T3,
        "w_neto": w_neto,
        "W_neto_total": W_neto_total,
        "q_in": q23,
        "q_out": q_out_mag,
        "eta_th": eta_th,
        "eta_otto_ideal": eta_otto_ideal,
        "pme": pme,
        "w_ideal": w_ideal,
        "w_lost": w_lost,
        "s_gen": s_gen,
        "W_ideal_total": cantidad * w_ideal,
        "W_lost_total": cantidad * w_lost,
        "S_G_total": cantidad * s_gen,
    }

    return resumen, df_estados, df_procesos, curvas
