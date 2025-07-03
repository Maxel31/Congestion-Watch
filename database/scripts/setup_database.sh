#!/bin/bash

# =============================================================================
# Database Setup Script for Congestion Watch
# =============================================================================
# このスクリプトは以下を自動実行します：
# 1. PostgreSQLコンテナの起動
# 2. データベースの初期化
# 3. マイグレーションの実行
# 4. 初期データの投入
# 5. スプレッドシートからの実データ取得
# =============================================================================

set -e  # エラーで停止

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログ関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# プロジェクトルートディレクトリの検出
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DATABASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

log_info "プロジェクトルート: $PROJECT_ROOT"
log_info "データベースディレクトリ: $DATABASE_DIR"

# 必要なファイルの存在確認
check_prerequisites() {
    log_info "前提条件をチェック中..."
    
    # Docker Composeファイルの確認
    if [ ! -f "$PROJECT_ROOT/compose.yaml" ]; then
        log_error "compose.yamlが見つかりません: $PROJECT_ROOT/compose.yaml"
        exit 1
    fi
    
    # 設定ファイルの確認
    if [ ! -f "$PROJECT_ROOT/config.env" ]; then
        log_error "config.envが見つかりません: $PROJECT_ROOT/config.env"
        exit 1
    fi
    
    # Docker の確認
    if ! command -v docker &> /dev/null; then
        log_error "Dockerがインストールされていません"
        exit 1
    fi
    
    # uv の確認（Pythonスクリプト用）
    if ! command -v uv &> /dev/null; then
        log_error "uvがインストールされていません"
        exit 1
    fi
    
    log_success "前提条件チェック完了"
}

# PostgreSQLコンテナの起動
start_postgresql() {
    log_info "PostgreSQLコンテナを起動中..."
    
    cd "$PROJECT_ROOT"
    
    # 既存のコンテナを停止
    docker-compose --env-file config.env down postgres 2>/dev/null || true
    
    # PostgreSQLコンテナを起動
    docker-compose --env-file config.env up -d postgres
    
    # コンテナの起動を待機
    log_info "PostgreSQLの起動を待機中..."
    sleep 10
    
    # ヘルスチェック
    for i in {1..30}; do
        if docker-compose --env-file config.env exec postgres pg_isready -U congestion_user &>/dev/null; then
            log_success "PostgreSQLが正常に起動しました"
            return 0
        fi
        log_info "PostgreSQLの起動を待機中... ($i/30)"
        sleep 2
    done
    
    log_error "PostgreSQLの起動がタイムアウトしました"
    exit 1
}

# マイグレーション実行
run_migrations() {
    log_info "マイグレーションを実行中..."
    
    cd "$SCRIPT_DIR"
    
    # 環境変数設定
    export POSTGRES_HOST=localhost
    export POSTGRES_PORT=5432
    export POSTGRES_USER=congestion_user
    export POSTGRES_PASSWORD=secure_password
    export POSTGRES_DB=congestion_watch_dev
    
    # 既存のスキーマをクリア（必要に応じて）
    ./migrate.sh down 2>/dev/null || true
    
    # マイグレーション実行
    ./migrate.sh up
    
    log_success "マイグレーション完了"
}

# 初期データ投入
insert_initial_data() {
    log_info "初期データを投入中..."
    
    # 初期データのSQL実行
    PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch_dev -f "$DATABASE_DIR/seeds/initial_data.sql"
    
    log_success "初期データ投入完了"
}

# スプレッドシートからのデータ取得
fetch_spreadsheet_data() {
    log_info "スプレッドシートからデータを取得中..."
    
    cd "$PROJECT_ROOT"
    
    # 環境変数設定
    export POSTGRES_HOST=localhost
    export POSTGRES_PORT=5432
    export POSTGRES_USER=congestion_user
    export POSTGRES_PASSWORD=secure_password
    export POSTGRES_DB=congestion_watch_dev
    
    # スプレッドシートデータ取得
    uv run --frozen python database/src/fetch_spreadsheet_data.py
    
    log_success "スプレッドシートデータ取得完了"
}

# データベース状態確認
verify_setup() {
    log_info "セットアップ結果を確認中..."
    
    # テーブル一覧表示
    echo ""
    log_info "=== テーブル一覧 ==="
    PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch_dev -c "\dt"
    
    # データ件数確認
    echo ""
    log_info "=== データ件数 ==="
    PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch_dev -c "
    SELECT 
      'actual_score' as table_name, COUNT(*) as records 
    FROM actual_score 
    UNION ALL 
    SELECT 'predicted_score', COUNT(*) FROM predicted_score 
    UNION ALL 
    SELECT 'place', COUNT(*) FROM place 
    UNION ALL 
    SELECT 'sensor', COUNT(*) FROM sensor 
    UNION ALL 
    SELECT 'prediction_model', COUNT(*) FROM prediction_model 
    UNION ALL 
    SELECT 'weather', COUNT(*) FROM weather 
    ORDER BY records DESC;"
    
    # 最新データサンプル表示
    echo ""
    log_info "=== 最新データサンプル ==="
    PGPASSWORD=secure_password psql -h localhost -U congestion_user -d congestion_watch_dev -c "
    SELECT 
      a.score, 
      a.target_datetime, 
      p.name 
    FROM actual_score a 
    JOIN place p ON a.place_id = p.id 
    ORDER BY a.target_datetime DESC 
    LIMIT 5;"
    
    echo ""
    log_success "データベースセットアップが完了しました！"
}

# メイン関数
main() {
    log_info "====================================================="
    log_info "Congestion Watch Database Setup Script"
    log_info "====================================================="
    echo ""
    
    check_prerequisites
    start_postgresql
    run_migrations
    insert_initial_data
    fetch_spreadsheet_data
    verify_setup
    
    echo ""
    log_success "====================================================="
    log_success "セットアップが正常に完了しました！"
    log_success "====================================================="
    echo ""
    log_info "1. データベース確認: uv run --frozen python database/src/view_database.py"
    log_info "2. スケジューラー起動: uv run --frozen python database/src/data_scheduler.py"
    log_info "3. バックエンド起動: docker-compose up backend"
    echo ""
}

# トラップでエラー処理
trap 'log_error "スクリプトがエラーで中断されました"; exit 1' ERR

# スクリプト実行
main "$@"