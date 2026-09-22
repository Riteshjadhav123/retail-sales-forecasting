import pytest
from src.simulation.scenario_lab import WhatIfScenarioLab

def test_scenario_lab_simulation():
    lab = WhatIfScenarioLab()
    res = lab.run_scenario_simulation(
        base_avg_daily_demand=20.0,
        demand_growth_pct=25.0,
        scenario_lead_time_days=10.0
    )

    assert "baseline" in res
    assert "scenario" in res
    assert "impact_delta" in res
    assert res["scenario"]["avg_daily_demand"] == 25.0
    assert res["impact_delta"]["reorder_point_delta"] > 0
