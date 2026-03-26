# 华创金工形态学 API Skill 使用说明书

本文说明本 Skill 的**作用**、**功能**与**安装使用方法**。技术细节与接口列表以同目录下的 [SKILL.md](SKILL.md) 为准。

---

## 一、作用与适用场景

本 Skill 面向 **OpenClaw、Cursor Agent 等可执行脚本的智能体**，将「华创金工形态学」后端 HTTP 能力封装为：

- 固定目录下的 **命令行工具**（`scripts/morphology_cli.py`）；
- 通过 **JSON 标准输出** 返回结果，便于程序解析与对话中引用。

**典型使用场景包括：**

- 查询形态文字说明、系统支持的资产、最新日统计等基础数据；
- 获取宽基 / 行业 / 风格 / 概念指数的**最新截面择时信号**或**历史择时区间**；
- 获取 ETF 截面信号、历史信号、门户数据、得分及中间数据；
- 在已安装 `empyrical` 的前提下，对 ETF 信号做简单绩效指标计算。

数据来源为官方接口域名（见 SKILL 描述中的 `mark.hcquant.com`、`xingtai.pro`），**访问需有效 API Token**，Token 仅存放在本地配置文件中，不写入 Skill 正文。

---

## 二、功能概览

| 类别 | 能力摘要 |
|------|-----------|
| 基础数据 | 形态介绍、支持资产列表、最新日统计、带胜率与持仓方向的历史数据等 |
| 择时截面 | 宽基、行业、风格、概念四类指数的最新形态学信号 |
| 择时历史 | 上述四类指数按资产代码拉取历史 JSON，并附带可读的区间时间处理结果 |
| ETF | 按基金公司代码的截面信号、历史信号、门户数据、全市场得分、中间数据 |
| 其他 | 实时历史纯信号、指数中间数据（含港股指数识别）、可选 ETF 绩效评价 |

完整 **方法名与参数** 见 [SKILL.md](SKILL.md) 中的「方法速查」表；也可在安装后执行：

```bash
python scripts/morphology_cli.py --list
```

---

## 三、安装方法

### 3.1 环境要求

- **操作系统**：Windows / macOS / Linux 均可  
- **Python**：建议 **3.8 及以上**  
- **网络**：能访问形态学服务所在公网地址  

### 3.2 获取 Skill 文件

将本文件夹 **`huachuang-morphology`** 整目录复制到所需位置，例如：

- **课题/项目内**：放在你的工程目录下，与代码一起管理；  
- **个人 Cursor 技能目录**（可选）：复制到 `~/.cursor/skills/huachuang-morphology/`，便于所有项目识别该 Skill。

目录内应至少包含：`SKILL.md`、`scripts/morphology_api.py`、`scripts/morphology_cli.py`、`scripts/config.example.json`、`scripts/requirements.txt`。

### 3.3 安装 Python 依赖

在 **本 Skill 根目录**（与 `SKILL.md` 同级）打开终端，执行：

```bash
pip install -r scripts/requirements.txt
```

若仅需基础拉数、不做 ETF 绩效指标，可暂不安装 `empyrical`；使用 `evaluate_etf_performance` 前需确保已安装 `empyrical`。

### 3.4 配置 Token（必做）

1. 将 `scripts/config.example.json` **复制**为同目录下的 **`scripts/config.json`**。  
2. 用文本编辑器打开 `scripts/config.json`，将 `token` 改为你的 **真实 API Token**，例如：

```json
{
  "token": "此处填写你的真实Token"
}
```

3. **不要将 `config.json` 提交到公共仓库**。本仓库已提供 `.gitignore` 忽略 `scripts/config.json`，请保持该习惯。

### 3.5 验证安装

在 Skill 根目录执行：

```bash
python scripts/morphology_cli.py --list
```

若输出包含 `"ok": true` 与方法名列表，说明 CLI 可运行。再执行（需 Token 有效、网络可达）：

```bash
python scripts/morphology_cli.py get_basic_info
```

若返回 `"ok": true` 且 `data` 中有数据，则安装与配置成功。

---

## 四、基本用法（人类用户与 Agent）

在 **Skill 根目录** 下：

```bash
python scripts/morphology_cli.py <方法名> '[JSON参数字符串]'
```

- **第一个参数**：API 方法名（与 `morphology_api.py` 中一致，如 `get_basic_info`）。  
- **第二个参数**（可选）：JSON 对象字符串，作为该方法的**关键字参数**；未写的参数使用代码中的默认值。  

示例：

```bash
python scripts/morphology_cli.py get_basic_info
python scripts/morphology_cli.py get_historical_data "{\"win_rate\":0.6,\"trade_date\":\"2024-01-02\",\"position\":\"负面\"}"
```

> **Windows PowerShell 提示**：JSON 中含双引号时，外层可用单引号包住整段 JSON，或对内部双引号转义为 `\"`（如上例）。

**返回约定简述：**

- 成功：`ok: true`，`type` 标明 `dataframe` / `dict` / `text` / `json`，业务数据多在 `data` 中。  
- 失败：`ok: false`，`error` 为说明；部分提示可能同时在 stderr。  

---

## 五、安全与合规提示

- Token 等同于账号密钥，**仅限本机或受信环境**使用，勿泄露、勿截图外传。  
- 本客户端对 HTTPS 校验策略与官方示例环境可能一致（如关闭证书校验），请在合规网络环境下使用。  
- 调用频率请遵守服务方约定，避免过高并发影响服务。

---

## 六、文档与故障排查

| 问题 | 建议 |
|------|------|
| 提示缺少 `config.json` | 按 3.4 节复制并填写 `config.json`。 |
| `token 为空` | 检查 JSON 格式与字段名是否为 `token`。 |
| `evaluate_etf_performance` 失败 | 执行 `pip install empyrical` 后重试。 |
| 网络超时或 SSL 错误 | 检查本机网络、代理与防火墙；必要时联系服务提供方。 |

更细的 **Agent 执行约定** 与 **脚本文件说明** 见 [SKILL.md](SKILL.md)；**各接口 URL、参数与返回结构** 见 [接口说明.md](接口说明.md)。

---

*文档版本：与当前 `huachuang-morphology` 目录结构对应；若移动目录，请以实际路径替换文中命令。*
