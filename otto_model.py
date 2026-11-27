import numpy as np
import pandas as pd

# Constante universal de los gases en distintas unidades:
# R_KJ_MOL_K = 0.008314 kJ/(mol·K)
# R_BAR_M3_MOL_K = 0.00008314 bar·m^3/(mol·K) 1 kJ = 0.01 bar·m^3
R_KJ_MOL_K = 0.008314
R_BAR_M3_MOL_K = 0.00008314

FLUIDOS_PREDEFINIDOS = {
    "Aire (gas ideal estándar)": {
        "cv": 0.0208,       # kJ/(mol·K)
        "k": 1.400,         # adimensional
        "Rf": R_BAR_M3_MOL_K,
    },
    "Mezcla aire-combustible": {
        "cv": 0.0238,       # kJ/(mol·K)
        "k": 1.350,         # adimensional
        "Rf": R_BAR_M3_MOL_K,
    },
    "Gas monoatómico (ej. Ar)": {
        "cv": 0.01247,      # kJ/(mol·K) (~3/2 R)
        "k": 1.667,         # adimensional (~5/3)
        "Rf": R_BAR_M3_MOL_K,
    },
    "Dióxido de carbono (CO2)": {
        "cv": 0.0289,       # kJ/(mol·K)
        "k": 1.289,         # adimensional
        "Rf": R_BAR_M3_MOL_K,
    },
}


