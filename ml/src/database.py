"""
データベース接続とモデル定義
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.pool import NullPool

from config import config

logger = logging.getLogger(__name__)

# データベース接続設定
DATABASE_URL = config.DATABASE_URL


def get_engine(for_test: bool = False) -> Any:
    """エンジンを取得（テスト用/本番用の切り替え対応）"""
    import os

    if for_test or os.getenv("TEST_DATABASE_URL"):
        test_url = os.getenv("TEST_DATABASE_URL", "sqlite:///test.db")
        return create_engine(test_url, echo=False)
    else:
        return create_engine(
            DATABASE_URL,
            poolclass=NullPool,  # コネクションプーリングを無効化（長時間接続対策）
            echo=False,
        )


# SQLAlchemyエンジンの作成
engine = get_engine()

# セッションファクトリの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session_local(for_test: bool = False) -> Any:
    """セッションローカルを取得（テスト用/本番用の切り替え対応）"""
    import os

    if for_test or os.getenv("TEST_DATABASE_URL"):
        test_engine = get_engine(for_test=True)
        return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    return SessionLocal


# ベースクラスの作成
Base = declarative_base()


class Place(Base):  # type: ignore
    """場所情報テーブル"""

    __tablename__ = "place"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())

    # リレーション
    sensors = relationship("Sensor", back_populates="place")
    actual_scores = relationship("ActualScore", back_populates="place")
    predicted_scores = relationship("PredictedScore", back_populates="place")


class Sensor(Base):  # type: ignore
    """センサー情報テーブル"""

    __tablename__ = "sensor"

    id = Column(Integer, primary_key=True)
    place_id = Column(Integer, ForeignKey("place.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())

    # リレーション
    place = relationship("Place", back_populates="sensors")
    prediction_models = relationship("PredictionModel", back_populates="sensor")


class PredictionModel(Base):  # type: ignore
    """予測モデルテーブル"""

    __tablename__ = "prediction_model"

    id = Column(Integer, primary_key=True)
    sensor_id = Column(Integer, ForeignKey("sensor.id"), nullable=False)
    model_params = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, default=func.now())

    # リレーション
    sensor = relationship("Sensor", back_populates="prediction_models")
    predicted_scores = relationship("PredictedScore", back_populates="model")


class ActualScore(Base):  # type: ignore
    """実測混雑度テーブル"""

    __tablename__ = "actual_score"

    id = Column(Integer, primary_key=True)
    score = Column(Integer, nullable=False)
    place_id = Column(Integer, ForeignKey("place.id"), nullable=False)
    target_datetime = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())

    # リレーション
    place = relationship("Place", back_populates="actual_scores")


class PredictedScore(Base):  # type: ignore
    """予測混雑度テーブル"""

    __tablename__ = "predicted_score"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("prediction_model.id"), nullable=False)
    score = Column(Integer, nullable=False)
    place_id = Column(Integer, ForeignKey("place.id"), nullable=False)
    target_datetime = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())

    # リレーション
    model = relationship("PredictionModel", back_populates="predicted_scores")
    place = relationship("Place", back_populates="predicted_scores")


class Weather(Base):  # type: ignore
    """天気情報テーブル"""

    __tablename__ = "weather"

    id = Column(Integer, primary_key=True)
    datetime = Column(TIMESTAMP, nullable=False)
    weather = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())


@contextmanager
def get_db() -> Generator[Session]:
    """データベースセッションのコンテキストマネージャー"""
    import os

    if os.getenv("TEST_DATABASE_URL"):
        session_local = get_session_local(for_test=True)
        db = session_local()
    else:
        db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseManager:
    """データベース操作を管理するクラス"""

    @staticmethod
    def get_all_places(db: Session) -> list[Place]:
        """全ての場所情報を取得"""
        return db.query(Place).all()

    @staticmethod
    def get_actual_scores(
        db: Session,
        place_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ActualScore]:
        """実測スコアを取得"""
        query = db.query(ActualScore)

        if place_id:
            query = query.filter(ActualScore.place_id == place_id)
        if start_date:
            query = query.filter(ActualScore.target_datetime >= start_date)
        if end_date:
            query = query.filter(ActualScore.target_datetime <= end_date)

        return query.order_by(ActualScore.target_datetime).all()

    @staticmethod
    def save_prediction_model(
        db: Session, sensor_id: int, model_params: dict[str, Any]
    ) -> PredictionModel:
        """予測モデルを保存"""
        model = PredictionModel(sensor_id=sensor_id, model_params=model_params)
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def save_predictions(
        db: Session, predictions: list[dict[str, Any]]
    ) -> list[PredictedScore]:
        """予測結果を保存"""
        predicted_scores = []
        for pred in predictions:
            score = PredictedScore(
                model_id=pred["model_id"],
                score=pred["score"],
                place_id=pred["place_id"],
                target_datetime=pred["target_datetime"],
            )
            db.add(score)
            predicted_scores.append(score)

        db.commit()
        return predicted_scores

    @staticmethod
    def get_latest_model(db: Session, sensor_id: int) -> PredictionModel | None:
        """最新のモデルを取得"""
        return (
            db.query(PredictionModel)
            .filter(PredictionModel.sensor_id == sensor_id)
            .order_by(PredictionModel.created_at.desc())
            .first()
        )

    @staticmethod
    def delete_old_predictions(db: Session, before_date: datetime) -> int:
        """古い予測データを削除"""
        deleted = (
            db.query(PredictedScore)
            .filter(PredictedScore.target_datetime < before_date)
            .delete()
        )
        db.commit()
        return deleted

    @staticmethod
    def get_database_status(db: Session, prefix: str = "") -> dict[str, Any]:
        """データベースの状態を取得"""

        from sqlalchemy import text

        status: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "prefix": prefix,
            "tables": {}
        }

        # 各テーブルのレコード数を取得
        tables = ["place", "sensor", "prediction_model", "actual_score", "predicted_score", "weather"]

        for table in tables:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                status["tables"][table] = int(result) if result is not None else 0
            except Exception as e:
                status["tables"][table] = f"ERROR: {str(e)}"

        # 最新のデータ情報
        try:
            latest_actual = db.execute(text(
                "SELECT target_datetime FROM actual_score ORDER BY target_datetime DESC LIMIT 1"
            )).scalar()
            status["latest_actual_data"] = latest_actual.isoformat() if latest_actual else None
        except Exception:
            status["latest_actual_data"] = None

        try:
            latest_prediction = db.execute(text(
                "SELECT target_datetime FROM predicted_score ORDER BY target_datetime DESC LIMIT 1"
            )).scalar()
            status["latest_prediction_data"] = latest_prediction.isoformat() if latest_prediction else None
        except Exception:
            status["latest_prediction_data"] = None

        return status

    @staticmethod
    def save_database_status(db: Session, status: dict[str, Any], filepath: str) -> None:
        """データベース状態をファイルに保存"""
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
