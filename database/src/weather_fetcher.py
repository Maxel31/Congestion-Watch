#!/usr/bin/env python3
"""
天気データ取得スクリプト
OpenWeather APIを使用して天気データを取得し、データベースに保存する
作成日: 2025-07-03
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import psycopg2
import requests
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherFetcher:
    def __init__(self) -> None:
        """天気データ取得クラス"""
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY環境変数が設定されていません")

        self.location = os.getenv("WEATHER_LOCATION", "Tokyo,JP")
        self.api_url = "https://api.openweathermap.org/data/2.5/weather"
        self.db_config = self._get_db_config()

    def _get_db_config(self) -> Dict[str, Any]:
        """データベース設定を取得"""
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "congestion_watch_dev"),
            "user": os.getenv("POSTGRES_USER", "congestion_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "secure_password"),
        }

    def fetch_current_weather(self) -> Optional[Dict[str, Any]]:
        """現在の天気データを取得"""
        try:
            params = {
                "q": self.location,
                "appid": self.api_key,
                "units": "metric",  # 摂氏温度
                "lang": "ja",  # 日本語
            }

            logger.info(f"天気データを取得中: {self.location}")
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 必要なデータを抽出
            weather_info = {
                "datetime": datetime.now(),
                "weather": f"{data['weather'][0]['main']} - {data['weather'][0]['description']}",
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data.get("wind", {}).get("speed", 0),
                "visibility": data.get("visibility", 0),
                "location": self.location,
            }

            logger.info(
                f"天気データ取得成功: {weather_info['weather']}, 気温: {weather_info['temperature']}°C"
            )
            return weather_info

        except requests.exceptions.RequestException as e:
            logger.error(f"API呼び出しエラー: {e}")
            return None
        except KeyError as e:
            logger.error(f"レスポンスデータ解析エラー: {e}")
            return None
        except Exception as e:
            logger.error(f"天気データ取得エラー: {e}")
            return None

    def save_weather_data(self, weather_info: Dict[str, Any]) -> bool:
        """天気データをデータベースに保存"""
        try:
            conn = psycopg2.connect(**self.db_config)

            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 同じ時刻のデータが既に存在するかチェック（分単位で重複チェック）
                cursor.execute(
                    """
                    SELECT id FROM weather 
                    WHERE date_trunc('minute', datetime) = date_trunc('minute', %s)
                    """,
                    (weather_info["datetime"],),
                )

                if cursor.fetchone():
                    logger.debug(
                        f"同じ時刻の天気データが既に存在します: {weather_info['datetime']}"
                    )
                    return True

                # 新しい天気データを挿入
                cursor.execute(
                    """
                    INSERT INTO weather (datetime, weather, created_at) 
                    VALUES (%s, %s, %s)
                    """,
                    (weather_info["datetime"], weather_info["weather"], datetime.now()),
                )

                conn.commit()
                logger.info(
                    f"天気データをデータベースに保存しました: {weather_info['weather']}"
                )
                return True

        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
            if "conn" in locals():
                conn.rollback()
            return False
        finally:
            if "conn" in locals():
                conn.close()

    def fetch_and_save_weather(self) -> bool:
        """天気データを取得してデータベースに保存"""
        weather_info = self.fetch_current_weather()
        if weather_info:
            return self.save_weather_data(weather_info)
        return False


def main() -> None:
    """メイン関数"""
    try:
        fetcher = WeatherFetcher()
        success = fetcher.fetch_and_save_weather()

        if success:
            logger.info("天気データの取得・保存が完了しました")
        else:
            logger.error("天気データの取得・保存に失敗しました")
            exit(1)

    except Exception as e:
        logger.error(f"実行エラー: {e}")
        exit(1)


if __name__ == "__main__":
    main()
