# 上传 R2SFCA v1.1.2 到 PyPI 的步骤

## 版本 1.1.2 更新内容

**修复内容：**
- ✅ 修复 `solve_beta` 方法中相关性优化问题
- ✅ Correlation 指标现在正确地被**最大化**而不是最小化
- ✅ Cross-entropy, RMSE, MSE, MAE 继续正确地被最小化
- ✅ 输出的 correlation 值保持为正数

---

## 快速上传步骤

### 方法 1: 使用自动化脚本 (Windows)

```cmd
build_and_upload.bat
```

然后按照提示上传：
```cmd
python -m twine upload dist/*
```

### 方法 2: 手动执行命令

#### 1. 验证版本号
```bash
python verify_version.py
```

#### 2. 安装/升级构建工具
```bash
python -m pip install --upgrade pip build twine
```

#### 3. 清理旧构建
```bash
# Windows PowerShell
Remove-Item -Recurse -Force build, dist, r2sfca.egg-info -ErrorAction SilentlyContinue

# Linux/Mac
rm -rf build/ dist/ *.egg-info/
```

#### 4. 构建分发包
```bash
python -m build
```

这将生成:
- `dist/r2sfca-1.1.2-py3-none-any.whl`
- `dist/r2sfca-1.1.2.tar.gz`

#### 5. 检查包
```bash
python -m twine check dist/*
```

#### 6. 上传到 PyPI

**选项 A: 先上传到测试 PyPI (推荐)**
```bash
python -m twine upload --repository testpypi dist/*
```

测试安装:
```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps r2sfca
```

**选项 B: 直接上传到正式 PyPI**
```bash
python -m twine upload dist/*
```

---

## PyPI 认证

### 使用 API Token (推荐)

1. 登录 https://pypi.org/
2. 进入 Account Settings > API tokens
3. 创建 token (如果是首次上传，选择 "Entire account" scope)
4. 复制 token

上传时输入:
- Username: `__token__`
- Password: `pypi-AgE...` (你的 API token)

### 或者配置 ~/.pypirc
```ini
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-你的API-token
```

---

## 验证上传

### 1. 检查 PyPI 页面
https://pypi.org/project/r2sfca/

### 2. 测试安装
```bash
pip install --upgrade r2sfca
```

### 3. 验证版本
```python
import r2sfca
print(r2sfca.__version__)  # 应该显示: 1.1.2
```

### 4. 测试修复的功能
```python
import pandas as pd
from r2sfca import R2SFCA

# 创建测试数据
df = pd.DataFrame({
    'Demand': [100, 200, 150],
    'Supply': [50, 75, 60],
    'TravelCost': [10, 20, 15],
    'DemandID': [1, 1, 2],
    'SupplyID': [1, 2, 1]
})

# 测试相关性优化
model = R2SFCA(df, decay_function='exponential')
result = model.solve_beta(metric='correlation')  # 现在会最大化相关性

print(f"优化后的 beta: {result['optimal_beta']:.4f}")
print(f"相关性 (应该是正数): {result['final_metrics']['correlation']:.4f}")
print("✓ 修复验证成功！")
```

---

## 发布后任务

### 1. 创建 Git Tag
```bash
git add .
git commit -m "Release v1.1.2: Fix correlation maximization in solve_beta"
git tag -a v1.1.2 -m "Version 1.1.2 - Fix correlation optimization"
git push origin main --tags
```

### 2. 创建 GitHub Release
- 访问 GitHub repository
- 创建新的 Release: v1.1.2
- 复制 CHANGELOG 中的更新内容

### 3. 通知用户 (如果需要)
```markdown
📦 R2SFCA v1.1.2 已发布！

🐛 修复内容:
- 修复了 solve_beta 方法中相关性优化的问题
- Correlation 现在正确地被最大化而不是最小化

📥 安装/更新:
pip install --upgrade r2sfca
```

---

## 故障排除

### 问题 1: `python` 命令不存在
**解决方案**: 
- Windows: 使用 `py` 命令
- 或确保 Python 已添加到 PATH

### 问题 2: twine 认证失败
**解决方案**:
- 确保使用 `__token__` 作为用户名
- Token 应该以 `pypi-` 开头
- 检查 token 是否有正确的权限

### 问题 3: 包名或版本冲突
**解决方案**:
- 确保版本号递增 (1.1.1 -> 1.1.2)
- 无法重新上传相同版本号

### 问题 4: 构建失败
**解决方案**:
```bash
# 清理所有缓存
python -m pip cache purge
python -m pip install --upgrade setuptools wheel build

# 重新构建
python -m build
```

---

## 命令速查表

```bash
# 完整流程 (一键复制)
python verify_version.py
python -m pip install --upgrade pip build twine
rm -rf build/ dist/ *.egg-info/  # Linux/Mac
python -m build
python -m twine check dist/*
python -m twine upload dist/*  # 输入你的 PyPI token
```

---

**版本**: 1.1.2  
**发布日期**: 2025-10-14  
**主要修复**: Correlation maximization in solve_beta method

