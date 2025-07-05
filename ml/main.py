"""
機械学習サービスのエントリーポイント
"""

import logging
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import config
from src.database import get_db
from src.model import CongestionPredictionModel
from src.scheduler import get_scheduler_status, start_scheduler, stop_scheduler

# ロギング設定
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="Congestion Watch ML Service",
    description="混雑度予測機械学習サービス",
    version="1.0.0",
)


class PredictionRequest(BaseModel):
    """予測リクエストモデル"""

    place_id: int
    target_datetime: str
    hours_ahead: int = 24


class PredictionResponse(BaseModel):
    """予測レスポンスモデル"""

    place_id: int
    predictions: list[dict[str, Any]]
    model_version: str
    total_predictions: int


class TrainingRequest(BaseModel):
    """訓練リクエストモデル"""

    test_size: float = 0.2


class TrainingResponse(BaseModel):
    """訓練レスポンスモデル"""

    status: str
    trained_models: int
    results: dict[str, Any]


@app.get("/")
async def root() -> dict[str, str]:
    """ルートエンドポイント"""
    return {
        "service": "Congestion Watch ML Service",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected",  # TODO: 実際のDB接続確認を実装
        "models_loaded": True,  # TODO: モデルロード状態を確認
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """混雑度予測エンドポイント"""
    try:
        logger.info(
            f"Prediction request: place_id={request.place_id}, datetime={request.target_datetime}"
        )

        # 日時文字列をパース
        target_datetime = datetime.fromisoformat(
            request.target_datetime.replace("Z", "+00:00")
        )

        # 予測モデルを初期化
        model = CongestionPredictionModel()

        # 予測実行
        with get_db() as db:
            predictions = model.predict(
                db=db,
                place_id=request.place_id,
                target_datetime=target_datetime,
                hours_ahead=request.hours_ahead,
            )

        return PredictionResponse(
            place_id=request.place_id,
            predictions=predictions,
            model_version="v1.0.0",
            total_predictions=len(predictions),
        )

    except Exception as e:
        logger.error(f"予測エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"予測エラー: {str(e)}") from e


@app.post("/train", response_model=TrainingResponse)
async def train_model(request: TrainingRequest) -> TrainingResponse:
    """モデル訓練エンドポイント"""
    try:
        logger.info("Model training started")

        # 予測モデルを初期化
        model = CongestionPredictionModel()

        # 訓練実行
        with get_db() as db:
            results = model.train(db=db, test_size=request.test_size)

        return TrainingResponse(
            status=results["status"],
            trained_models=results["trained_models"],
            results=results["results"],
        )

    except Exception as e:
        logger.error(f"訓練エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=f"訓練エラー: {str(e)}") from e


@app.get("/scheduler/status")
async def get_scheduler_status_endpoint() -> dict[str, Any]:
    """スケジューラーの状態を取得"""
    return get_scheduler_status()


@app.post("/scheduler/start")
async def start_scheduler_endpoint() -> dict[str, str]:
    """スケジューラーを開始"""
    try:
        await start_scheduler()
        return {"status": "started", "message": "スケジューラーを開始しました"}
    except Exception as e:
        logger.error(f"スケジューラー開始エラー: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"スケジューラー開始エラー: {str(e)}"
        ) from e


@app.post("/scheduler/stop")
async def stop_scheduler_endpoint() -> dict[str, str]:
    """スケジューラーを停止"""
    try:
        await stop_scheduler()
        return {"status": "stopped", "message": "スケジューラーを停止しました"}
    except Exception as e:
        logger.error(f"スケジューラー停止エラー: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"スケジューラー停止エラー: {str(e)}"
        ) from e


@app.on_event("startup")
async def startup_event() -> None:
    """アプリケーション起動時の処理"""
    logger.info("MLサービスを起動しています...")

    # 自動的にスケジューラーを開始
    if config.AUTO_START_SCHEDULER:
        try:
            await start_scheduler()
            logger.info("スケジューラーを自動開始しました")
        except Exception as e:
            logger.error(f"スケジューラー自動開始エラー: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """アプリケーション終了時の処理"""
    logger.info("MLサービスを終了しています...")

    try:
        await stop_scheduler()
        logger.info("スケジューラーを停止しました")
    except Exception as e:
        logger.error(f"スケジューラー停止エラー: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0", port=config.ML_PORT, reload=config.is_development()
    )