def resolver_ciclo_otto_molar(
    P1_bar: float,
    T1_K: float,
    r: float,
    q_in_kj_mol: float,
    cv: float,
    k: float,
    Rf_bar_m3_mol_K: float = R_BAR_M3_MOL_K,
    n_mol: float = 1.0,
    T0_K: float = None,
    T_fuente_K: float = None,
):
    """
    Resuelve el ciclo Otto ideal en base molar (kJ/mol, kJ/(mol·K), m^3/mol)
    y presiones en bar.
    """
    if T0_K is None:
        T0_K = T1_K

    cp = k * cv
    R_kj = cp - cv  # kJ/(mol·K)

    # --- ESTADO 1 (Inicio de compresión) ---
    v1 = (Rf_bar_m3_mol_K * T1_K) / P1_bar  # m^3/mol
    V1 = n_mol * v1                          # m^3
    s1 = 0.0                                 # kJ/(mol·K)

    # --- PROCESO 1 -> 2 (Compresión isentrópica) ---
    v2 = v1 / r
    V2 = V1 / r
    T2 = T1_K * (r ** (k - 1.0))
    P2_bar = P1_bar * (r ** k)
    s2 = s1
    q12 = 0.0
    w12 = cv * (T1_K - T2)  # kJ/mol (negativo: trabajo suministrado al gas)

    # --- PROCESO 2 -> 3 (Adición de calor isocórica) ---
    v3 = v2
    V3 = V2
    T3 = T2 + (q_in_kj_mol / cv)
    P3_bar = P2_bar * (T3 / T2)
    s3 = s2 + cv * np.log(T3 / T2)
    q23 = q_in_kj_mol        # kJ/mol
    w23 = 0.0

    # --- PROCESO 3 -> 4 (Expansión isentrópica) ---
    v4 = v1
    V4 = V1
    T4 = T3 * ((1.0 / r) ** (k - 1.0))
    P4_bar = P3_bar * ((1.0 / r) ** k)
    s4 = s3
    q34 = 0.0
    w34 = cv * (T3 - T4)  # kJ/mol (positivo: trabajo entregado por el gas)

    # --- PROCESO 4 -> 1 (Rechazo de calor isocórica) ---
    q41 = cv * (T1_K - T4)  # kJ/mol (negativo: calor rechazado)
    q_out_mag = abs(q41)    # kJ/mol
    w41 = 0.0

    # --- MÉTRICAS DEL CICLO ---
    w_neto = w12 + w23 + w34 + w41          # kJ/mol (igual a q23 - q_out_mag)
    W_neto = n_mol * w_neto                 # kJ
    eta_th = (w_neto / q23) * 100.0         # %
    eta_teorica = (1.0 - 1.0 / (r ** (k - 1.0))) * 100.0

    # PME en bar: 1 kJ/m^3 = 1 kPa = 0.01 bar
    pme_bar = ((w_neto / (v1 - v2)) * 0.01) if (v1 - v2) != 0 else 0.0

    # --- PARÁMETROS ADICIONALES DE RÚBRICA (w_ideal, w_lost, s_gen) ---
    T_H = T_fuente_K if T_fuente_K is not None else T3
    w_ideal = q23 * (1.0 - (T0_K / T_H))             # kJ/mol
    s_gen = (-q23 / T_H) + (q_out_mag / T0_K)        # kJ/(mol·K)
    w_lost = T0_K * s_gen                            # kJ/mol

    # --- TABLAS ---
    df_estados = pd.DataFrame({
        "Estado": [
            "1 (Inicio compresión)",
            "2 (Fin compresión)",
            "3 (Fin combustión)",
            "4 (Fin expansión)",
        ],
        "Presión [bar]": [P1_bar, P2_bar, P3_bar, P4_bar],
        "Temperatura [K]": [T1_K, T2, T3, T4],
        "Volumen molar [m³/mol]": [v1, v2, v3, v4],
        "Volumen total [m³]": [V1, V2, V3, V4],
        "Entropía rel. Δs [kJ/(mol·K)]": [s1, s2, s3, s4],
    })

    df_procesos = pd.DataFrame({
        "Proceso": [
            "1 → 2 (Compresión isentrópica)",
            "2 → 3 (Adición calor isocórica)",
            "3 → 4 (Expansión isentrópica)",
            "4 → 1 (Rechazo calor isocórico)",
            "CICLO NETO",
        ],
        "Calor molar q [kJ/mol]": [q12, q23, q34, q41, q23 + q41],
        "Trabajo molar w [kJ/mol]": [w12, w23, w34, w41, w_neto],
        "Calor total Q [kJ]": [n_mol * q12, n_mol * q23, n_mol * q34, n_mol * q41, n_mol * (q23 + q41)],
        "Trabajo total W [kJ]": [n_mol * w12, n_mol * w23, n_mol * w34, n_mol * w41, W_neto],
    })

    # --- CURVAS PARA DIAGRAMAS P-v Y T-s ---
    v_12 = np.linspace(v1, v2, 100)
    P_12 = P1_bar * ((v1 / v_12) ** k)

    v_23 = np.full(50, v2)
    P_23 = np.linspace(P2_bar, P3_bar, 50)

    v_34 = np.linspace(v3, v4, 100)
    P_34 = P3_bar * ((v3 / v_34) ** k)

    v_41 = np.full(50, v4)
    P_41 = np.linspace(P4_bar, P1_bar, 50)

    T_12 = np.linspace(T1_K, T2, 50)
    s_12 = np.full(50, s1)

    T_23 = np.linspace(T2, T3, 100)
    s_23 = s2 + cv * np.log(T_23 / T2)

    T_34 = np.linspace(T3, T4, 50)
    s_34 = np.full(50, s3)

    T_41 = np.linspace(T4, T1_K, 100)
    s_41 = s1 + cv * np.log(T_41 / T1_K)

    curvas = {
        "pv": {
            "v": np.concatenate([v_12, v_23, v_34, v_41]),
            "P": np.concatenate([P_12, P_23, P_34, P_41]),
            "estados_v": [v1, v2, v3, v4],
            "estados_P": [P1_bar, P2_bar, P3_bar, P4_bar],
        },
        "ts": {
            "s": np.concatenate([s_12, s_23, s_34, s_41]),
            "T": np.concatenate([T_12, T_23, T_34, T_41]),
            "estados_s": [s1, s2, s3, s4],
            "estados_T": [T1_K, T2, T3, T4],
        },
    }

    resumen = {
        "cp": cp,
        "R_kj": R_kj,
        "P_max_bar": P3_bar,
        "T_max_K": T3,
        "w_neto": w_neto,
        "W_neto": W_neto,
        "q_in": q23,
        "q_out": q_out_mag,
        "eta_th": eta_th,
        "eta_teorica": eta_teorica,
        "pme_bar": pme_bar,
        "w_ideal": w_ideal,
        "w_lost": w_lost,
        "s_gen": s_gen,
        "W_ideal": n_mol * w_ideal,
        "W_lost": n_mol * w_lost,
        "S_G": n_mol * s_gen,
    }

    return resumen, df_estados, df_procesos, curvas