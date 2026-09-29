"""
lab_dss_toolkit.py
==================
Módulo avanzado de extracción de datos, análisis de calidad de energía (IEC 61000-4-30),
evaluación térmica de ramas y visualización para OpenDSS mediante py-dss-interface.

Desarrollado para el laboratorio educativo: OpenDSS-pyDSS-Lab
"""

import os
import cmath
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def get_project_root() -> str:
    """Retorna la ruta absoluta del directorio raíz del repositorio OpenDSS-pyDSS-Lab."""
    p = os.path.abspath(os.getcwd())
    while p and os.path.basename(p) != "OpenDSS-pyDSS-Lab":
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    return p

# Operador de rotación compleja Fortescue a = e^(j*2*pi/3)
ALPHA = cmath.rect(1.0, 2.0 * np.pi / 3.0)
ALPHA2 = ALPHA ** 2

def calculate_vuf_iec(v_a: complex, v_b: complex, v_c: complex) -> tuple[float, float, float]:
    """
    Calcula las componentes simétricas de Fortescue y el Factor de Desbalance de Tensión
    (Voltage Unbalance Factor - VUF%) según la norma IEC 61000-4-30 y EN 50160.
    
    Parámetros:
        v_a, v_b, v_c (complex): Fasores de tensión fase-neutro o fase-fase.
        
    Retorna:
        tuple[float, float, float]:
            - vuf_pct: Porcentaje de desbalance de secuencia negativa |V-| / |V+| * 100%
            - v_pos_mag: Magnitud de la componente de secuencia positiva |V+|
            - v_neg_mag: Magnitud de la componente de secuencia negativa |V-|
    """
    v_pos = (v_a + ALPHA * v_b + ALPHA2 * v_c) / 3.0
    v_neg = (v_a + ALPHA2 * v_b + ALPHA * v_c) / 3.0
    v_zero = (v_a + v_b + v_c) / 3.0
    
    v_pos_mag = abs(v_pos)
    v_neg_mag = abs(v_neg)
    
    if v_pos_mag > 1e-6:
        vuf_pct = (v_neg_mag / v_pos_mag) * 100.0
    else:
        vuf_pct = 0.0
        
    return vuf_pct, v_pos_mag, v_neg_mag


