import sys

sys.path.append("r2sfca")

import pandas as pd
import numpy as np
from core import R2SFCA, DecayFunction

# 创建测试数据
df = pd.DataFrame(
    {
        "Demand": [100, 200, 150, 300],
        "Supply": [50, 75, 60, 80],
        "TravelCost": [10, 20, 15, 25],
        "DemandID": [1, 2, 1, 2],
        "SupplyID": [1, 2, 2, 1],
    }
)

print("测试 SIGMOID 初始化...")
print("Travel costs:", df["TravelCost"].values)
print("Median travel cost:", np.median(df["TravelCost"].values))

# 初始化 SIGMOID 模型
print("\n初始化 SIGMOID 模型:")
model = R2SFCA(
    df=df,
    demand_col="Demand",
    supply_col="Supply",
    travel_cost_col="TravelCost",
    demand_id_col="DemandID",
    supply_id_col="SupplyID",
    decay_function="sigmoid",
)

print(f"模型中的 median_travel_cost: {model.median_travel_cost}")
print(f"decay_function: {model.decay_function}")
print(
    f"decay_function == DecayFunction.SIGMOID: {model.decay_function == DecayFunction.SIGMOID}"
)

# 测试 dist_decay
print("\n测试 dist_decay:")
decay_values = model.dist_decay(beta=1.0, steepness=5.0)
print(f"衰减值: {decay_values}")
