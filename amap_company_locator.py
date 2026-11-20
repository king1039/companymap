import json
from pathlib import Path
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


AMAP_KEY = "d441e1c0ef8feb75ec1f6d2781ed2a6d"
AMAP_POI_SEARCH_URL = "https://restapi.amap.com/v3/place/text"
REQUEST_TIMEOUT_SECONDS = 15
REQUEST_INTERVAL_SECONDS = 1.2
EXCLUDED_POI_KEYWORDS = (
    "专卖店",
    "授权店",
    "体验馆",
    "维修中心",
    "电脑城",
    "家电",
    "驿站",
    "商城",
    "门店",
    "零售",
    "京东",
    "苏宁",
)
PREFERRED_POI_KEYWORDS = (
    "有限公司",
    "分公司",
    "总部",
    "办公室",
    "写字楼",
    "中心",
    "广场",
)


class AMapAPIError(Exception):
    """Raised when the AMap service returns an unsuccessful response."""


def empty_result(company_name: str, status: str) -> dict[str, Any]:
    return {
        "company_name": company_name,
        "poi_name": None,
        "address": None,
        "district": None,
        "lng": None,
        "lat": None,
        "status": status,
    }


def parse_company_line(line: str) -> tuple[str, str]:
    display_name, separator, keyword = line.partition("|")
    display_name = display_name.strip()
    if not display_name:
        raise ValueError(f"Company name is empty in line: {line!r}")

    search_keyword = keyword.strip() if separator else display_name
    if not search_keyword:
        raise ValueError(f"Search keyword is empty in line: {line!r}")
    return display_name, search_keyword


def fetch_pois(keywords: str) -> list[dict[str, Any]]:
    query = urlencode(
        {
            "key": AMAP_KEY,
            "keywords": keywords,
            "city": "广州",
            "offset": 20,
            "page": 1,
            "extensions": "base",
        }
    )
    request = Request(
        f"{AMAP_POI_SEARCH_URL}?{query}",
        headers={"User-Agent": "CompanyMap/1.0"},
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    finally:
        time.sleep(REQUEST_INTERVAL_SECONDS)

    if str(payload.get("status")) != "1":
        raise AMapAPIError(payload.get("info", "AMap POI search failed"))

    return payload.get("pois") or []


def select_poi(pois: list[dict[str, Any]]) -> dict[str, Any] | None:
    eligible_pois: list[dict[str, Any]] = []
    for poi in pois:
        searchable_text = str(poi.get("name") or "")
        if any(keyword in searchable_text for keyword in EXCLUDED_POI_KEYWORDS):
            continue
        eligible_pois.append(poi)

    for poi in eligible_pois:
        searchable_text = str(poi.get("name") or "")
        if any(keyword in searchable_text for keyword in PREFERRED_POI_KEYWORDS):
            return poi

    return eligible_pois[0] if eligible_pois else None


def make_company_result(company_name: str, poi: dict[str, Any]) -> dict[str, Any]:
    location = poi.get("location", "")
    coordinates = location.split(",", maxsplit=1)
    if len(coordinates) != 2:
        raise ValueError(f"POI has an invalid location: {location!r}")

    try:
        lng, lat = (float(coordinate) for coordinate in coordinates)
    except ValueError as exc:
        raise ValueError(f"POI has an invalid location: {location!r}") from exc

    return {
        "company_name": company_name,
        "poi_name": poi.get("name"),
        "address": poi.get("address"),
        "district": poi.get("adname"),
        "lng": lng,
        "lat": lat,
    }


def search_company(
    display_name: str, search_keyword: str
) -> dict[str, Any]:
    queries = [search_keyword, f"{search_keyword} 广州"]
    for keywords in queries:
        poi = select_poi(fetch_pois(keywords))
        if poi is not None:
            return make_company_result(display_name, poi)

    return empty_result(display_name, "NOT_FOUND")


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    input_path = project_dir / "companies.txt"
    output_path = project_dir / "companies_guangzhou.json"

    if not input_path.is_file():
        raise FileNotFoundError(f"Company list not found: {input_path}")

    companies: list[tuple[str, str]] = []
    for line in input_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        companies.append(parse_company_line(line))

    if not companies:
        raise ValueError(f"No company names found in {input_path}")

    results: list[dict[str, Any]] = []
    for index, (display_name, search_keyword) in enumerate(companies, start=1):
        print(f"{index}/{len(companies)} - {display_name}", flush=True)
        try:
            result = search_company(display_name, search_keyword)
        except (
            AMapAPIError,
            HTTPError,
            URLError,
            TimeoutError,
            json.JSONDecodeError,
            ValueError,
        ) as exc:
            result = empty_result(display_name, "ERROR")
            result["error"] = str(exc)
            print(f"[ERROR] {display_name} -> {exc}", flush=True)
        else:
            if result.get("status") == "NOT_FOUND":
                print(f"[NOT_FOUND] {display_name}", flush=True)
            else:
                print(f"[OK] {display_name} -> {result['poi_name']}", flush=True)
        results.append(result)

    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    success_count = sum("status" not in result for result in results)
    failure_count = len(results) - success_count
    print(f"总数：{len(results)}")
    print(f"成功数：{success_count}")
    print(f"失败数：{failure_count}")
    print(f"结果文件：{output_path}")


if __name__ == "__main__":
    main()
