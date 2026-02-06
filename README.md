# AutoCase

![CI](https://github.com/AlexWuYh/AutoCase/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)

AutoCase 是一个轻量、可扩展的“LLM 自动生成测试用例”工具，支持按固定 YAML 输入格式生成标准测试用例 Excel/CSV 表格。

**核心特性**
- 基于 YAML 输入的批量功能点解析
- 直接调用 LLM 生成测试用例
- 输出美化后的 Excel（含表头样式、斑马纹、冻结首行、自动筛选），也支持 CSV
- 适配本地 LLM（通过 `base_url` 与 `api_mode`）

**项目结构**
- `src/autocase/cli.py` 命令行入口
- `src/autocase/llm_client.py` LLM 调用与重试逻辑
- `src/autocase/generator.py` 用例结构转换与输出
- `src/autocase/parser.py` YAML 解析
- `config/llm.yaml` 大模型参数配置
- `config/system_prompt.txt` 系统级 prompt
- `inputs/` 默认输入目录
- `outputs/` 默认输出目录

**安装部署**

**环境要求**
- Python 3.9+

**安装方式**
1. 安装依赖
```bash
pip3 install -r requirements.txt
```

2. 以开发模式安装命令
```bash
pip3 install -e .
```

安装完成后即可使用 `autocase` 命令。

**一键系统级安装（macOS / Linux 推荐）**

```bash
./install.sh
```

说明：该脚本优先使用 `pipx` 进行系统级安装；若未安装，会尝试通过 `brew` 或 `apt` 安装 `pipx`。

**一键卸载**

```bash
./uninstall.sh
```

**Makefile 快捷命令**

```bash
make install
make uninstall
```

**Windows 安装与运行适配**

说明：Windows 不支持 `install.sh`/`uninstall.sh`，建议使用虚拟环境安装。

1. 创建并激活虚拟环境（PowerShell）
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 安装依赖与命令
```powershell
pip install -r requirements.txt
pip install -e .
```

3. 运行示例
```powershell
autocase -f input.example.yaml
```

如果 `autocase` 命令不可用，可使用：
```powershell
py -m autocase.cli -f input.example.yaml
```

**快速开始**

1. 准备输入文件（默认放在 `inputs/`）

示例文件位置：`inputs/input.example.yaml`

2. 执行生成
```bash
autocase -f input.example.yaml
```

生成文件默认输出到 `outputs/`，文件名规则见“输出规则”。

**命令行使用说明**

**基础用法**
- `autocase` 打印 Banner 与帮助
- `autocase -h` 打印帮助
- `autocase -f xxxx.yaml` 生成 Excel（默认 .xlsx）

**常用参数**
- `-f/--file` 输入 YAML 文件
- `--llm-config` 大模型参数配置
- `--prompt` 系统级 prompt
- `-o/--output` 输出文件路径（支持 .xlsx 或 .csv）
- `--no-banner` 关闭启动 Banner
- `--json-only` 仅输出 JSON 到 STDOUT

**输出规则**
- 输入文件默认从 `inputs/` 目录读取
- 输出文件默认写入 `outputs/` 目录
- 当仅指定 `-f` 时，输出文件名为 `{输入文件名}_testcases.xlsx`
- 当指定 `-o` 时，使用用户自定义名称（相对路径默认落在 `outputs/`）
- 当输出目录不存在时会自动创建

**输入格式说明（YAML CaseSpec）**

支持批量输入，`cases` 数组包含多组功能点：

```yaml
cases:
  - module: 系统设置 / 业务设置 / 机构场地
    feature: 机构场地管理-新增场地
    description: 支持管理员新增场地，包含名称、地址、容量；校验名称唯一；可保存成功或提示错误
    keywords:
      - 金砖
      - 睿镜
  - module: 订单中心 / 退款管理
    feature: 退款申请-发起
    description: 用户发起退款申请，校验订单状态，生成退款单
    keywords: 退款, 订单
```

支持中文键名别名：`模块/功能/描述/关键词`。

**LLM 配置说明**

配置文件：`config/llm.yaml`

常见字段：
- `provider` 目前默认 `openai`
- `enabled` 是否启用 LLM
- `api_key_env` API Key 环境变量名（默认 `OPENAI_API_KEY`）
- `base_url` 本地 LLM 服务地址
- `api_mode` `responses` 或 `chat_completions`
- `model` 模型名称
- `temperature` / `top_p` / `max_tokens` 等采样参数
- `retry_count` JSON 解析失败重试次数
- `retry_prompt_suffix` 重试时追加的提示

**API Key 环境变量配置**
1. 在 `config/llm.yaml` 中设置 `api_key_env`（默认 `OPENAI_API_KEY`）
2. 在系统环境变量中设置对应变量

示例（macOS / Linux）：
```bash
export OPENAI_API_KEY=你的Key
```

示例（Windows PowerShell）：
```powershell
$env:OPENAI_API_KEY="你的Key"
```

如果你使用自定义变量名（例如 `MY_LLM_KEY`），则需要在 `config/llm.yaml` 中设置：
```yaml
api_key_env: MY_LLM_KEY
```

**本地部署大模型配置示例**
以下示例适配“兼容 OpenAI API”的本地服务（如 LM Studio / vLLM / Ollama OpenAI 兼容端口等）：
```yaml
enabled: true
provider: openai
api_key_env: LOCAL_LLM_KEY
base_url: http://127.0.0.1:8000/v1
api_mode: chat_completions
model: Qwen2.5-7B-Instruct
temperature: 0.2
max_tokens: 2000
```

并设置环境变量：
```bash
export LOCAL_LLM_KEY=anything
```

**系统级 Prompt**
- 默认文件：`config/system_prompt.txt`
- 你可以直接修改此文件来改变生成风格、覆盖范围与质量要求

**本地 LLM 兼容**
- 若本地服务仅支持 Chat Completions 风格接口，请在 `config/llm.yaml` 中设置 `api_mode: chat_completions` 并填写 `base_url`
- 若 JSON 解析失败，可在 `config/llm.yaml` 中调整 `retry_count` 与 `retry_prompt_suffix`

**JSON-only 输出**

```bash
autocase -f input.example.yaml --json-only > output.json
```

说明：`steps` 与 `expected` 字段在 JSON-only 输出中为数组，并与步骤严格一一对应。

**示例命令**

```bash
export OPENAI_API_KEY=你的Key
autocase -f input.example.yaml
```

```bash
autocase -f input.example.yaml -o my_cases.xlsx
autocase -f input.example.yaml -o my_cases.csv
```

**输出格式**
- 输出为 `.xlsx` 或 `.csv`，可直接导入用例管理系统
- 默认列头顺序：用例ID、所属模块、用例名称、前置条件、步骤、预期、关键词、优先级、用例类型、适用阶段

**常见问题**

- 提示缺少依赖：请执行 `pip3 install -r requirements.txt`
- 提示 API Key 未找到：请设置 `OPENAI_API_KEY` 或在 `config/llm.yaml` 修改 `api_key_env`
- 解析失败：检查输入 YAML 是否符合格式
- 输入文件不存在：确认文件在 `inputs/` 目录或传入正确路径

**扩展建议**
- 调整 `config/system_prompt.txt` 以适配不同测试规范
- 如需自定义输出样式，可调整 `src/autocase/cli.py` 的 Excel 样式段
