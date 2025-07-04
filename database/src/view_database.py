#!/usr/bin/env python3
"""
データベース内容表示スクリプト
作成日: 2025-06-25
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import RealDictCursor


def load_env_file() -> None:
    """
    .envファイルから環境変数を読み込む
    """
    # プロジェクトルートの.envファイルを探す
    current_dir = Path(__file__).parent
    env_file = current_dir.parent.parent / ".env"
    
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    # 環境変数を上書きして最新の.envファイルの値を使用
                    os.environ[key] = value


class DatabaseViewer:
    def __init__(self) -> None:
        # .envファイルを読み込み
        load_env_file()
        
        self.db_config: Dict[str, Any] = {
            "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "congestion_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "secure_password"),
            "database": os.getenv("POSTGRES_DB", "congestion_watch"),
        }

    def get_connection(self) -> Any:
        """データベース接続を取得"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.OperationalError as e:
            print(f"データベース接続エラー: {e}")
            print(f"接続設定: user={self.db_config['user']}, host={self.db_config['host']}, db={self.db_config['database']}")
            raise

    def show_table_counts(self) -> None:
        """各テーブルのレコード数を表示"""
        print("=" * 60)
        print("データベーステーブル一覧とレコード数")
        print("=" * 60)

        tables = [
            "place",
            "sensor",
            "prediction_model",
            "actual_score",
            "predicted_score",
            "weather",
        ]

        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                count = result["count"] if result else 0
                print(f"{table:25} : {count:>10} 件")

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    def show_places(self) -> None:
        """場所一覧を表示"""
        print("\n" + "=" * 60)
        print("場所一覧")
        print("=" * 60)

        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT * FROM place ORDER BY id")
            places = cursor.fetchall()

            if places:
                print(f"{'ID':>3} | {'場所名':20} | {'作成日時':19}")
                print("-" * 50)
                for place in places:
                    print(
                        f"{place['id']:>3} | {place['name']:20} | {place['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                    )
            else:
                print("データがありません")

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    def show_sensors(self) -> None:
        """センサー一覧を表示"""
        print("\n" + "=" * 60)
        print("センサー一覧")
        print("=" * 60)

        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT s.id, p.name as place_name, s.created_at
                FROM sensor s
                JOIN place p ON s.place_id = p.id
                ORDER BY s.id
            """)
            sensors = cursor.fetchall()

            if sensors:
                print(f"{'ID':>3} | {'場所':15} | {'作成日時':19}")
                print("-" * 45)
                for sensor in sensors:
                    print(
                        f"{sensor['id']:>3} | {sensor['place_name']:15} | {sensor['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                    )
            else:
                print("データがありません")

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    def show_recent_scores(self, limit: int = 20) -> None:
        """最近の実測スコアを表示"""
        print("\n" + "=" * 60)
        print(f"最近の実測スコア（最新{limit}件）")
        print("=" * 60)

        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute(
                """
                SELECT 
                    as_.id,
                    as_.score,
                    as_.target_datetime,
                    as_.created_at,
                    p.name as place_name
                FROM actual_score as_
                JOIN place p ON as_.place_id = p.id
                ORDER BY as_.created_at DESC
                LIMIT %s
            """,
                (limit,),
            )

            scores = cursor.fetchall()

            if scores:
                print(
                    f"{'ID':>3} | {'スコア':>6} | {'測定日時':19} | {'場所':15} | {'作成日時':19}"
                )
                print("-" * 75)
                for score in scores:
                    print(
                        f"{score['id']:>3} | {score['score']:>6} | {score['target_datetime'].strftime('%Y-%m-%d %H:%M:%S')} | {score['place_name']:15} | {score['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                    )
            else:
                print("データがありません")

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    def show_date_range(self) -> None:
        """データの日付範囲を表示"""
        print("\n" + "=" * 60)
        print("データ期間")
        print("=" * 60)

        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT 
                    MIN(target_datetime) as min_date,
                    MAX(target_datetime) as max_date,
                    COUNT(DISTINCT DATE(target_datetime)) as date_count
                FROM actual_score
            """)

            date_info = cursor.fetchone()

            if date_info and date_info["min_date"]:
                print(f"開始日: {date_info['min_date']}")
                print(f"終了日: {date_info['max_date']}")
                print(f"期間日数: {date_info['date_count']} 日")

                # 実測データの統計
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        MIN(score) as min_score,
                        MAX(score) as max_score,
                        ROUND(AVG(score), 2) as avg_score
                    FROM actual_score
                """)

                stats = cursor.fetchone()
                if stats:
                    print("\n実測データ統計:")
                    print(f"  総レコード数: {stats['total_records']} 件")
                    print(f"  最小スコア: {stats['min_score']}")
                    print(f"  最大スコア: {stats['max_score']}")
                    print(f"  平均スコア: {stats['avg_score']}")
            else:
                print("日付データがありません")

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    def show_hourly_stats(self, date: Optional[str] = None) -> None:
        """時間別統計を表示"""
        print("\n" + "=" * 60)
        if date:
            print(f"{date} の時間別統計")
        else:
            print("全期間の時間別統計")
        print("=" * 60)

        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if date:
                cursor.execute(
                    """
                    SELECT 
                        EXTRACT(HOUR FROM as_.target_datetime) as hour,
                        COUNT(*) as count,
                        ROUND(AVG(as_.score), 2) as avg_score,
                        MIN(as_.score) as min_score,
                        MAX(as_.score) as max_score
                    FROM actual_score as_
                    WHERE DATE(as_.target_datetime) = %s
                    GROUP BY EXTRACT(HOUR FROM as_.target_datetime)
                    ORDER BY hour
                """,
                    (date,),
                )
            else:
                cursor.execute("""
                    SELECT 
                        EXTRACT(HOUR FROM as_.target_datetime) as hour,
                        COUNT(*) as count,
                        ROUND(AVG(as_.score), 2) as avg_score,
                        MIN(as_.score) as min_score,
                        MAX(as_.score) as max_score
                    FROM actual_score as_
                    GROUP BY EXTRACT(HOUR FROM as_.target_datetime)
                    ORDER BY hour
                """)

            stats = cursor.fetchall()

            if stats:
                print(
                    f"{'時間':>4} | {'件数':>6} | {'平均':>8} | {'最小':>6} | {'最大':>6}"
                )
                print("-" * 40)
                for stat in stats:
                    hour = int(stat["hour"]) if stat["hour"] else 0
                    print(
                        f"{hour:>4} | {stat['count']:>6} | {stat['avg_score']:>8} | {stat['min_score']:>6} | {stat['max_score']:>6}"
                    )
            else:
                print("データがありません")

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if "conn" in locals():
                conn.close()

    def show_all(self) -> None:
        """すべての情報を表示"""
        self.show_table_counts()
        self.show_places()
        self.show_sensors()
        self.show_date_range()
        self.show_recent_scores()
        self.show_hourly_stats()


def main() -> None:
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="データベース内容表示ツール")
    parser.add_argument(
        "--tables", action="store_true", help="テーブル一覧とレコード数を表示"
    )
    parser.add_argument("--places", action="store_true", help="場所一覧を表示")
    parser.add_argument("--sensors", action="store_true", help="センサー一覧を表示")
    parser.add_argument(
        "--scores", type=int, default=20, help="最近のスコアを表示（件数指定）"
    )
    parser.add_argument("--stats", action="store_true", help="統計情報を表示")
    parser.add_argument("--hourly", action="store_true", help="時間別統計を表示")
    parser.add_argument("--date", type=str, help="特定日の統計（YYYY-MM-DD形式）")
    parser.add_argument("--all", action="store_true", help="すべての情報を表示")

    args = parser.parse_args()

    viewer = DatabaseViewer()

    try:
        if args.all:
            viewer.show_all()
        else:
            if args.tables:
                viewer.show_table_counts()
            if args.places:
                viewer.show_places()
            if args.sensors:
                viewer.show_sensors()
            if args.stats:
                viewer.show_date_range()
            if args.scores:
                viewer.show_recent_scores(args.scores)
            if args.hourly:
                viewer.show_hourly_stats(args.date)

            # 何も指定されていない場合はデフォルト表示
            if not any(
                [
                    args.tables,
                    args.places,
                    args.sensors,
                    args.stats,
                    args.scores,
                    args.hourly,
                ]
            ):
                viewer.show_table_counts()
                viewer.show_recent_scores(10)

    except KeyboardInterrupt:
        print("\n処理を中断しました")
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
