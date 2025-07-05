#!/usr/bin/env python3
"""
PostgreSQL統合テスト実行スクリプト
Docker Composeでpostgresサービスを起動してからテストを実行
"""

import logging
import subprocess
import sys
import time
from pathlib import Path

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_command(command: str, cwd: str | None = None) -> bool:
    """コマンドを実行して結果を返す"""
    try:
        result = subprocess.run(
            command.split(), cwd=cwd, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            logger.error(f"コマンド実行失敗: {command}")
            logger.error(f"エラー: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"コマンドタイムアウト: {command}")
        return False
    except Exception as e:
        logger.error(f"コマンド実行エラー: {command}, {str(e)}")
        return False


def check_postgres_health(max_retries: int = 30) -> bool:
    """PostgreSQLの起動を待機"""
    logger.info("PostgreSQLの起動を待機中...")

    for i in range(max_retries):
        try:
            result = subprocess.run(
                ["docker", "exec", "postgresql", "pg_isready", "-U", "postgres"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                logger.info("PostgreSQLが起動しました")
                return True

        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            logger.debug(f"接続確認エラー: {str(e)}")

        logger.info(f"待機中... ({i + 1}/{max_retries})")
        time.sleep(2)

    logger.error("PostgreSQLの起動に失敗しました")
    return False


def start_postgres_service() -> bool:
    """PostgreSQLサービスを起動"""
    logger.info("PostgreSQLサービス起動開始")

    # プロジェクトルートに移動
    project_root = Path(__file__).parent.parent

    # Docker Composeでpostgresサービスを起動
    if not run_command("docker-compose up -d postgres", cwd=str(project_root)):
        return False

    # PostgreSQLの起動を待機
    return check_postgres_health()


def run_integration_tests() -> bool:
    """統合テストを実行"""
    logger.info("統合テスト実行開始")

    # testディレクトリに移動してテストを実行
    test_dir = Path(__file__).parent

    try:
        # test_integration.pyを実行
        result = subprocess.run(
            [sys.executable, "test_integration.py"], cwd=str(test_dir), timeout=300
        )

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        logger.error("統合テストがタイムアウトしました")
        return False
    except Exception as e:
        logger.error(f"統合テスト実行エラー: {str(e)}")
        return False


def main() -> None:
    """メイン処理"""
    logger.info("=== PostgreSQL統合テスト自動実行 ===")

    try:
        # 1. PostgreSQLサービス起動
        if not start_postgres_service():
            logger.error("PostgreSQLサービスの起動に失敗しました")
            sys.exit(1)

        # 2. 統合テスト実行
        if not run_integration_tests():
            logger.error("統合テストに失敗しました")
            sys.exit(1)

        logger.info("=== すべてのテストが成功しました ===")

    except KeyboardInterrupt:
        logger.info("テストが中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
