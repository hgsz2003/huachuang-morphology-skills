# -*- coding: utf-8 -*-
"""
华创形态学 API CLI：从 scripts/config.json 读取 token，调用 HuaChuangMorphologyAPI 方法，向 stdout 输出 JSON。
用法:
  python morphology_cli.py <方法名> '[JSON 参数字符串]'
示例:
  python morphology_cli.py get_basic_info
  python morphology_cli.py get_historical_data '{"win_rate":0.6,"trade_date":"2024-01-02","position":"负面"}'
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import numpy as np
import pandas as pd

from morphology_api import HuaChuangMorphologyAPI
CONFIG_PATH = SCRIPT_DIR / "config.json"


def load_config() -> dict:
    if not CONFIG_PATH.is_file():
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"缺少配置文件: {CONFIG_PATH}。请复制 config.example.json 为 config.json 并填入 token。",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    token = (cfg.get("token") or "").strip()
    if not token:
        print(
            json.dumps({"ok": False, "error": "config.json 中 token 为空"}, ensure_ascii=False),
            file=sys.stderr,
        )
        sys.exit(1)
    return cfg


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"不可 JSON 序列化: {type(obj)}")


def normalize_for_json(obj: Any) -> Any:
    if isinstance(obj, pd.DataFrame):
        return json.loads(obj.to_json(orient="records", date_format="iso"))
    if isinstance(obj, dict):
        return {k: normalize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_for_json(x) for x in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    return obj


def serialize_result(result: Any) -> dict:
    if result is None:
        return {"ok": False, "error": "无数据或请求失败"}

    if isinstance(result, pd.DataFrame):
        records = json.loads(result.to_json(orient="records", date_format="iso"))
        return {"ok": True, "type": "dataframe", "rows": len(result), "data": records}

    if isinstance(result, dict):
        return {"ok": True, "type": "dict", "data": normalize_for_json(result)}

    if isinstance(result, str):
        return {"ok": True, "type": "text", "data": result}

    return {"ok": True, "type": "json", "data": json.loads(json.dumps(result, default=_json_default))}


def list_methods() -> list[str]:
    names = []
    for name, _ in inspect.getmembers(HuaChuangMorphologyAPI, predicate=inspect.isfunction):
        if name.startswith("get_") or name == "evaluate_etf_performance":
            names.append(name)
    return sorted(names)


def main() -> None:
    parser = argparse.ArgumentParser(description="华创形态学 API CLI")
    parser.add_argument(
        "method",
        nargs="?",
        help="API 方法名，如 get_basic_info；省略时与 --list 配合",
    )
    parser.add_argument(
        "kwargs_json",
        nargs="?",
        default="{}",
        help='JSON 对象字符串，作为关键字参数传入方法，默认 "{}"',
    )
    parser.add_argument("--list", action="store_true", help="列出可调用的方法名")
    args = parser.parse_args()

    if args.list:
        print(json.dumps({"ok": True, "methods": list_methods()}, ensure_ascii=False))
        return

    if not args.method:
        parser.error("请指定方法名，或使用 --list 查看列表")

    method_name = args.method
    allowed = set(list_methods())
    if method_name not in allowed:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"未知方法: {method_name}",
                    "allowed": sorted(allowed),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        kwargs = json.loads(args.kwargs_json) if args.kwargs_json.strip() else {}
        if not isinstance(kwargs, dict):
            raise ValueError("第二个参数必须是 JSON 对象")
    except (json.JSONDecodeError, ValueError) as e:
        print(json.dumps({"ok": False, "error": f"参数 JSON 无效: {e}"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    cfg = load_config()
    token = cfg["token"].strip()
    verify_ssl = cfg.get("verify_ssl", True)
    if not isinstance(verify_ssl, bool):
        verify_ssl = True

    client = HuaChuangMorphologyAPI(token, verify_ssl=verify_ssl)
    fn = getattr(client, method_name)
    sig = inspect.signature(fn)
    params = {k: v for k, v in kwargs.items() if k in sig.parameters}

    try:
        result = fn(**params)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    payload = serialize_result(result)
    print(json.dumps(payload, ensure_ascii=False, default=_json_default))


if __name__ == "__main__":
    main()
