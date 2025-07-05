"""
定期的なモデル更新スケジューラー
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from config import config

from .database import DatabaseManager, get_db
from .model import CongestionPredictionModel

logger = logging.getLogger(__name__)


class ModelScheduler:
    """モデル更新スケジューラー"""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.model = CongestionPredictionModel()
        self.db_manager = DatabaseManager()
        self.is_running = False

    async def start(self, test_mode: bool = False) -> None:
        """スケジューラーを開始"""
        if self.is_running:
            logger.warning("スケジューラーは既に実行中です")
            return

        if test_mode:
            # テストモード：短い間隔で実行
            logger.info("テストモードでスケジューラーを開始")

            # 2分ごとにモデルを再訓練（テスト用）
            self.scheduler.add_job(
                self._daily_retrain,
                CronTrigger(minute="*/2"),
                id="test_retrain",
                name="Test Model Retraining (Every 2 minutes)",
                replace_existing=True,
            )

            # 1分ごとに予測を実行（テスト用）
            self.scheduler.add_job(
                self._generate_predictions,
                CronTrigger(minute="*"),
                id="test_prediction",
                name="Test Prediction Generation (Every 1 minute)",
                replace_existing=True,
            )
        else:
            # 本番モード：要件通りの間隔
            logger.info("本番モードでスケジューラーを開始")

            # 毎日指定時刻にモデルを再訓練
            self.scheduler.add_job(
                self._daily_retrain,
                CronTrigger(hour=config.MODEL_RETRAIN_HOUR, minute=0),
                id="daily_retrain",
                name="Daily Model Retraining",
                replace_existing=True,
            )

            # 指定間隔で予測を実行
            self.scheduler.add_job(
                self._generate_predictions,
                CronTrigger(minute=f"*/{config.PREDICTION_INTERVAL_MINUTES}"),
                id="prediction_generation",
                name="Prediction Generation",
                replace_existing=True,
            )

        # 古い予測データを削除（1時間ごと）
        self.scheduler.add_job(
            self._cleanup_old_predictions,
            CronTrigger(minute=0),
            id="cleanup_predictions",
            name="Cleanup Old Predictions",
            replace_existing=True,
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("スケジューラーを開始しました")

    async def stop(self) -> None:
        """スケジューラーを停止"""
        if not self.is_running:
            return

        self.scheduler.shutdown()
        self.is_running = False
        logger.info("スケジューラーを停止しました")

    async def _daily_retrain(self) -> None:
        """毎日のモデル再訓練"""
        try:
            logger.info("定期的なモデル再訓練を開始")

            with get_db() as db:
                results = self.model.train(db=db, test_size=0.2)

            logger.info(f"モデル再訓練完了: {results['trained_models']}個のモデル")

            # 訓練結果をログに記録
            for place_id, result in results.get("results", {}).items():
                logger.info(
                    f"場所ID {place_id}: "
                    f"MAE={result['test_mae']:.2f}, "
                    f"RMSE={result['test_rmse']:.2f}, "
                    f"R2={result['test_r2']:.3f}"
                )

        except Exception as e:
            logger.error(f"定期的なモデル再訓練でエラー: {str(e)}")

    async def _generate_predictions(self) -> None:
        """予測データの生成"""
        try:
            logger.info("予測データの生成を開始")

            with get_db() as db:
                # 全場所を取得
                places = self.db_manager.get_all_places(db)

                # 現在時刻から24時間先まで予測
                now = datetime.now()
                total_predictions = 0

                for place in places:
                    try:
                        # 予測実行
                        predictions = self.model.predict(
                            db=db,
                            place_id=int(place.id),
                            target_datetime=now,
                            hours_ahead=24,
                        )

                        # 予測結果をデータベースに保存
                        if predictions:
                            # 最新のモデルIDを取得
                            latest_model = self.db_manager.get_latest_model(
                                db, int(place.id)
                            )
                            if latest_model:
                                prediction_data = []
                                for pred in predictions:
                                    prediction_data.append(
                                        {
                                            "model_id": latest_model.id,
                                            "score": pred["predicted_score"],
                                            "place_id": int(place.id),
                                            "target_datetime": datetime.fromisoformat(
                                                pred["target_datetime"]
                                            ),
                                        }
                                    )

                                # 既存の予測データを削除（同じ時間帯）
                                self._cleanup_duplicate_predictions(
                                    db, int(place.id), now
                                )

                                # 新しい予測データを保存
                                self.db_manager.save_predictions(db, prediction_data)
                                total_predictions += len(predictions)

                    except Exception as e:
                        logger.error(f"場所ID {place.id} の予測生成でエラー: {str(e)}")
                        continue

                logger.info(f"予測データ生成完了: {total_predictions}件")

        except Exception as e:
            logger.error(f"予測データ生成でエラー: {str(e)}")

    def _cleanup_duplicate_predictions(
        self, db: Session, place_id: int, base_datetime: datetime
    ) -> None:
        """重複する予測データを削除"""
        from .database import PredictedScore

        # 既存の予測データを削除（同じ場所、同じ時間帯）
        deleted = (
            db.query(PredictedScore)
            .filter(PredictedScore.place_id == place_id)
            .filter(PredictedScore.target_datetime >= base_datetime)
            .delete()
        )

        if deleted > 0:
            logger.info(f"場所ID {place_id} の重複予測データ {deleted}件を削除")

        db.commit()

    async def _cleanup_old_predictions(self) -> None:
        """古い予測データのクリーンアップ"""
        try:
            logger.info("古い予測データのクリーンアップを開始")

            # 24時間前より古いデータを削除
            cutoff_time = datetime.now() - timedelta(hours=24)

            with get_db() as db:
                deleted = self.db_manager.delete_old_predictions(db, cutoff_time)

            logger.info(f"古い予測データ {deleted}件を削除")

        except Exception as e:
            logger.error(f"予測データクリーンアップでエラー: {str(e)}")

    def get_status(self) -> dict[str, Any]:
        """スケジューラーの状態を取得"""
        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append(
                    {
                        "id": job.id,
                        "name": job.name,
                        "next_run": job.next_run_time.isoformat()
                        if job.next_run_time
                        else None,
                    }
                )

        return {"is_running": self.is_running, "jobs": jobs, "total_jobs": len(jobs)}


# グローバルインスタンス
scheduler = ModelScheduler()


async def start_scheduler() -> None:
    """スケジューラーを開始する関数"""
    await scheduler.start()


async def stop_scheduler() -> None:
    """スケジューラーを停止する関数"""
    await scheduler.stop()


def get_scheduler_status() -> dict[str, Any]:
    """スケジューラーの状態を取得する関数"""
    return scheduler.get_status()
