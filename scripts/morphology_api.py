# -*- coding: utf-8 -*-
"""华创金工形态学 API 客户端（供 skill CLI 调用）。"""
import datetime
import json
import logging
import warnings
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class HuaChuangMorphologyAPI:
    """华创金工形态学 API 客户端。"""

    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://mark.hcquant.com/all_api"
        self.timing_base_url = "https://xingtai.pro"
        self.logger = logging.getLogger(__name__)

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(
            {
                "User-Agent": "HuaChuang-API-Client/2.0",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        self.session.verify = False

        self.asset_codes = {
            "broad_index": [
                "000001.SH",
                "000016.SH",
                "000300.SH",
                "000510.CSI",
                "000852.SH",
                "000905.SH",
                "000906.SH",
                "399006.SZ",
                "881001.WI",
            ],
            "industry_codes": [f"CI00500{i}.WI" for i in range(1, 31)],
            "style_codes": [
                "000015.SH",
                "399372.SZ",
                "399373.SZ",
                "399374.SZ",
                "399375.SZ",
                "399376.SZ",
                "399377.SZ",
            ],
            "companies": {
                "fg": "富国",
                "js": "景顺长城",
                "yy": "永赢",
                "htbr": "华泰柏瑞",
                "hx": "华夏",
                "bs": "博时",
                "nf": "南方",
                "th": "天弘",
                "ph": "鹏华",
                "efund": "易方达",
            },
        }

    def _parse_json_text(self, text: str) -> Union[pd.DataFrame, Dict, List, str]:
        if not text:
            return None
        try:
            if text.startswith("[") or text.startswith("{"):
                data = json.loads(text)
                if isinstance(data, list):
                    return pd.DataFrame(data)
                return data
            return pd.read_json(text)
        except (ValueError, json.JSONDecodeError):
            self.logger.warning("JSON 解析失败，返回原始文本")
            return text

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Union[pd.DataFrame, Dict, str, None]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                if not response.text:
                    self.logger.warning("响应内容为空: %s", url)
                    return None
                return self._parse_json_text(response.text)
            except requests.exceptions.SSLError as e:
                self.logger.warning("SSL 错误 (%s/%s): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    continue
                return None
            except requests.exceptions.ConnectionError as e:
                self.logger.warning("连接错误 (%s/%s): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    continue
                return None
            except requests.exceptions.Timeout as e:
                self.logger.warning("超时 (%s/%s): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    continue
                return None
            except requests.exceptions.RequestException as e:
                self.logger.error("请求失败: %s, %s", url, e)
                return None
        return None

    def unix_to_date(self, timestamp: int) -> datetime.datetime:
        return datetime.datetime.utcfromtimestamp(timestamp / 1000)

    def get_basic_info(self) -> pd.DataFrame:
        return self._make_request(f"{self.base_url}/basic.php", {"token": self.token})

    def get_supported_assets(self) -> pd.DataFrame:
        return self._make_request(f"{self.base_url}/get_sid.php", {"token": self.token})

    def get_latest_daily_stats(self) -> pd.DataFrame:
        return self._make_request(f"{self.base_url}/all.php", {"token": self.token})

    def get_historical_data(
        self,
        win_rate: float = 0.6,
        trade_date: Optional[str] = None,
        position: str = "负面",
    ) -> pd.DataFrame:
        if trade_date is None:
            trade_date = datetime.datetime.now().strftime("%Y-%m-%d")
        return self._make_request(
            f"{self.base_url}/fullfun.php",
            {
                "token": self.token,
                "win": win_rate,
                "tr": trade_date,
                "pos": position,
            },
        )

    def get_broad_index_timing(self) -> pd.DataFrame:
        return self._make_request(f"{self.base_url}/indextiming.php", {"token": self.token})

    def get_industry_timing(self) -> pd.DataFrame:
        return self._make_request(f"{self.base_url}/indtiming.php", {"token": self.token})

    def get_style_timing(self) -> pd.DataFrame:
        return self._make_request(f"{self.base_url}/styletiming.php", {"token": self.token})

    def get_concept_timing(self) -> pd.DataFrame:
        return self._make_request(f"{self.base_url}/concepttiming.php", {"token": self.token})

    def _fetch_timing_json(self, url: str) -> Optional[Dict[str, Any]]:
        response = self.session.get(url)
        if response.status_code != 200:
            return None
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                data = eval(response.text)  # noqa: S307 — 与服务端历史格式兼容
        if isinstance(data, dict) and "betime" in data:
            time_df = pd.DataFrame(data["betime"], columns=["begindate", "enddate"])
            time_df["begindate"] = time_df["begindate"].apply(self.unix_to_date)
            time_df["enddate"] = time_df["enddate"].apply(self.unix_to_date)
            data["processed_time"] = time_df
        return data

    def get_historical_broad_timing(self, asset_code: str = "881001.WI") -> Optional[Dict]:
        return self._fetch_timing_json(f"{self.timing_base_url}/timing/{asset_code}.json")

    def get_historical_industry_timing(self, asset_code: str = "CI005001.WI") -> Optional[Dict]:
        return self._fetch_timing_json(f"{self.timing_base_url}/indtiming/{asset_code}.json")

    def get_historical_style_timing(self, asset_code: str = "000015.SH") -> Optional[Dict]:
        return self._fetch_timing_json(f"{self.timing_base_url}/styletiming/{asset_code}.json")

    def get_historical_concept_timing(self, asset_code: str = "884030.WI") -> Optional[Dict]:
        return self._fetch_timing_json(f"{self.timing_base_url}/concepttiming/{asset_code}.json")

    def get_etf_cross_section_signal(self, company: str = "fg") -> pd.DataFrame:
        return self._make_request(
            f"{self.base_url}/etfnow.php",
            {"token": self.token, "company": company},
        )

    def get_etf_historical_signal(self, asset_code: str = "000300.SH", company: str = "th") -> Optional[Dict]:
        folder_mapping = {
            "th": "etftimingth",
            "htbr": "etftiminghtbr",
            "fg": "etftiming",
            "bs": "etftiming",
        }
        folder = folder_mapping.get(company, "etftiming")
        return self._fetch_timing_json(f"{self.timing_base_url}/{folder}/{asset_code}.json")

    def evaluate_etf_performance(self, asset_code: str = "000812.CSI") -> Optional[Dict]:
        try:
            from empyrical import annual_return, calmar_ratio, max_drawdown, sharpe_ratio, sortino_ratio
        except ImportError:
            self.logger.warning("未安装 empyrical，无法计算 ETF 绩效")
            return None

        url = f"{self.timing_base_url}/etftiming/{asset_code}.json"
        response = self.session.get(url)
        if response.status_code != 200:
            return None
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            data = eval(response.text)  # noqa: S307

        trade_data = pd.DataFrame(data["data"])
        trade_data.columns = [
            "unixtime",
            "open",
            "high",
            "low",
            "close",
            "amount",
            "cumret",
            "indcumret",
        ]
        trade_data["date"] = trade_data["unixtime"].apply(self.unix_to_date)
        trade_data = trade_data.set_index("date")

        time_df = pd.DataFrame(data["betime"], columns=["begindate", "enddate"])
        time_df["begindate"] = time_df["begindate"].apply(self.unix_to_date)
        time_df["enddate"] = time_df["enddate"].apply(self.unix_to_date)

        trade_data["signal"] = 0
        for _, row in time_df.iterrows():
            trade_data.loc[row["begindate"] : row["enddate"], "signal"] = 1

        trade_data["position"] = trade_data["signal"].shift(1)
        trade_data["return"] = trade_data["open"].shift(-1) / trade_data["open"] - 1
        trade_data = trade_data.dropna()

        strategy_returns = trade_data["return"] * trade_data["position"]
        benchmark_returns = trade_data["return"]

        return {
            "strategy_annual_return": float(annual_return(strategy_returns)),
            "strategy_max_drawdown": float(max_drawdown(strategy_returns)),
            "strategy_sharpe": float(sharpe_ratio(strategy_returns)),
            "strategy_sortino": float(sortino_ratio(strategy_returns)),
            "strategy_calmar": float(calmar_ratio(strategy_returns)),
            "benchmark_annual_return": float(annual_return(benchmark_returns)),
            "benchmark_max_drawdown": float(max_drawdown(benchmark_returns)),
            "benchmark_sharpe": float(sharpe_ratio(benchmark_returns)),
            "rows": len(trade_data),
        }

    def get_realtime_historical_data(self, trade_date: Optional[str] = None) -> pd.DataFrame:
        if trade_date is None:
            trade_date = datetime.datetime.now().strftime("%Y-%m-%d")
        return self._make_request(
            f"{self.base_url}/fullfun_realtime.php",
            {"token": self.token, "tr": trade_date},
        )

    def get_index_median_data(self, sid: str = "000300.SH") -> pd.DataFrame:
        url = (
            f"{self.base_url}/HK_median_data.php"
            if "HI" in sid
            else f"{self.base_url}/index_median_data.php"
        )
        return self._make_request(url, {"token": self.token, "sid": sid})

    def get_etf_median_data(self, company: str = "bs", sid: str = "000861.CSI") -> pd.DataFrame:
        return self._make_request(
            f"{self.base_url}/etf_median_data_all.php",
            {"token": self.token, "company": company, "sid": sid},
        )

    def get_etf_portal_data(self, sid: str = "000037.SH") -> Optional[Dict]:
        return self._fetch_timing_json(f"{self.timing_base_url}/etftimingV2/{sid}.json")

    def get_etf_scores(self) -> Optional[pd.DataFrame]:
        response = self.session.get(f"{self.timing_base_url}/etfv2/score_all.json")
        if response.status_code != 200:
            return None
        data = json.loads(response.text)
        return pd.DataFrame(data)
