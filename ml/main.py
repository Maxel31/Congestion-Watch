"""
機械学習サービスのエントリーポイント
"""

import argparse
import logging
from datetime import datetime

from config import config
from src.database import get_db
from src.model import CongestionPredictionModel

# ロギング設定
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def train_models() -> None:
    """モデル訓練を実行"""
    logger.info("モデル訓練を開始します...")
    model = CongestionPredictionModel()
    with get_db() as db:
        result = model.train(db)
        logger.info(f"訓練完了: {result}")


def predict_models() -> None:
    """予測を実行"""
    logger.info("予測を開始します...")
    model = CongestionPredictionModel()
    with get_db() as db:
        # 実測データがある場所のみを対象とする
        from sqlalchemy import text

        # 実測データが存在する場所IDを取得
        actual_places = db.execute(
            text("SELECT DISTINCT place_id FROM actual_score ORDER BY place_id")
        ).fetchall()

        for place_row in actual_places:
            place_id = place_row[0]
            try:
                predictions = model.predict(
                    db=db,
                    place_id=place_id,
                    target_datetime=datetime.now(),
                    hours_ahead=24,
                )
                logger.info(f"場所 {place_id} の予測完了: {len(predictions)} 件")
            except Exception as e:
                logger.error(f"場所 {place_id} の予測エラー: {e}")


def main() -> None:
    """メイン関数"""
    parser = argparse.ArgumentParser(description="機械学習サービス")
    parser.add_argument("--train", action="store_true", help="モデルを訓練する")
    parser.add_argument("--predict", action="store_true", help="予測を実行する")
    parser.add_argument(
        "--server", action="store_true", help="サーバーモード（現在は非対応）"
    )

    args = parser.parse_args()

    if args.train:
        train_models()
    elif args.predict:
        predict_models()
    elif args.server:
        logger.info("MLサービスをサーバーモードで起動しました（バッチ処理待機中）")
        logger.info("使用方法:")
        logger.info("  docker exec <container> uv run python main.py --train")
        logger.info("  docker exec <container> uv run python main.py --predict")

        # コンテナを起動状態に保つ
        import time

        try:
            while True:
                time.sleep(60)  # 1分間隔でスリープ
                logger.debug("MLサービス待機中...")
        except KeyboardInterrupt:
            logger.info("MLサービスを終了します")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
