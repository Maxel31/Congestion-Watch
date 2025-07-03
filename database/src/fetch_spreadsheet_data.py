#!/usr/bin/env python3
"""
Googleスプレッドシートからデータを取得してデータベースに挿入するスクリプト
スプレッドシート: https://docs.google.com/spreadsheets/d/1LUE3KlT_J1lSgYmclg-ljiXDS4JYaAwEtc0X-ia-twU/edit?gid=1986572533#gid=1986572533

データマッピング:
- DateTime -> target_datetime
- Phone Count -> actual_score.score
- Location -> place.name
"""

import csv
import logging
import os
from typing import Any, Dict, List

import psycopg2
import requests
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SpreadsheetDataFetcher:
    def __init__(self) -> None:
        """スプレッドシートデータ取得クラス"""
        # 環境変数からスプレッドシートIDとGIDを取得
        sheet_id = os.getenv(
            "SPREADSHEET_ID", "1LUE3KlT_J1lSgYmclg-ljiXDS4JYaAwEtc0X-ia-twU"
        )
        gid = os.getenv("SPREADSHEET_GID", "1986572533")
        self.spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
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

    def fetch_spreadsheet_data(self) -> List[Dict[str, Any]]:
        """スプレッドシートからデータを取得"""
        try:
            logger.info(f"スプレッドシートからデータを取得中: {self.spreadsheet_url}")
            response = requests.get(self.spreadsheet_url, timeout=30)
            response.raise_for_status()

            # CSVデータをパース
            csv_data = response.content.decode("utf-8")
            reader = csv.DictReader(csv_data.splitlines())

            data = []
            for row in reader:
                if (
                    row.get("DateTime")
                    and row.get("Phone Count")
                    and row.get("Location")
                ):
                    data.append(
                        {
                            "datetime": row["DateTime"],
                            "phone_count": int(row["Phone Count"]),
                            "location": row["Location"],
                        }
                    )

            logger.info(f"取得データ数: {len(data)}")
            return data

        except Exception as e:
            logger.error(f"スプレッドシートデータ取得エラー: {e}")
            raise

    def get_or_create_place(
        self, conn: psycopg2.extensions.connection, location_name: str
    ) -> int:
        """場所を取得または作成"""
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 既存の場所を確認
            cursor.execute("SELECT id FROM place WHERE name = %s", (location_name,))
            result = cursor.fetchone()

            if result:
                return int(result["id"])

            # 新しい場所を作成
            cursor.execute(
                "INSERT INTO place (name) VALUES (%s) RETURNING id", (location_name,)
            )
            result = cursor.fetchone()
            if result is None:
                raise ValueError("Failed to create place")
            return int(result["id"])

    def insert_actual_score(
        self,
        conn: psycopg2.extensions.connection,
        place_id: int,
        datetime_str: str,
        score: int,
    ) -> None:
        """実測スコアデータを挿入"""
        with conn.cursor() as cursor:
            # 既存データの確認
            cursor.execute(
                "SELECT id FROM actual_score WHERE place_id = %s AND target_datetime = %s",
                (place_id, datetime_str),
            )
            if cursor.fetchone():
                logger.debug(f"既存データをスキップ: {datetime_str}, {score}")
                return

            # 新しいデータを挿入
            cursor.execute(
                "INSERT INTO actual_score (score, place_id, target_datetime) VALUES (%s, %s, %s)",
                (score, place_id, datetime_str),
            )
            logger.debug(f"データ挿入: {datetime_str}, {score}")

    def clear_existing_data(self, conn: Any) -> None:
        """既存データを消去"""
        try:
            with conn.cursor() as cursor:
                logger.info("既存データを消去中...")
                
                # 外部キー制約を考慮して順序良く削除
                cursor.execute("DELETE FROM predicted_score")
                cursor.execute("DELETE FROM actual_score")
                cursor.execute("DELETE FROM prediction_model")
                cursor.execute("DELETE FROM sensor")
                cursor.execute("DELETE FROM place")
                cursor.execute("DELETE FROM weather")
                
                logger.info("既存データの消去が完了しました")
                
        except Exception as e:
            logger.error(f"既存データ消去エラー: {e}")
            raise

    def process_and_insert_data(self, clear_data: bool = False) -> None:
        """データを処理してデータベースに挿入"""
        try:
            # スプレッドシートからデータを取得
            spreadsheet_data = self.fetch_spreadsheet_data()

            if not spreadsheet_data:
                logger.warning("取得データが空です")
                return

            # データベースに接続
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = False

            try:
                # 必要に応じて既存データを消去
                if clear_data:
                    self.clear_existing_data(conn)
                
                inserted_count = 0

                for data_row in spreadsheet_data:
                    # 場所IDを取得または作成
                    place_id = self.get_or_create_place(conn, data_row["location"])

                    # 実測スコアを挿入
                    self.insert_actual_score(
                        conn, place_id, data_row["datetime"], data_row["phone_count"]
                    )
                    inserted_count += 1

                conn.commit()
                logger.info(f"データベース挿入完了: {inserted_count} 件")

            except Exception as e:
                conn.rollback()
                logger.error(f"データベース処理エラー: {e}")
                raise

            finally:
                conn.close()

        except Exception as e:
            logger.error(f"データ処理エラー: {e}")
            raise


def main() -> None:
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="スプレッドシートデータ取得ツール")
    parser.add_argument("--clear", action="store_true", help="既存データを消去してから挿入")
    
    args = parser.parse_args()
    
    try:
        fetcher = SpreadsheetDataFetcher()
        fetcher.process_and_insert_data(clear_data=args.clear)
        logger.info("スプレッドシートデータの取得・挿入が完了しました")

    except Exception as e:
        logger.error(f"実行エラー: {e}")
        exit(1)


if __name__ == "__main__":
    main()
