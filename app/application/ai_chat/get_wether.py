import requests
from aws_lambda_powertools import Logger

logger = Logger()


def get_wether(region_code: str) -> str:

    if not region_code:
        logger.error("Region Code not found")
        return ""

    try:
        response = requests.get(
            f"https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{region_code}.json",
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        return data.get("text", "")

    except Exception as e:
        logger.exception("Failed to fetch forecast")
        return ""
