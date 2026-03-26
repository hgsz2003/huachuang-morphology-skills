---
name: huachuang-morphology-api
description: 调用华创金工形态学 HTTP API（基础形态、择时截面/历史、ETF 信号与中间数据等）。在用户询问形态学、择时信号、ETF 截面/历史、指数中间数据或需拉取 mark.hcquant.com / xingtai.pro 数据时使用；通过运行 scripts 目录下 CLI 并读取 scripts/config.json 中的 token 完成请求。
---

# 华创金工形态学 API（OpenClaw / Agent Skill）

## 前置条件

1. Python 3.8+，安装依赖：

   ```bash
   pip install -r scripts/requirements.txt
   ```

2. **Token 配置（必填）**：在 skill 目录下的 `scripts/config.json` 中存放密钥（勿提交版本库）。

   - 复制 `scripts/config.example.json` 为 `scripts/config.json`
   - 将 `token` 字段改为有效 API Token

   ```json
   {
     "token": "你的真实Token"
   }
   ```

## 调用方式

在 skill 根目录（本文件所在目录）执行：

```bash
python scripts/morphology_cli.py <方法名> '[可选：JSON参数字符串]'
```

- 成功时 stdout 为 JSON：`ok: true`，`type` 为 `dataframe` / `dict` / `text` / `json`，数据在 `data` 字段（DataFrame 为行对象数组）。
- 失败时 `ok: false`，`error` 说明原因；部分错误信息在 stderr。

列出全部可调用方法：

```bash
python scripts/morphology_cli.py --list
```

### 参数说明

第二个参数为 **JSON 对象**，键名须与 Python 方法参数一致，仅支持的键会被传入（多余键忽略）。

示例：

```bash
python scripts/morphology_cli.py get_basic_info
python scripts/morphology_cli.py get_historical_data '{"win_rate":0.6,"trade_date":"2024-01-02","position":"负面"}'
python scripts/morphology_cli.py get_index_median_data '{"sid":"000300.SH"}'
python scripts/morphology_cli.py get_etf_cross_section_signal '{"company":"fg"}'
```

## 方法速查（与 `morphology_api.py` 一致）

| 方法 | 作用 |
|------|------|
| `get_basic_info` | 全部形态文字介绍 |
| `get_supported_assets` | 系统支持的资产 |
| `get_latest_daily_stats` | 全部资产最新日统计 |
| `get_historical_data` | 历史数据（参数：`win_rate`, `trade_date`, `position`） |
| `get_broad_index_timing` | 宽基指数最新截面信号 |
| `get_industry_timing` | 行业指数最新截面信号 |
| `get_style_timing` | 风格指数最新截面信号 |
| `get_concept_timing` | 概念指数最新截面信号 |
| `get_historical_broad_timing` | 宽基历史择时（`asset_code`） |
| `get_historical_industry_timing` | 行业历史择时（`asset_code`） |
| `get_historical_style_timing` | 风格历史择时（`asset_code`） |
| `get_historical_concept_timing` | 概念历史择时（`asset_code`） |
| `get_etf_cross_section_signal` | ETF 截面信号（`company` 如 fg/th/bs） |
| `get_etf_historical_signal` | ETF 历史信号（`asset_code`, `company`） |
| `evaluate_etf_performance` | ETF 信号绩效（需 empyrical，`asset_code`） |
| `get_realtime_historical_data` | 实时历史纯信号（`trade_date`） |
| `get_index_median_data` | 指数中间数据（`sid`，港股含 HI 走港股接口） |
| `get_etf_median_data` | ETF 中间数据（`company`, `sid`） |
| `get_etf_portal_data` | ETF 门户 JSON（`sid`） |
| `get_etf_scores` | 最新 ETF 得分 |

常用公司代码 `company`：`fg` 富国、`th` 天弘、`bs` 博时、`htbr` 华泰柏瑞等（完整映射见 `morphology_api.py` 中 `asset_codes['companies']`）。

## Agent 执行约定

1. 先确认 `scripts/config.json` 存在且含有效 `token`；若缺失，提示用户复制 `config.example.json` 并填写。
2. 需要表格数据时优先调用 CLI，用返回的 JSON 回答用户，必要时对 `data` 做摘要或筛选。
3. `evaluate_etf_performance` 未安装 `empyrical` 时会失败，可先 `pip install empyrical` 或换用其他接口。

## 脚本说明

- `scripts/morphology_api.py`：API 客户端实现。
- `scripts/morphology_cli.py`：命令行入口，读取 `scripts/config.json`。
- `scripts/config.example.json`：配置模板。
- `scripts/requirements.txt`：Python 依赖。

## 接口文档

HTTP 路径、Query 参数、返回值类型与 CLI 信封格式见 [接口说明.md](接口说明.md)。
