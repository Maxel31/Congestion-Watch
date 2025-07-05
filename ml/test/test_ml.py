"""
ML機能の基本テスト
"""

import pytest
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from typing import Any

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# テスト用の環境変数設定
from config import config  # noqa: E402

os.environ["DATABASE_URL"] = config.TEST_DATABASE_URL  # noqa: E402

from main import app  # noqa: E402
from src.model import CongestionPredictionModel  # noqa: E402
from src.feature_engineering import FeatureEngineer  # noqa: E402
from src.database import DatabaseManager  # noqa: E402


class TestMLService:
    """MLサービスのテストクラス"""

    def setup_method(self) -> None:
        """テストメソッドの前処理"""
        self.client = TestClient(app)

    def test_root_endpoint(self) -> None:
        """ルートエンドポイントのテスト"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert data["service"] == "Congestion Watch ML Service"

    def test_health_check(self) -> None:
        """ヘルスチェックエンドポイントのテスト"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    @patch("src.model.CongestionPredictionModel.predict")
    @patch("src.database.get_db")
    def test_predict_endpoint(self, mock_get_db: Any, mock_predict: Any) -> None:
        """予測エンドポイントのテスト"""
        # モックの設定
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_predict.return_value = [
            {
                "place_id": 1,
                "target_datetime": "2024-01-01T12:00:00",
                "predicted_score": 50,
                "confidence": 0.85,
            }
        ]

        # リクエストの実行
        response = self.client.post(
            "/predict",
            json={
                "place_id": 1,
                "target_datetime": "2024-01-01T12:00:00",
                "hours_ahead": 24,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert data["place_id"] == 1
        assert data["total_predictions"] == 1

    @patch("src.model.CongestionPredictionModel.train")
    @patch("src.database.get_db")
    def test_train_endpoint(self, mock_get_db: Any, mock_train: Any) -> None:
        """訓練エンドポイントのテスト"""
        # モックの設定
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_train.return_value = {
            "status": "success",
            "trained_models": 2,
            "results": {
                "1": {"place_name": "test_place", "test_mae": 5.0},
                "2": {"place_name": "test_place2", "test_mae": 3.0},
            },
        }

        # リクエストの実行
        response = self.client.post("/train", json={"test_size": 0.2})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["trained_models"] == 2

    def test_scheduler_status(self) -> None:
        """スケジューラー状態エンドポイントのテスト"""
        response = self.client.get("/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "is_running" in data
        assert "jobs" in data


class TestFeatureEngineer:
    """特徴量エンジニアリングのテストクラス"""

    def setup_method(self) -> None:
        """テストメソッドの前処理"""
        self.mock_db = MagicMock()
        self.feature_engineer = FeatureEngineer(self.mock_db)

    def test_handle_missing_values(self) -> None:
        """欠損値処理のテスト"""
        # テストデータの準備
        df = pd.DataFrame(
            {
                "feature1": [1, 2, np.nan, 4],
                "feature2": [np.nan, 2, 3, 4],
                "feature3": ["a", "b", "c", "d"],
            }
        )

        # 欠損値処理の実行
        result = self.feature_engineer._handle_missing_values(df)

        # 結果の確認
        assert result["feature1"].iloc[2] == -1  # 欠損値が-1に置換
        assert result["feature2"].iloc[0] == -1  # 欠損値が-1に置換
        assert result["feature3"].iloc[0] == "a"  # 文字列は変更されない

    def test_create_features_basic(self) -> None:
        """基本的な特徴量作成のテスト"""
        # テストデータの準備
        current = pd.Series(
            {"place_id": 1, "target_datetime": datetime(2024, 1, 1, 12, 0), "score": 50}
        )

        past_data = pd.DataFrame(
            {
                "target_datetime": [
                    datetime(2024, 1, 1, 11, 0),
                    datetime(2024, 1, 1, 10, 0),
                ],
                "score": [40, 30],
                "place_id": [1, 1],
            }
        )

        all_data = pd.DataFrame(
            {
                "target_datetime": [
                    datetime(2024, 1, 1, 11, 0),
                    datetime(2024, 1, 1, 10, 0),
                    datetime(2024, 1, 1, 11, 30),
                    datetime(2024, 1, 1, 10, 30),
                ],
                "score": [40, 30, 35, 25],
                "place_id": [1, 1, 2, 2],
            }
        )
        place_ids = [1, 2]

        # 特徴量作成の実行
        features = self.feature_engineer._create_features(
            current, past_data, all_data, place_ids
        )

        # 結果の確認
        assert "place_id" in features
        assert "hour" in features
        assert "minute" in features
        assert "day_of_week" in features
        assert features["place_id"] == 1
        assert features["hour"] == 12
        assert features["minute"] == 0
        assert features["day_of_week"] == 0  # 月曜日


class TestCongestionPredictionModel:
    """混雑度予測モデルのテストクラス"""

    def setup_method(self) -> None:
        """テストメソッドの前処理"""
        self.model = CongestionPredictionModel(model_dir="test_models")

    def test_model_initialization(self) -> None:
        """モデル初期化のテスト"""
        assert self.model.model_dir.name == "test_models"
        assert self.model.models == {}
        assert self.model.feature_columns is None
        assert "n_estimators" in self.model.model_params

    def test_calculate_confidence(self) -> None:
        """信頼度計算のテスト"""
        # モックモデルの作成
        mock_model = MagicMock()
        mock_estimator1 = MagicMock()
        mock_estimator2 = MagicMock()
        mock_estimator1.predict.return_value = [45.0]
        mock_estimator2.predict.return_value = [55.0]
        mock_model.estimators_ = [mock_estimator1, mock_estimator2]

        # テストデータの準備
        X = pd.DataFrame({"feature1": [1]})

        # 信頼度計算の実行
        confidence = self.model._calculate_confidence(mock_model, X)

        # 結果の確認
        assert 0 <= confidence <= 1
        assert isinstance(confidence, float)

    @patch("src.model.CongestionPredictionModel._save_models")
    @patch("src.model.CongestionPredictionModel._save_model_info_to_db")
    def test_train_with_mock_data(
        self, mock_save_db: Any, mock_save_models: Any
    ) -> None:
        """モックデータでの訓練テスト"""
        # モックデータベースの設定
        mock_db = MagicMock()

        # モック場所データ
        mock_place = MagicMock()
        mock_place.id = 1
        mock_place.name = "Test Place"

        # モック特徴量エンジニアリング
        with patch("src.model.FeatureEngineer") as mock_fe:
            mock_fe_instance = mock_fe.return_value
            mock_fe_instance.prepare_training_data.return_value = (
                pd.DataFrame(
                    {"feature1": [1, 2, 3, 4, 5], "feature2": [2, 3, 4, 5, 6]}
                ),
                pd.Series([10, 20, 30, 40, 50]),
            )

            # モックデータベースマネージャー
            with patch("src.model.DatabaseManager") as mock_dm:
                mock_dm_instance = mock_dm.return_value
                mock_dm_instance.get_all_places.return_value = [mock_place]

                # 訓練の実行
                result = self.model.train(mock_db, test_size=0.2)

                # 結果の確認
                assert result["status"] == "success"
                assert result["trained_models"] >= 0
                assert "results" in result


class TestDatabaseManager:
    """データベースマネージャーのテストクラス"""

    def test_database_manager_initialization(self) -> None:
        """データベースマネージャーの初期化テスト"""
        manager = DatabaseManager()
        assert manager is not None

    def test_get_all_places_mock(self) -> None:
        """全場所取得のモックテスト"""
        mock_db = MagicMock()
        mock_place = MagicMock()
        mock_place.id = 1
        mock_place.name = "Test Place"
        mock_db.query.return_value.all.return_value = [mock_place]

        manager = DatabaseManager()
        places = manager.get_all_places(mock_db)

        assert len(places) == 1
        assert places[0].name == "Test Place"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
