# 修复后的代码
import numpy as np
import matplotlib.pyplot as plt
from core import R2SFCA, DecayFunction

# 假设 test_df 和 beta 已经定义
# test_df = ...
# beta = 1.0

# Distance decay function comparison
plt.figure(figsize=(12, 8))

for decay_func in DecayFunction:
    # 修复：直接使用 decay_func，不需要检查
    test_model = R2SFCA(df=test_df, decay_function=decay_func.value)

    # 使用模型中的travel_cost数据
    travel_costs = test_model.travel_cost
    sorted_indices = np.argsort(travel_costs)
    sorted_costs = travel_costs[sorted_indices]

    if decay_func == DecayFunction.SIGMOID:
        values = test_model.dist_decay(beta, steepness=5.0)
    elif decay_func == DecayFunction.GAUSSIAN:
        values = test_model.dist_decay(beta, d0=20.0)
    elif decay_func == DecayFunction.LOG_SQUARED:
        values = test_model.dist_decay(beta, epsilon=1)
    else:
        values = test_model.dist_decay(beta)

    sorted_values = values[sorted_indices]

    # 为了可视化，只显示前1000个点
    if len(sorted_costs) > 1000:
        step = len(sorted_costs) // 1000
        sorted_costs = sorted_costs[::step]
        sorted_values = sorted_values[::step]

    plt.plot(
        sorted_costs, sorted_values, label=decay_func.value, linewidth=2, alpha=0.7
    )

plt.xlabel("Travel Cost")
plt.ylabel("Decay Value")
plt.xlim(0, 100)
plt.ylim(0, 1)
plt.title("Distance Decay Functions Comparison (β=1.0)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


