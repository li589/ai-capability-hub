---
kind: "repo_knowledge"
category: "dependency_management"
title: "Python 依赖管理：无统一清单的脚本式依赖声明"
scopes: ["**"]
updated_at: "2026-07-30T06:34:27Z"
---

# Python 依赖管理：无统一清单的脚本式依赖声明

本仓库为科研数据与模型分析项目，**未采用任何统一的 Python 依赖管理系统**（如 requirements.txt、pyproject.toml、Pipfile、poetry.lock、conda environment.yml 等），也未发现 Go/Node/Rust/C++ 等语言的包管理文件。依赖声明呈现以下特征：

1. **直接 import 声明依赖**：所有 Python 脚本通过 `import` / `from ... import` 直接引入第三方库，如 `torch`、`numpy`、`pandas`、`sklearn`、`matplotlib`、`seaborn`、`networkx`、`tqdm` 等，未见集中化的版本约束。
2. **本地虚拟环境隔离**：根目录存在 `Code/venv` 目录（已被忽略或不存在于当前分支快照），表明开发者使用 Python 虚拟环境隔离依赖，但未将环境状态纳入版本控制。
3. **Jupyter Notebook 内嵌安装记录**：在 `Code/ShowTime/Hyper-TCDF-Show-V2.ipynb` 中可见 `pip install` 及 `pyproject.toml` 构建日志，说明部分依赖通过 Notebook 运行时临时安装，而非预先声明。
4. **硬编码路径与环境耦合**：配置文件（如 `Hyper-TCDF/V6.1/config.py`、`EM-DAT/config_emdat.py`）中大量使用绝对路径（`E:\TCDF\...`、`/share/home/user03/...`），表明代码强绑定特定开发/服务器环境，进一步削弱了可移植性。
5. **无锁定文件或私有源配置**：未发现 `requirements.txt`、`poetry.lock`、`pipenv.lock`、`go.sum`、`package-lock.json` 等锁定文件，也无 `~/.pip/pip.conf`、`~/.config/pip/pip.conf`、`.npmrc`、`.gitconfig` 中的私有源或代理配置痕迹。

**对开发者的建议**：
- 在项目根目录创建 `requirements.txt` 或 `pyproject.toml`，集中声明所有第三方依赖及其版本范围。
- 使用 `pip freeze > requirements.txt` 或 `poetry export -f requirements.txt` 生成锁定文件，确保环境可复现。
- 避免在代码中硬编码绝对路径，改用相对路径或环境变量注入。
- 将虚拟环境目录（如 `venv/`、`.venv/`）加入 `.gitignore`，仅提交依赖清单。
- 若需私有包源，应在 CI/CD 或部署脚本中统一配置，而非分散在各脚本中。
