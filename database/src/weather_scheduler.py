#!/usr/bin/env python3
"""
天気データ取得スケジューラー
定期的に天気データを取得してデータベースに保存する
作成日: 2025-07-03
"""

import argparse
import logging
import os
import signal
import sys
import time
from typing import Optional
from types import FrameType

sys.path.append(os.path.dirname(__file__))
from weather_fetcher import WeatherFetcher

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("weather_scheduler.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class WeatherScheduler:
    def __init__(self) -> None:
        """天気データ取得スケジューラー"""
        self.running = False
        self.weather_fetcher = WeatherFetcher()

    def run_once(self) -> None:
        """1回の天気データ取得サイクルを実行"""
        logger.info("天気データ取得サイクルを開始")

        try:
            success = self.weather_fetcher.fetch_and_save_weather()
            if success:
                logger.info("天気データ取得サイクル完了")
            else:
                logger.error("天気データ取得サイクル失敗")
        except Exception as e:
            logger.error(f"天気データ取得エラー: {e}")

    def start(self, interval_minutes: int = 60) -> None:
        """スケジューラーを開始"""
        self.running = True
        interval_seconds = interval_minutes * 60

        logger.info(f"天気データスケジューラーを開始 (間隔: {interval_minutes}分)")

        try:
            while self.running:
                start_time = time.time()

                # 天気データ取得サイクルを実行
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

    def stop(self) -> None:
        """スケジューラーを停止"""
        self.running = False
        logger.info("天気データスケジューラーを停止しました")


def signal_handler(signum: int, frame: Optional[FrameType]) -> None:
    """シグナルハンドラー"""
    logger.info(f"シグナル {signum} を受信。プログラムを終了します")
    sys.exit(0)


def main() -> None:
    """メイン関数"""
    # シグナルハンドラーの設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # スケジューラーの初期化
    scheduler = WeatherScheduler()

    # 引数処理
    parser = argparse.ArgumentParser(description="天気データ取得スケジューラー")
    parser.add_argument("--interval", type=int, default=60, help="取得間隔（分）")
    parser.add_argument("--once", action="store_true", help="1回だけ実行")

    args = parser.parse_args()

    try:
        if args.once:
            logger.info("1回だけ天気データ取得を実行します")
            scheduler.run_once()
        else:
            scheduler.start(args.interval)
    except Exception as e:
        logger.error(f"実行エラー: {e}")
        exit(1)


if __name__ == "__main__":
    main()
