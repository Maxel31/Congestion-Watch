#!/usr/bin/env python3
"""
スプレッドシートデータ取得スクリプト
作成日: 2025-06-25
"""

import os
import csv
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs
import psycopg2
from psycopg2.extras import RealDictCursor


def extract_sheet_id(url: str) -> str:
    """Google SheetsのURLからシートIDを抽出"""
    if '/spreadsheets/d/' in url:
        return url.split('/spreadsheets/d/')[1].split('/')[0]
    raise ValueError("無効なGoogle Sheets URL")


def fetch_sheet_data(sheet_id: str) -> List[Dict[str, Any]]:
    """
    Google SheetsからCSVデータを取得
    
    Args:
        sheet_id: Google SheetsのID
        
    Returns:
        List[Dict]: 取得したデータのリスト
    """
    # CSV形式でエクスポート
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        
        # CSVデータを解析
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
                except (ValueError, TypeError):
                    continue
            
            # 数値データの変換
            if 'Phone Count' in row:
                try:
                    row['phone_count'] = int(row['Phone Count']) if row['Phone Count'] else 0
                except ValueError:
                    row['phone_count'] = 0
                    
            if 'Total Device Count' in row:
                try:
                    row['device_count'] = int(row['Total Device Count']) if row['Total Device Count'] else 0
                except ValueError:
                    row['device_count'] = 0
            
            data.append(row)
        
        return data
        
    except requests.RequestException as e:
        print(f"データ取得エラー: {e}")
        return []


def get_db_connection():
    """データベース接続を取得"""
    config = {
        'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),  # IPv4アドレスを明示的に指定
        'port': int(os.getenv('POSTGRES_PORT', '5432')),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password'),
        'database': os.getenv('POSTGRES_DB', 'congestion_watch')
    }
    
    return psycopg2.connect(**config)


def insert_data_to_db(data: List[Dict[str, Any]]) -> bool:
    """
    取得したデータをデータベースに挿入
    
    Args:
        data: 挿入するデータのリスト
        
    Returns:
        bool: 成功時True
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 場所データを確認・挿入
        place_name = "南館食堂"
        cursor.execute("SELECT id FROM place WHERE name = %s", (place_name,))
        place_result = cursor.fetchone()
        
        if not place_result:
            cursor.execute("INSERT INTO place (name) VALUES (%s) RETURNING id", (place_name,))
            place_id = cursor.fetchone()['id']
        else:
            place_id = place_result['id']
        
        # センサーデータを確認・挿入
        sensor_name = "デバイス検出センサー"
        cursor.execute("SELECT id FROM sensor WHERE place_id = %s AND name = %s", (place_id, sensor_name))
        sensor_result = cursor.fetchone()
        
        if not sensor_result:
            cursor.execute("INSERT INTO sensor (place_id, name) VALUES (%s, %s) RETURNING id", (place_id, sensor_name))
            sensor_id = cursor.fetchone()['id']
        else:
            sensor_id = sensor_result['id']
        
        # データを日付ごとに処理
        for row in data:
            if 'date' not in row or 'phone_count' not in row:
                continue
                
            # 日付データを確認・挿入
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
            
            # 実測スコアを挿入（電話数をスコアとして使用）
            cursor.execute(
                "INSERT INTO actual_score (score, measured_date_id) VALUES (%s, %s)",
                (row['phone_count'], date_id)
            )
        
        conn.commit()
        print(f"データベースに {len(data)} 件のデータを挿入しました")
        return True
        
    except Exception as e:
        print(f"データベース挿入エラー: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()


def main():
    """メイン関数"""
    # スプレッドシートURL
    sheet_url = "https://docs.google.com/spreadsheets/d/1LUE3KlT_J1lSgYmclg-ljiXDS4JYaAwEtc0X-ia-twU/edit?usp=sharing"
    
    try:
        # シートIDを抽出
        sheet_id = extract_sheet_id(sheet_url)
        print(f"シートID: {sheet_id}")
        
        # データを取得
        print("スプレッドシートからデータを取得中...")
        data = fetch_sheet_data(sheet_id)
        
        if not data:
            print("データを取得できませんでした")
            return False
        
        print(f"{len(data)} 件のデータを取得しました")
        
        # データをデータベースに挿入
        print("データベースに挿入中...")
        success = insert_data_to_db(data)
        
        if success:
            print("データ取得・挿入が完了しました！")
            return True
        else:
            print("データ挿入に失敗しました")
            return False
            
    except Exception as e:
        print(f"エラー: {e}")
        return False


if __name__ == "__main__":
    main()