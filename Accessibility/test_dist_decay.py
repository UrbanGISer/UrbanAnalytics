import sys

sys.path.append("r2sfca")

import pandas as pd
import numpy as np
from core import R2SFCA, DecayFunction

# 创建简单测试数据
df = pd.DataFrame(
    {
        "Demand": [100, 200, 150],
        "Supply": [50, 75, 60],
        "TravelCost": [10, 20, 15],
        "DemandID": [1, 2, 1],
        "SupplyID": [1, 2, 2],
    }
)

print("创建模型...")
model = R2SFCA(
    df=df,
    demand_col="Demand",
    supply_col="Supply",
    travel_cost_col="TravelCost",
    demand_id_col="DemandID",
    supply_id_col="SupplyID",
    decay_function="exponential",
)

print("模型创建成功！")
print(f"travel_cost: {model.travel_cost}")

print("\n测试 dist_decay...")
try:
    decay_values = model.dist_decay(beta=1.0)
    print(f"✓ dist_decay 成功！decay_values: {decay_values}")
except Exception as e:
    print(f"✗ dist_decay 失败: {e}")
    import traceback

    traceback.print_exc()

print("\n测试 fij...")
try:
    fij_values = model.fij(beta=1.0)
    print(f"✓ fij 成功！fij_values: {fij_values}")
except Exception as e:
    print(f"✗ fij 失败: {e}")
    import traceback

    traceback.print_exc()

print("\n测试 tij...")
try:
    tij_values = model.tij(beta=1.0)
    print(f"✓ tij 成功！tij_values: {tij_values}")
except Exception as e:
    print(f"✗ tij 失败: {e}")
    import traceback

    traceback.print_exc()
