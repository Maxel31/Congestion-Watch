#!/bin/bash
# Docker内でスケジューラーを実行するスクリプト
# 作成日: 2025-06-25

set -e

echo "Docker内でPythonスケジューラーを実行します..."

# Pythonスクリプトをコンテナにコピーして実行
docker-compose exec postgres bash -c "
apt-get update && apt-get install -y python3 python3-pip
pip3 install requests psycopg2-binary

cat > /tmp/run_scheduler.py << 'EOF'
import os
import csv
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# スプレッドシートからデータを取得
sheet_id = '1LUE3KlT_J1lSgYmclg-ljiXDS4JYaAwEtc0X-ia-twU'
csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

print('スプレッドシートからデータを取得中...')
response = requests.get(csv_url)
lines = response.text.strip().split('\n')
reader = csv.DictReader(lines)

data = []
for row in reader:
    if 'Timestamp' in row and row['Timestamp']:
        try:
            timestamp = float(row['Timestamp'])
            dt = datetime.fromtimestamp(timestamp)
            row['parsed_datetime'] = dt
            row['date'] = dt.date()
            row['phone_count'] = int(row['Phone Count']) if row['Phone Count'] else 0
            data.append(row)
        except:
            continue

print(f'取得したデータ: {len(data)} 件')

# データベースに挿入
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='password',
    database='congestion_watch'
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# 場所を確保
cursor.execute(\"SELECT id FROM place WHERE name = '南館食堂'\")
place_result = cursor.fetchone()
if not place_result:
    cursor.execute(\"INSERT INTO place (name) VALUES ('南館食堂') RETURNING id\")
    place_id = cursor.fetchone()['id']
else:
    place_id = place_result['id']

# センサーを確保
cursor.execute(\"SELECT id FROM sensor WHERE place_id = %s AND name = 'デバイス検出センサー'\", (place_id,))
sensor_result = cursor.fetchone()
if not sensor_result:
    cursor.execute(\"INSERT INTO sensor (place_id, name) VALUES (%s, 'デバイス検出センサー') RETURNING id\", (place_id,))
    sensor_id = cursor.fetchone()['id']
else:
    sensor_id = sensor_result['id']

# データを挿入
inserted = 0
for row in data:
    if 'date' not in row:
        continue
    
    # 日付を確保
    cursor.execute(\"INSERT INTO actual_predictions_date (date) VALUES (%s) ON CONFLICT (date) DO NOTHING RETURNING id\", (row['date'],))
    result = cursor.fetchone()
    if result:
        date_id = result['id']
    else:
        cursor.execute(\"SELECT id FROM actual_predictions_date WHERE date = %s\", (row['date'],))
        date_id = cursor.fetchone()['id']
    
    # スコアを挿入
    cursor.execute(\"INSERT INTO actual_score (score, measured_date_id, created_at) VALUES (%s, %s, %s)\", 
                   (row['phone_count'], date_id, row['parsed_datetime']))
    inserted += 1

conn.commit()
print(f'データベースに {inserted} 件のデータを挿入しました')

# データ確認
cursor.execute(\"SELECT COUNT(*) as count FROM actual_score\")
count = cursor.fetchone()['count']
print(f'total records in actual_score: {count}')

conn.close()
EOF

python3 /tmp/run_scheduler.py
"