def get_network_snapshot(dss) -> dict[str, pd.DataFrame]:
    """
    Extrae un estado instantáneo consolidado de toda la red activa en OpenDSS en DataFrames de pandas.
    
    Retorna:
        dict con claves:
            - 'buses': Tensiones por fase (pu y kV), desbalance VUF% (IEC), mínima y máxima tensión.
            - 'lines': Corriente por fase, corriente máxima, capacidad nominal (NormAmps), % de carga y pérdidas.
            - 'loads': Potencia P (kW), Q (kvar), factor de potencia, tensión de operación.
            - 'summary': Resumen global (potencia total suministrada, pérdidas totales, tensión mín/máx).
    """
    # 1. Extracción de Barras (Buses)
    bus_records = []
    buses_names = dss.circuit.buses_names
    
    for bus_name in buses_names:
        dss.circuit.set_active_bus(bus_name)
        nodes = list(dss.bus.nodes)
        v_pu = list(dss.bus.pu_voltages)
        v_cplx = list(dss.bus.voltages)
        kv_base = dss.bus.kv_base
        
        # Procesar fasores complejos
        phasors = {}
        pu_vals = {}
        for idx, node in enumerate(nodes):
            if idx * 2 + 1 < len(v_cplx):
                r = v_cplx[idx * 2]
                im = v_cplx[idx * 2 + 1]
                phasors[node] = complex(r, im)
            if idx * 2 + 1 < len(v_pu):
                r_pu = v_pu[idx * 2]
                im_pu = v_pu[idx * 2 + 1]
                pu_vals[node] = abs(complex(r_pu, im_pu))
                
        # Calcular VUF% si la barra tiene las 3 fases 1, 2 y 3
        vuf = 0.0
        if 1 in phasors and 2 in phasors and 3 in phasors:
            vuf, _, _ = calculate_vuf_iec(phasors[1], phasors[2], phasors[3])
            
        all_pu = list(pu_vals.values()) if pu_vals else [0.0]
        
        bus_records.append({
            "Bus": bus_name,
            "Nodes": str(nodes),
            "kV_Base": kv_base,
            "Va_pu": pu_vals.get(1, np.nan),
            "Vb_pu": pu_vals.get(2, np.nan),
            "Vc_pu": pu_vals.get(3, np.nan),
            "V_min_pu": min(all_pu) if all_pu else np.nan,
            "V_max_pu": max(all_pu) if all_pu else np.nan,
            "VUF_percent": vuf if (1 in phasors and 2 in phasors and 3 in phasors) else np.nan,
        })
    df_buses = pd.DataFrame(bus_records)
    
    # 2. Extracción de Líneas (Lines)
    line_records = []
    lines_names = dss.lines.names
    
    for l_name in lines_names:
        dss.lines.name = l_name
        num_phases = dss.lines.phases
        dss.circuit.set_active_element(f"Line.{l_name}")
        curr_mag_ang = dss.cktelement.currents_mag_ang
        mags = [curr_mag_ang[i * 2] for i in range(num_phases)] if curr_mag_ang else [0.0]
        i_max = max(mags) if mags else 0.0
        norm_amps = dss.lines.norm_amps
        loading_pct = (i_max / norm_amps * 100.0) if norm_amps > 0 else 0.0
        
        # Pérdidas de la línea
        losses = dss.cktelement.losses
        losses_kw = (losses[0] / 1000.0) if len(losses) >= 2 else 0.0
        
        line_records.append({
            "Line": l_name,
            "Bus1": dss.lines.bus1,
            "Bus2": dss.lines.bus2,
            "Phases": num_phases,
            "Length_m": dss.lines.length,
            "I_max_A": round(i_max, 2),
            "NormAmps_A": norm_amps,
            "Loading_pct": round(loading_pct, 2),
            "Losses_kW": round(losses_kw, 3),
            "Status": "SOBRECARGA" if loading_pct > 100 else ("ALERTA" if loading_pct > 80 else "NORMAL"),
        })
    df_lines = pd.DataFrame(line_records)
    
    # 3. Extracción de Cargas (Loads)
    load_records = []
    load_names = dss.loads.names
    for ld in load_names:
        dss.loads.name = ld
        dss.circuit.set_active_element(f"Load.{ld}")
        bus_name = dss.cktelement.bus_names[0] if dss.cktelement.bus_names else ""
        num_phases = dss.cktelement.num_phases
        load_records.append({
            "Load": ld,
            "Bus": bus_name,
            "Phases": num_phases,
            "kW": dss.loads.kw,
            "kvar": dss.loads.kvar,
            "PF": dss.loads.pf,
            "kV": dss.loads.kv,
        })
    df_loads = pd.DataFrame(load_records)
    
    # 4. Resumen Global
    losses_total_kw = dss.circuit.losses[0] / 1000.0
    losses_total_kvar = dss.circuit.losses[1] / 1000.0
    total_power_kw = abs(dss.circuit.total_power[0])
    total_power_kvar = abs(dss.circuit.total_power[1])
    
    df_summary = pd.DataFrame([{
        "Total_Generation_kW": total_power_kw,
        "Total_Generation_kvar": total_power_kvar,
        "Total_Losses_kW": losses_total_kw,
        "Total_Losses_kvar": losses_total_kvar,
        "Losses_Percentage": (losses_total_kw / total_power_kw * 100.0) if total_power_kw > 0 else 0.0,
        "Circuit_Converged": bool(dss.solution.converged),
    }])
    
    return {
        "buses": df_buses,
        "lines": df_lines,
        "loads": df_loads,
        "summary": df_summary,
    }


def calculate_branch_loading(dss) -> pd.DataFrame:
    """Calcula el estado térmico y porcentaje de carga de todos los conductores del circuito."""
    snapshot = get_network_snapshot(dss)
    return snapshot["lines"]


