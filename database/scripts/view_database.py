#!/usr/bin/env python3
"""
データベース内容表示スクリプト
作成日: 2025-06-25
"""

import os
import sys
from datetime import datetime
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor


class DatabaseViewer:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password'),
            'database': os.getenv('POSTGRES_DB', 'congestion_watch')
        }
    
    def get_connection(self):
        """データベース接続を取得"""
        return psycopg2.connect(**self.db_config)
    
    def show_table_counts(self):
        """各テーブルのレコード数を表示"""
        print("=" * 60)
        print("データベーステーブル一覧とレコード数")
        print("=" * 60)
        
        tables = [
            'place', 'sensor', 'prediction_model', 'actual_predictions_date',
            'actual_score', 'predicted_score', 'actual_predictions', 'weather_data'
        ]
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"{table:25} : {count:>10} 件")
            
        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def show_places(self):
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
                    print(f"{place['id']:>3} | {place['name']:20} | {place['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("データがありません")
                
        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def show_sensors(self):
        """センサー一覧を表示"""
        print("\n" + "=" * 60)
        print("センサー一覧")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT s.id, s.name, p.name as place_name, s.created_at
                FROM sensor s
                JOIN place p ON s.place_id = p.id
                ORDER BY s.id
            """)
            sensors = cursor.fetchall()
            
            if sensors:
                print(f"{'ID':>3} | {'センサー名':25} | {'場所':15} | {'作成日時':19}")
                print("-" * 70)
                for sensor in sensors:
                    print(f"{sensor['id']:>3} | {sensor['name']:25} | {sensor['place_name']:15} | {sensor['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("データがありません")
                
        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def show_recent_scores(self, limit: int = 20):
        """最近の実測スコアを表示"""
        print(f"\n" + "=" * 60)
        print(f"最近の実測スコア（最新{limit}件）")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    as_.id,
                    as_.score,
                    apd.date,
                    as_.created_at
                FROM actual_score as_
                JOIN actual_predictions_date apd ON as_.measured_date_id = apd.id
                ORDER BY as_.created_at DESC
                LIMIT %s
            """, (limit,))
            
            scores = cursor.fetchall()
            
            if scores:
                print(f"{'ID':>3} | {'スコア':>6} | {'測定日':12} | {'作成日時':19}")
                print("-" * 50)
                for score in scores:
                    print(f"{score['id']:>3} | {score['score']:>6} | {score['date']} | {score['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("データがありません")
                
        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def show_date_range(self):
        """データの日付範囲を表示"""
        print("\n" + "=" * 60)
        print("データ期間")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT 
                    MIN(date) as min_date,
                    MAX(date) as max_date,
                    COUNT(*) as date_count
                FROM actual_predictions_date
            """)
            
            date_info = cursor.fetchone()
            
            if date_info and date_info['min_date']:
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
                    print(f"\n実測データ統計:")
                    print(f"  総レコード数: {stats['total_records']} 件")
                    print(f"  最小スコア: {stats['min_score']}")
                    print(f"  最大スコア: {stats['max_score']}")
                    print(f"  平均スコア: {stats['avg_score']}")
            else:
                print("日付データがありません")
                
        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def show_hourly_stats(self, date: Optional[str] = None):
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
                cursor.execute("""
                    SELECT 
                        EXTRACT(HOUR FROM as_.created_at) as hour,
                        COUNT(*) as count,
                        ROUND(AVG(as_.score), 2) as avg_score,
                        MIN(as_.score) as min_score,
                        MAX(as_.score) as max_score
                    FROM actual_score as_
                    JOIN actual_predictions_date apd ON as_.measured_date_id = apd.id
                    WHERE apd.date = %s
                    GROUP BY EXTRACT(HOUR FROM as_.created_at)
                    ORDER BY hour
                """, (date,))
            else:
                cursor.execute("""
                    SELECT 
                        EXTRACT(HOUR FROM as_.created_at) as hour,
                        COUNT(*) as count,
                        ROUND(AVG(as_.score), 2) as avg_score,
                        MIN(as_.score) as min_score,
                        MAX(as_.score) as max_score
                    FROM actual_score as_
                    GROUP BY EXTRACT(HOUR FROM as_.created_at)
                    ORDER BY hour
                """)
            
            stats = cursor.fetchall()
            
            if stats:
                print(f"{'時間':>4} | {'件数':>6} | {'平均':>8} | {'最小':>6} | {'最大':>6}")
                print("-" * 40)
                for stat in stats:
                    hour = int(stat['hour']) if stat['hour'] else 0
                    print(f"{hour:>4} | {stat['count']:>6} | {stat['avg_score']:>8} | {stat['min_score']:>6} | {stat['max_score']:>6}")
            else:
                print("データがありません")
                
        except Exception as e:
            print(f"エラー: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def show_all(self):
        """すべての情報を表示"""
        self.show_table_counts()
        self.show_places()
        self.show_sensors()
        self.show_date_range()
        self.show_recent_scores()
        self.show_hourly_stats()


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='データベース内容表示ツール')
    parser.add_argument('--tables', action='store_true', help='テーブル一覧とレコード数を表示')
    parser.add_argument('--places', action='store_true', help='場所一覧を表示')
    parser.add_argument('--sensors', action='store_true', help='センサー一覧を表示')
    parser.add_argument('--scores', type=int, default=20, help='最近のスコアを表示（件数指定）')
    parser.add_argument('--stats', action='store_true', help='統計情報を表示')
    parser.add_argument('--hourly', action='store_true', help='時間別統計を表示')
    parser.add_argument('--date', type=str, help='特定日の統計（YYYY-MM-DD形式）')
    parser.add_argument('--all', action='store_true', help='すべての情報を表示')
    
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
            if not any([args.tables, args.places, args.sensors, args.stats, args.scores, args.hourly]):
                viewer.show_table_counts()
                viewer.show_recent_scores(10)
                
    except KeyboardInterrupt:
        print("\n処理を中断しました")
    except Exception as e:
        print(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()