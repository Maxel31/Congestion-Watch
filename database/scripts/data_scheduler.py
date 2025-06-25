#!/usr/bin/env python3
"""
5分間隔データ取得スケジューラー
作成日: 2025-06-25
"""

import os
import csv
import json
import time
import signal
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Set
import requests
import psycopg2
from psycopg2.extras import RealDictCursor


# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataScheduler:
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        self.csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        self.running = False
        self.processed_timestamps: Set[float] = set()
        
        # DB接続設定
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password'),
            'database': os.getenv('POSTGRES_DB', 'congestion_watch')
        }
        
        # 既存データの読み込み
        self._load_existing_timestamps()
    
    def _load_existing_timestamps(self):
        """データベースから既存のタイムスタンプを読み込み"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 実際には、actual_scoreテーブルの作成日時から推測
            cursor.execute("""
                SELECT DISTINCT 
                    EXTRACT(EPOCH FROM created_at) as timestamp
                FROM actual_score
            """)
            
            results = cursor.fetchall()
            for row in results:
                if row['timestamp']:
                    self.processed_timestamps.add(float(row['timestamp']))
            
            logger.info(f"既存のタイムスタンプ {len(self.processed_timestamps)} 件を読み込みました")
            
        except Exception as e:
            logger.warning(f"既存タイムスタンプの読み込みに失敗: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def fetch_sheet_data(self) -> List[Dict[str, Any]]:
        """スプレッドシートからデータを取得"""
        try:
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()
            
            lines = response.text.strip().split('\n')
            reader = csv.DictReader(lines)
            
            data = []
            for row in reader:
                # タイムスタンプから日付を変換
                if 'Timestamp' in row and row['Timestamp']:
                    try:
                        timestamp = float(row['Timestamp'])
                        dt = datetime.fromtimestamp(timestamp)
                        
                        row['parsed_datetime'] = dt
                        row['date'] = dt.date()
                        row['time'] = dt.time()
                        row['timestamp'] = timestamp
                        
                        # 数値データの変換
                        row['phone_count'] = int(row['Phone Count']) if row['Phone Count'] else 0
                        row['device_count'] = int(row['Total Device Count']) if row['Total Device Count'] else 0
                        
                        data.append(row)
                        
                    except (ValueError, TypeError):
                        continue
            
            logger.info(f"スプレッドシートから {len(data)} 件のデータを取得")
            return data
            
        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            return []
    
    def find_new_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """新しいデータのみを抽出"""
        new_data = []
        for row in data:
            if 'timestamp' in row and row['timestamp'] not in self.processed_timestamps:
                new_data.append(row)
        
        logger.info(f"新しいデータ {len(new_data)} 件を検出")
        return new_data
    
    def get_db_connection(self):
        """データベース接続を取得"""
        return psycopg2.connect(**self.db_config)
    
    def ensure_place_and_sensor(self, cursor) -> tuple:
        """場所とセンサーのIDを確保"""
        place_name = "南館食堂"
        sensor_name = "デバイス検出センサー"
        
        # 場所の確保
        cursor.execute("SELECT id FROM place WHERE name = %s", (place_name,))
        place_result = cursor.fetchone()
        
        if not place_result:
            cursor.execute("INSERT INTO place (name) VALUES (%s) RETURNING id", (place_name,))
            place_id = cursor.fetchone()['id']
        else:
            place_id = place_result['id']
        
        # センサーの確保
        cursor.execute("SELECT id FROM sensor WHERE place_id = %s AND name = %s", (place_id, sensor_name))
        sensor_result = cursor.fetchone()
        
        if not sensor_result:
            cursor.execute("INSERT INTO sensor (place_id, name) VALUES (%s, %s) RETURNING id", (place_id, sensor_name))
            sensor_id = cursor.fetchone()['id']
        else:
            sensor_id = sensor_result['id']
        
        return place_id, sensor_id
    
    def insert_new_data(self, new_data: List[Dict[str, Any]]) -> bool:
        """新しいデータをデータベースに挿入"""
        if not new_data:
            return True
        
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            place_id, sensor_id = self.ensure_place_and_sensor(cursor)
            
            inserted_count = 0
            
            for row in new_data:
                if 'date' not in row or 'phone_count' not in row:
                    continue
                
                # 日付データを確保
                cursor.execute(
                    "INSERT INTO actual_predictions_date (date) VALUES (%s) ON CONFLICT (date) DO NOTHING RETURNING id",
                    (row['date'],)
                )
                result = cursor.fetchone()
                
                if result:
                    date_id = result['id']
                else:
                    cursor.execute("SELECT id FROM actual_predictions_date WHERE date = %s", (row['date'],))
                    date_id = cursor.fetchone()['id']
                
                # 実測スコア挿入（重複チェック付き）
                cursor.execute("""
                    INSERT INTO actual_score (score, measured_date_id, created_at) 
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (row['phone_count'], date_id, row['parsed_datetime']))
                
                # 処理済みタイムスタンプに追加
                self.processed_timestamps.add(row['timestamp'])
                inserted_count += 1
            
            conn.commit()
            logger.info(f"データベースに {inserted_count} 件の新しいデータを挿入")
            return True
            
        except Exception as e:
            logger.error(f"データベース挿入エラー: {e}")
            if 'conn' in locals():
                conn.rollback()
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def run_once(self):
        """1回のデータ取得・処理サイクルを実行"""
        logger.info("データ取得サイクルを開始")
        
        # データ取得
        data = self.fetch_sheet_data()
        if not data:
            logger.warning("データを取得できませんでした")
            return
        
        # 新しいデータの検出
        new_data = self.find_new_data(data)
        
        # 新しいデータの挿入
        if new_data:
            success = self.insert_new_data(new_data)
            if success:
                logger.info(f"データ処理サイクル完了: {len(new_data)} 件追加")
            else:
                logger.error("データ処理サイクル失敗")
        else:
            logger.info("新しいデータはありませんでした")
    
    def start(self, interval_minutes: int = 5):
        """スケジューラーを開始"""
        self.running = True
        interval_seconds = interval_minutes * 60
        
        logger.info(f"データスケジューラーを開始 (間隔: {interval_minutes}分)")
        
        try:
            while self.running:
                start_time = time.time()
                
                # データ処理サイクルを実行
                self.run_once()
                
                # 次の実行まで待機
                elapsed_time = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed_time)
                
                if sleep_time > 0:
                    logger.info(f"次の実行まで {sleep_time:.1f} 秒待機")
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Ctrl+Cが押されました。スケジューラーを停止します")
        except Exception as e:
            logger.error(f"スケジューラーエラー: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """スケジューラーを停止"""
        self.running = False
        logger.info("データスケジューラーを停止しました")


def signal_handler(signum, frame):
    """シグナルハンドラー"""
    logger.info(f"シグナル {signum} を受信。プログラムを終了します")
    sys.exit(0)


def main():
    """メイン関数"""
    # シグナルハンドラーの設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # スプレッドシートID
    sheet_id = "1LUE3KlT_J1lSgYmclg-ljiXDS4JYaAwEtc0X-ia-twU"
    
    # スケジューラーの初期化と開始
    scheduler = DataScheduler(sheet_id)
    
    # 引数処理
    import argparse
    parser = argparse.ArgumentParser(description='混雑度データ取得スケジューラー')
    parser.add_argument('--interval', type=int, default=5, help='取得間隔（分）')
    parser.add_argument('--once', action='store_true', help='1回だけ実行')
    
    args = parser.parse_args()
    
    if args.once:
        logger.info("1回だけデータ取得を実行します")
        scheduler.run_once()
    else:
        scheduler.start(args.interval)


if __name__ == "__main__":
    main()