def plot_voltage_profile(df_buses: pd.DataFrame, v_min: float = 0.95, v_max: float = 1.05, title: str = "Perfil de Tensión por Fase (pu)") -> plt.Figure:
    """
    Grafica el perfil de tensión nodal para las 3 fases, indicando las bandas de tolerancia admisibles
    según normas regulatorias (IEC / ANSI C84.1).
    """
    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
    
    x = range(len(df_buses))
    bus_names = df_buses["Bus"].tolist()
    
    if "Va_pu" in df_buses.columns:
        ax.plot(x, df_buses["Va_pu"], marker="o", color="#d62728", label="Fase A (V1)", linewidth=2, markersize=6)
    if "Vb_pu" in df_buses.columns:
        ax.plot(x, df_buses["Vb_pu"], marker="s", color="#1f77b4", label="Fase B (V2)", linewidth=2, markersize=6)
    if "Vc_pu" in df_buses.columns:
        ax.plot(x, df_buses["Vc_pu"], marker="^", color="#2ca02c", label="Fase C (V3)", linewidth=2, markersize=6)
        
    ax.axhline(1.00, color="gray", linestyle="--", alpha=0.7, label="Nominal (1.00 pu)")
    ax.axhline(v_max, color="crimson", linestyle=":", linewidth=2, label=f"Límite Máximo (+{(v_max-1)*100:.1f}%)")
    ax.axhline(v_min, color="crimson", linestyle=":", linewidth=2, label=f"Límite Mínimo (-{(1-v_min)*100:.1f}%)")
    
    ax.set_xticks(x)
    ax.set_xticklabels(bus_names, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("Tensión [pu]", fontsize=11, fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="best", frameon=True)
    plt.tight_layout()
    return fig


def plot_unbalance_summary(df_buses: pd.DataFrame, limit_vuf: float = 2.0) -> plt.Figure:
    """Grafica el Factor de Desbalance de Tensión (VUF%) para todas las barras trifásicas."""
    df_3ph = df_buses.dropna(subset=["VUF_percent"]).copy()
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=100)
    
    colors = ["#2ca02c" if val <= limit_vuf else "#d62728" for val in df_3ph["VUF_percent"]]
    bars = ax.bar(df_3ph["Bus"], df_3ph["VUF_percent"], color=colors, edgecolor="black", alpha=0.85, width=0.55)
    
    ax.axhline(limit_vuf, color="red", linestyle="--", linewidth=2, label=f"Límite IEC 61000-4-30 ({limit_vuf}%)")
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.2f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8, fontweight="bold")
                    
    ax.set_ylabel("VUF [%] (Sec. Negativa / Sec. Positiva)", fontsize=10, fontweight="bold")
    ax.set_title("Factor de Desbalance de Tensión (VUF%) por Barra Trifásica", fontsize=11, fontweight="bold")
    ax.set_xticklabels(df_3ph["Bus"], rotation=40, ha="right", fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right")
    plt.tight_layout()
    return fig


def plot_qsts_voltage_heatmap(time_array: np.ndarray, bus_names: list[str], voltage_matrix: np.ndarray, title: str = "Evolución Temporal de Tensión Nodal (pu)") -> plt.Figure:
    """
    Genera un mapa de calor (Heatmap) representando la evolución temporal de la tensión
    en todas las barras a lo largo del horizonte cuasi-estático (QSTS).
    """
    fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
    
    im = ax.imshow(voltage_matrix.T, aspect="auto", cmap="viridis",
                   extent=[time_array[0], time_array[-1], len(bus_names)-0.5, -0.5])
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Tensión [pu]", fontsize=10, fontweight="bold")
    
    ax.set_yticks(range(len(bus_names)))
    ax.set_yticklabels(bus_names, fontsize=8)
    ax.set_xlabel("Paso Temporal / Hora", fontsize=10, fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold")
    plt.tight_layout()
    return fig
