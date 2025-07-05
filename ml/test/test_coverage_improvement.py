"""
カバレッジ向上のための追加テスト
"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typing import Any
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# テスト用の環境変数設定
from config import config  # noqa: E402

os.environ["DATABASE_URL"] = config.TEST_DATABASE_URL  # noqa: E402

from src.feature_engineering import FeatureEngineer  # noqa: E402
from src.model import CongestionPredictionModel  # noqa: E402
from src.scheduler import (  # noqa: E402
    ModelScheduler,
    start_scheduler,
    stop_scheduler,
    get_scheduler_status,
)
from src.database import DatabaseManager  # noqa: E402


class TestFeatureEngineeringCoverage:
    """特徴量エンジニアリングの詳細テスト"""

    def setup_method(self) -> None:
        """テストメソッドの前処理"""
        self.mock_db = MagicMock()
        self.feature_engineer = FeatureEngineer(self.mock_db)

    def test_prepare_training_data_with_data(self) -> None:
        """実際のデータありでの訓練データ準備テスト"""
        # モックデータベースマネージャーの設定
        mock_db_manager = MagicMock()
        self.feature_engineer.db_manager = mock_db_manager

        # モック場所データ
        mock_place = MagicMock()
        mock_place.id = 1
        mock_db_manager.get_all_places.return_value = [mock_place]

        # モック実測データ
        mock_actual_scores = [
            MagicMock(
                place_id=1, target_datetime=datetime(2024, 1, 1, 12, 0), score=50
            ),
            MagicMock(
                place_id=1, target_datetime=datetime(2024, 1, 1, 12, 5), score=45
            ),
            MagicMock(
                place_id=1, target_datetime=datetime(2024, 1, 1, 12, 10), score=55
            ),
        ]
        mock_db_manager.get_actual_scores.return_value = mock_actual_scores

        # 訓練データの準備を実行
        X, y = self.feature_engineer.prepare_training_data(place_id=1)

        # 結果の確認
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)

    def test_prepare_training_data_no_data(self) -> None:
        """データなしでの訓練データ準備テスト"""
        mock_db_manager = MagicMock()
        self.feature_engineer.db_manager = mock_db_manager

        # 空の場所データ
        mock_db_manager.get_all_places.return_value = []
        mock_db_manager.get_actual_scores.return_value = []

        X, y = self.feature_engineer.prepare_training_data()

        assert len(X) == 0
        assert len(y) == 0

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
        assert result["feature1"].iloc[2] == -1
        assert result["feature2"].iloc[0] == -1
        assert result["feature3"].iloc[0] == "a"

    def test_create_features_empty_past_data(self) -> None:
        """過去データなしでの特徴量作成テスト"""
        current = pd.Series(
            {"place_id": 1, "target_datetime": datetime(2024, 1, 1, 12, 0), "score": 50}
        )

        past_data = pd.DataFrame()
        all_data = pd.DataFrame()
        place_ids = [1, 2]

        features = self.feature_engineer._create_features(
            current, past_data, all_data, place_ids
        )

        assert features == {}


class TestCongestionPredictionModelCoverage:
    """混雑度予測モデルの詳細テスト"""

    def setup_method(self) -> None:
        """テストメソッドの前処理"""
        self.model = CongestionPredictionModel(model_dir="test_models")

    def test_predict_model_not_loaded(self) -> None:
        """モデル未ロード状態での予測テスト"""
        mock_db = MagicMock()

        # モデルが存在しない場合は空のリストを返す
        result = self.model.predict(
            db=mock_db, place_id=999, target_datetime=datetime.now()
        )

        assert result == []

    def test_load_models_no_files(self) -> None:
        """保存ファイル不存在でのモデルロードテスト"""
        # 存在しないディレクトリでモデルロードを試行
        test_model = CongestionPredictionModel(model_dir="nonexistent_dir")
        test_model._load_models()

        # エラーが発生しないことを確認
        assert len(test_model.models) == 0

    def test_calculate_confidence_edge_cases(self) -> None:
        """信頼度計算のエッジケーステスト"""
        # モックモデルの作成
        mock_model = MagicMock()
        mock_estimator = MagicMock()
        mock_estimator.predict.return_value = [50.0]
        mock_model.estimators_ = [mock_estimator]

        # テストデータの準備
        X = pd.DataFrame({"feature1": [1]})

        # 信頼度計算の実行
        confidence = self.model._calculate_confidence(mock_model, X)

        # 結果の確認
        assert 0 <= confidence <= 1
        assert isinstance(confidence, float)

    @patch("src.model.pickle.dump")
    @patch("src.model.json.dump")
    @patch("builtins.open")
    def test_save_models(
        self, mock_open: Any, mock_json_dump: Any, mock_pickle_dump: Any
    ) -> None:
        """モデル保存のテスト"""
        # テスト用のモデルを設定
        self.model.models = {1: MagicMock()}
        self.model.feature_columns = ["feature1", "feature2"]

        # モデル保存を実行
        self.model._save_models()

        # ファイル操作が正しく呼ばれることを確認
        assert mock_open.call_count >= 2
        mock_pickle_dump.assert_called_once()
        mock_json_dump.assert_called_once()


class TestModelSchedulerCoverage:
    """モデルスケジューラーの詳細テスト"""

    def setup_method(self) -> None:
        """テストメソッドの前処理"""
        self.scheduler = ModelScheduler()

    @pytest.mark.asyncio
    async def test_start_already_running(self) -> None:
        """既に実行中の状態でのスケジューラー開始テスト"""
        self.scheduler.is_running = True

        await self.scheduler.start()

        # 既に実行中の場合は何も起こらないことを確認
        assert self.scheduler.is_running is True

    @pytest.mark.asyncio
    async def test_stop_not_running(self) -> None:
        """実行していない状態でのスケジューラー停止テスト"""
        self.scheduler.is_running = False

        await self.scheduler.stop()

        # 実行していない場合は何も起こらないことを確認
        assert self.scheduler.is_running is False

    def test_get_status_not_running(self) -> None:
        """スケジューラー停止中の状態取得テスト"""
        self.scheduler.is_running = False

        status = self.scheduler.get_status()

        assert status["is_running"] is False
        assert status["jobs"] == []
        assert status["total_jobs"] == 0

    @pytest.mark.asyncio
    async def test_daily_retrain_error(self) -> None:
        """モデル再訓練でのエラーハンドリングテスト"""
        with patch.object(
            self.scheduler.model, "train", side_effect=Exception("Test error")
        ):
            # エラーが発生しても例外が外に漏れないことを確認
            await self.scheduler._daily_retrain()

    @pytest.mark.asyncio
    async def test_generate_predictions_error(self) -> None:
        """予測生成でのエラーハンドリングテスト"""
        with patch("src.scheduler.get_db", side_effect=Exception("Database error")):
            # エラーが発生しても例外が外に漏れないことを確認
            await self.scheduler._generate_predictions()

    @pytest.mark.asyncio
    async def test_cleanup_old_predictions_error(self) -> None:
        """古いデータクリーンアップでのエラーハンドリングテスト"""
        with patch("src.scheduler.get_db", side_effect=Exception("Database error")):
            # エラーが発生しても例外が外に漏れないことを確認
            await self.scheduler._cleanup_old_predictions()

    def test_cleanup_duplicate_predictions(self) -> None:
        """重複予測データクリーンアップのテスト"""
        mock_db = MagicMock()
        mock_query_result = MagicMock()
        mock_query_result.delete.return_value = 5
        mock_db.query.return_value.filter.return_value.filter.return_value = (
            mock_query_result
        )

        self.scheduler._cleanup_duplicate_predictions(mock_db, 1, datetime.now())

        # データベースクエリが実行されることを確認
        mock_db.query.assert_called()
        mock_db.commit.assert_called()


class TestSchedulerFunctions:
    """スケジューラー関数のテスト"""

    @pytest.mark.asyncio
    async def test_start_scheduler_function(self) -> None:
        """start_scheduler関数のテスト"""
        with patch("src.scheduler.scheduler.start") as mock_start:
            await start_scheduler()
            mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_scheduler_function(self) -> None:
        """stop_scheduler関数のテスト"""
        with patch("src.scheduler.scheduler.stop") as mock_stop:
            await stop_scheduler()
            mock_stop.assert_called_once()

    def test_get_scheduler_status_function(self) -> None:
        """get_scheduler_status関数のテスト"""
        with patch("src.scheduler.scheduler.get_status") as mock_get_status:
            mock_get_status.return_value = {"is_running": False}
            result = get_scheduler_status()
            mock_get_status.assert_called_once()
            assert result == {"is_running": False}


class TestDatabaseManagerCoverage:
    """データベースマネージャーの詳細テスト"""

    def test_get_actual_scores_with_filters(self) -> None:
        """フィルター付きでの実測スコア取得テスト"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)

        result = DatabaseManager.get_actual_scores(
            mock_db, place_id=1, start_date=start_date, end_date=end_date
        )

        # フィルターが正しく適用されることを確認
        assert mock_query.filter.call_count == 3  # place_id, start_date, end_date
        assert result == []

    def test_save_prediction_model(self) -> None:
        """予測モデル保存のテスト"""
        mock_db = MagicMock()
        mock_model = MagicMock()
        mock_model.id = 1

        with patch("src.database.PredictionModel", return_value=mock_model):
            result = DatabaseManager.save_prediction_model(
                mock_db, 1, {"param": "value"}
            )

        mock_db.add.assert_called_with(mock_model)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_with(mock_model)
        assert result == mock_model

    def test_save_predictions(self) -> None:
        """予測結果保存のテスト"""
        mock_db = MagicMock()

        predictions = [
            {
                "model_id": 1,
                "score": 50,
                "place_id": 1,
                "target_datetime": datetime.now(),
            }
        ]

        with patch("src.database.PredictedScore") as mock_predicted_score:
            mock_instance = MagicMock()
            mock_predicted_score.return_value = mock_instance

            result = DatabaseManager.save_predictions(mock_db, predictions)

        mock_db.add.assert_called_with(mock_instance)
        mock_db.commit.assert_called_once()
        assert len(result) == 1

    def test_get_latest_model(self) -> None:
        """最新モデル取得のテスト"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_model = MagicMock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_model

        result = DatabaseManager.get_latest_model(mock_db, 1)

        mock_db.query.assert_called()
        mock_query.filter.assert_called()
        mock_query.order_by.assert_called()
        mock_query.first.assert_called()
        assert result == mock_model

    def test_delete_old_predictions(self) -> None:
        """古い予測データ削除のテスト"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.delete.return_value = 10

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        result = DatabaseManager.delete_old_predictions(
            mock_db, datetime.now() - timedelta(days=1)
        )

        mock_db.query.assert_called()
        mock_query.filter.assert_called()
        mock_query.delete.assert_called()
        mock_db.commit.assert_called()
        assert result == 10


