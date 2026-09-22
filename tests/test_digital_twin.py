import pytest
import numpy as np
from src.simulation.digital_twin import DigitalRetailTwinSimulator

def test_digital_twin_simulation():
    simulator = DigitalRetailTwinSimulator()
    demand = np.random.exponential(20.0, 90)

    res_normal = simulator.simulate_series("Central_Furniture", demand, scenario_name="NORMAL")
    res_spike = simulator.simulate_series("Central_Furniture", demand, scenario_name="DEMAND_SPIKE")

    assert res_normal["horizon_days"] == 90
    assert res_normal["fill_rate_pct"] > 0
    assert res_spike["total_demand_units"] > res_normal["total_demand_units"]
