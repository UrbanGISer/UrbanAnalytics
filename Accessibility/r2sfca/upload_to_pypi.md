# 上传 R2SFCA 到 PyPI 的步骤

## 准备工作

### 1. 确保所有文件完整
```
r2sfca/
├── __init__.py
├── core.py
├── utils.py
├── setup.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
├── MANIFEST.in
├── CHANGELOG.md
├── .gitignore
└── example_usage.py
```

### 2. 检查版本号一致性
- `__init__.py`: `__version__ = "1.0.0"`
- `setup.py`: `version="1.0.0"`
- `pyproject.toml`: `version = "1.0.0"`

## 安装构建工具

```bash
pip install --upgrade pip
pip install --upgrade build
pip install --upgrade twine
```

## 构建包

### 1. 清理之前的构建
```bash
cd r2sfca
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
```

### 2. 构建分发包
```bash
python -m build
```

这将创建：
- `dist/r2sfca-1.0.0-py3-none-any.whl` (wheel 格式)
- `dist/r2sfca-1.0.0.tar.gz` (源码分发包)

## 检查包

### 1. 检查构建的包
```bash
twine check dist/*
```

### 2. 测试安装
```bash
pip install dist/r2sfca-1.0.0-py3-none-any.whl
```

### 3. 验证安装
```python
import r2sfca
print(r2sfca.__version__)
from r2sfca import R2SFCA, DecayFunction
print("导入成功！")
```

## 上传到 PyPI

### 1. 注册 PyPI 账户
- 访问 https://pypi.org/account/register/
- 创建账户并验证邮箱

### 2. 获取 API Token
- 登录 PyPI
- 进入 Account Settings > API tokens
- 创建新的 API token
- 复制 token (格式: `pypi-...`)

### 3. 配置认证
```bash
# 方法1: 使用 .pypirc 文件
# 在用户主目录创建 ~/.pypirc
[distutils]
index-servers = pypi

[pypi]
username = __token__
password = pypi-your-api-token-here

# 方法2: 直接使用环境变量
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here
```

### 4. 上传到测试 PyPI (推荐先测试)
```bash
twine upload --repository testpypi dist/*
```

测试安装：
```bash
pip install --index-url https://test.pypi.org/simple/ r2sfca
```

### 5. 上传到正式 PyPI
```bash
twine upload dist/*
```

## 验证上传

### 1. 检查 PyPI 页面
- 访问 https://pypi.org/project/r2sfca/
- 确认包信息正确显示

### 2. 测试安装
```bash
pip install r2sfca
```

### 3. 验证功能
```python
import r2sfca
print(f"R2SFCA version: {r2sfca.__version__}")

import pandas as pd
from r2sfca import R2SFCA, DecayFunction

# 创建测试数据
df = pd.DataFrame({
    'Demand': [100, 200],
    'Supply': [50, 75],
    'TravelCost': [10, 20],
    'DemandID': [1, 2],
    'SupplyID': [1, 2]
})

# 测试模型
model = R2SFCA(df, decay_function='exponential')
print("模型创建成功！")
```

## 发布后维护

### 1. 创建 GitHub Release
- 在 GitHub 仓库创建 v1.0.0 标签
- 添加发布说明

### 2. 更新文档
- 确保 README.md 中的安装说明正确
- 更新示例代码

### 3. 监控反馈
- 关注 PyPI 下载统计
- 处理用户反馈和问题

## 常见问题

### 1. 包名冲突
如果 `r2sfca` 已被占用，考虑：
- `r2sfca-model`
- `r2sfca-spatial`
- `urban-r2sfca`

### 2. 版本号管理
- 使用语义化版本号 (Semantic Versioning)
- 主版本号.次版本号.修订号 (1.0.0)

### 3. 依赖管理
- 确保所有依赖在 requirements.txt 中声明
- 使用版本范围而不是固定版本

## 命令总结

```bash
# 完整的上传流程
cd r2sfca
rm -rf build/ dist/ *.egg-info/
python -m build
twine check dist/*
twine upload --repository testpypi dist/*  # 测试
twine upload dist/*  # 正式发布
pip install r2sfca  # 验证
```
