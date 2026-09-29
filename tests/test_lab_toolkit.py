import os
import pytest
import py_dss_interface
from utils.lab_dss_toolkit import (
    get_project_root,
    calculate_vuf_iec,
    get_network_snapshot,
    calculate_branch_loading,
)

def test_project_root():
    root = get_project_root()
    assert os.path.exists(root)
    assert os.path.basename(root) == "OpenDSS-pyDSS-Lab"
    assert os.path.exists(os.path.join(root, "data", "circuit_lab_bt", "Master_LabBT.dss"))

def test_vuf_balanced():
    import cmath
    v_a = complex(230.0, 0.0)
    v_b = 230.0 * cmath.rect(1.0, -2.0 * cmath.pi / 3.0)
    v_c = 230.0 * cmath.rect(1.0, 2.0 * cmath.pi / 3.0)
    
    vuf, v_pos, v_neg = calculate_vuf_iec(v_a, v_b, v_c)
    assert abs(v_pos - 230.0) < 1e-4
    assert abs(v_neg) < 1e-4
    assert abs(vuf) < 1e-4

def test_vuf_unbalanced():
    v_a = complex(230.0, 0.0)
    v_b = complex(200.0, -50.0)
    v_c = complex(180.0, 60.0)
    
    vuf, v_pos, v_neg = calculate_vuf_iec(v_a, v_b, v_c)
    assert v_pos > 0
    assert v_neg > 0
    assert vuf > 0.0

def test_network_snapshot_and_loading():
    root = get_project_root()
    master_file = os.path.join(root, "data", "circuit_lab_bt", "Master_LabBT.dss")
    assert os.path.exists(master_file)
    
    dss = py_dss_interface.DSS()
    dss.dssinterface.allow_forms = False
    dss.text(f"compile [{master_file}]")
    dss.solution.solve()
    assert dss.solution.converged == 1
    
    snapshot = get_network_snapshot(dss)
    assert "buses" in snapshot
    assert "lines" in snapshot
    assert "loads" in snapshot
    assert "summary" in snapshot
    assert len(snapshot["buses"]) > 0
    assert len(snapshot["lines"]) > 0
    
    # Test branch loading
    df_lines = calculate_branch_loading(dss)
    assert not df_lines.empty
    assert "Loading_pct" in df_lines.columns
    assert (df_lines["Loading_pct"] >= 0).all()
