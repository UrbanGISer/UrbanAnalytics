# R2SFCA v1.1.2 更新总结

**发布日期**: 2025-10-14  
**版本号**: 1.1.2  
**更新类型**: Bug Fix (重要修复)

---

## 📋 修改的文件清单

### 1. 核心代码修改
- ✅ `r2sfca/core.py` - 修复 `solve_beta` 方法的相关性优化逻辑

### 2. 版本号更新
- ✅ `setup.py` - 版本号更新为 1.1.2
- ✅ `pyproject.toml` - 版本号更新为 1.1.2
- ✅ `r2sfca/__init__.py` - 版本号更新为 1.1.2
- ✅ `CHANGELOG.md` - 添加 v1.1.2 更新日志

### 3. 辅助文件 (新增)
- ✅ `build_and_upload.bat` - Windows 自动化构建脚本
- ✅ `verify_version.py` - 版本号一致性检查工具
- ✅ `UPLOAD_STEPS.md` - 简明上传指南
- ✅ `VERSION_1.1.2_SUMMARY.md` - 本文档

### 4. 清理的文件
- ✅ `CORRELATION_FIX.md` - 已删除（内容合并到 CHANGELOG）
- ✅ `dist/*` - 清理旧的构建文件
- ✅ `build/` - 清理构建缓存
- ✅ `*.egg-info/` - 清理包信息缓存

---

## 🐛 Bug 修复详情

### 问题描述
在 `solve_beta()` 方法中，所有优化指标都被**最小化**，包括相关性 (correlation)。

这是**错误**的，因为：
- ❌ Correlation 值越大越好，应该**最大化**
- ✅ Cross-entropy, RMSE, MSE, MAE 应该最小化

### 修复内容

#### 修改位置 1: `_solve_beta_minimize` 方法 (第 548-552 行)
```python
# 修复前：
return eval_metrics[metric]

# 修复后：
if metric == "correlation" or metric.endswith("_correlation"):
    return -eval_metrics[metric]  # 最大化相关性 = 最小化负相关性
else:
    return eval_metrics[metric]   # 最小化误差指标
```

#### 修改位置 2: `_solve_beta_adam` 方法 - 损失计算 (第 632-636 行)
```python
if metric == "correlation" or metric.endswith("_correlation"):
    loss = -eval_metrics[metric]
else:
    loss = eval_metrics[metric]
```

#### 修改位置 3: `_solve_beta_adam` 方法 - 梯度计算 (第 664-668 行)
```python
if metric == "correlation" or metric.endswith("_correlation"):
    loss_plus = -eval_metrics_plus[metric] + 0.001 * (log_beta_plus**2)
else:
    loss_plus = eval_metrics_plus[metric] + 0.001 * (log_beta_plus**2)
```

### 关键特性保证

✅ **输出值正确**: 虽然内部使用负相关性优化，但 `final_metrics['correlation']` 始终返回**正值**

✅ **向后兼容**: 不影响其他指标的优化行为

✅ **两种方法都修复**: `minimize` (scipy) 和 `adam` 优化器都已修正

---

## 📊 优化行为对比

| 指标 | v1.1.1 (修复前) | v1.1.2 (修复后) | 正确性 |
|------|----------------|-----------------|--------|
| `cross_entropy` | ⬇️ 最小化 | ⬇️ 最小化 | ✅ 保持正确 |
| `correlation` | ⬇️ **最小化 (错误)** | ⬆️ **最大化** | ✅ **已修复** |
| `rmse` | ⬇️ 最小化 | ⬇️ 最小化 | ✅ 保持正确 |
| `mse` | ⬇️ 最小化 | ⬇️ 最小化 | ✅ 保持正确 |
| `mae` | ⬇️ 最小化 | ⬇️ 最小化 | ✅ 保持正确 |

---

## 🧪 测试验证

### 测试代码
```python
import pandas as pd
from r2sfca import R2SFCA

# 创建测试数据
df = pd.DataFrame({
    'Demand': [100, 200, 150, 180, 120],
    'Supply': [50, 75, 60, 55, 65],
    'TravelCost': [10, 20, 15, 25, 12],
    'DemandID': [1, 1, 2, 2, 3],
    'SupplyID': [1, 2, 1, 2, 1]
})

# 测试相关性优化
model = R2SFCA(df, decay_function='exponential')

# v1.1.2 应该正确最大化相关性
result_corr = model.solve_beta(metric='correlation')
print(f"Correlation optimized: {result_corr['final_metrics']['correlation']:.4f}")

# 对比：最小化交叉熵
result_ce = model.solve_beta(metric='cross_entropy')
print(f"Cross-entropy optimized correlation: {result_ce['final_metrics']['correlation']:.4f}")

# 验证：相关性优化应该得到更高的相关性
assert result_corr['final_metrics']['correlation'] >= result_ce['final_metrics']['correlation']
print("✓ 修复验证成功！")
```

### 预期结果
- ✅ `result_corr` 的相关性 ≥ `result_ce` 的相关性
- ✅ 输出的相关性为正数 (0 到 1 之间)
- ✅ 不会影响其他指标的优化

---

## 📦 上传到 PyPI 的步骤

### 方法 1: 使用自动化脚本 (推荐 Windows 用户)
```cmd
build_and_upload.bat
```

### 方法 2: 手动执行
```bash
# 1. 验证版本号
python verify_version.py

# 2. 清理并构建
rm -rf build/ dist/ *.egg-info/
python -m build

# 3. 检查包
python -m twine check dist/*

# 4. 上传到 PyPI
python -m twine upload dist/*
```

详细步骤请参考: `UPLOAD_STEPS.md`

---

## ✅ 发布前检查清单

- [x] 修复代码错误
- [x] 更新版本号 (1.1.1 → 1.1.2)
  - [x] setup.py
  - [x] pyproject.toml
  - [x] r2sfca/__init__.py
- [x] 更新 CHANGELOG.md
- [x] 清理旧的构建文件
- [x] 创建上传辅助脚本
- [ ] 构建新的分发包 (`python -m build`)
- [ ] 检查包的完整性 (`twine check dist/*`)
- [ ] 上传到 PyPI (`twine upload dist/*`)
- [ ] 验证安装和功能
- [ ] 创建 Git tag (v1.1.2)
- [ ] 创建 GitHub Release

---

## 📞 需要帮助？

如果在上传过程中遇到问题，请参考:
1. `UPLOAD_STEPS.md` - 详细步骤和故障排除
2. `upload_to_pypi.md` - 完整的 PyPI 上传指南
3. CHANGELOG.md - 查看所有版本的更新历史

---

**状态**: ✅ 代码已修复，版本号已更新，准备构建和上传  
**下一步**: 运行 `build_and_upload.bat` 或按照 `UPLOAD_STEPS.md` 手动执行