class TestFeatureEngineeringAdditional:
    """特徴量エンジニアリングの追加テスト"""

    def test_prepare_prediction_features(self) -> None:
        """予測用特徴量準備のテスト"""
        mock_db = MagicMock()
        feature_engineer = FeatureEngineer(mock_db)

        # モックデータベースマネージャーの設定
        mock_db_manager = MagicMock()
        feature_engineer.db_manager = mock_db_manager

        # モック場所データ
        mock_place = MagicMock()
        mock_place.id = 1
        mock_db_manager.get_all_places.return_value = [mock_place]

        # モック実測データ
        mock_actual_scores = [
            MagicMock(
                place_id=1, target_datetime=datetime(2024, 1, 1, 12, 0), score=50
            ),
        ]
        mock_db_manager.get_actual_scores.return_value = mock_actual_scores

        result = feature_engineer.prepare_prediction_features(
            place_id=1, target_datetime=datetime(2024, 1, 1, 13, 0)
        )

        assert isinstance(result, pd.DataFrame)


class TestModelAdditional:
    """モデルの追加テスト"""

    def test_train_insufficient_data(self) -> None:
        """不十分なデータでの訓練テスト"""
        model = CongestionPredictionModel(model_dir="test_models")
        mock_db = MagicMock()

        # モックデータベースマネージャー
        with patch("src.model.DatabaseManager") as mock_dm_class:
            mock_dm = mock_dm_class.return_value

            # モック場所データ
            mock_place = MagicMock()
            mock_place.id = 1
            mock_place.name = "Test Place"
            mock_dm.get_all_places.return_value = [mock_place]

            # モック特徴量エンジニアリング（不十分なデータ）
            with patch("src.model.FeatureEngineer") as mock_fe_class:
                mock_fe = mock_fe_class.return_value
                mock_fe.prepare_training_data.return_value = (
                    pd.DataFrame({"feature1": [1, 2]}),  # 2件のみ（<10）
                    pd.Series([10, 20]),
                )

                result = model.train(mock_db, test_size=0.2)

                assert result["status"] == "success"
                assert result["trained_models"] == 0  # データ不足でモデル作成されない

    def test_train_no_places(self) -> None:
        """場所データなしでの訓練テスト"""
        model = CongestionPredictionModel(model_dir="test_models")
        mock_db = MagicMock()

        with patch("src.model.DatabaseManager") as mock_dm_class:
            mock_dm = mock_dm_class.return_value
            mock_dm.get_all_places.return_value = []  # 場所データなし

            result = model.train(mock_db, test_size=0.2)

            assert result["status"] == "error"
            assert "場所データが存在しません" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
