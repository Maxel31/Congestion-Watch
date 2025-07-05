"""
混雑度予測モデル
"""

import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from config import config

from .database import DatabaseManager, Sensor
from .feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class CongestionPredictionModel:
    """混雑度予測モデル"""

    def __init__(self, model_dir: str | None = None):
        if model_dir is None:
            model_dir = config.MODEL_DIR
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)

        # 予測結果保存用ディレクトリを作成
        self.predictions_dir = self.model_dir / "predictions"
        self.predictions_dir.mkdir(exist_ok=True)

        self.models: dict[
            int, RandomForestRegressor
        ] = {}  # place_id -> model のマッピング
        self.feature_columns: list[str] | None = None
        self.model_params = {
            "n_estimators": 100,
            "max_depth": 20,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
            "random_state": 42,
            "n_jobs": -1,
        }

    def train(self, db: Session, test_size: float = 0.2) -> dict[str, Any]:
        """
        全場所のモデルを訓練

        Args:
            db: データベースセッション
            test_size: テストデータの割合

        Returns:
            訓練結果の辞書
        """
        logger.info("モデル訓練開始")

        db_manager = DatabaseManager()
        feature_engineer = FeatureEngineer(db)

        # 全場所を取得
        places = db_manager.get_all_places(db)

        if not places:
            logger.error("場所データが存在しません")
            return {"status": "error", "message": "場所データが存在しません"}

        results = {}

        # 各場所ごとにモデルを訓練
        for place in places:
            logger.info(f"場所 {place.name} (ID: {place.id}) のモデル訓練開始")

            # 訓練データの準備
            X, y = feature_engineer.prepare_training_data(place_id=int(place.id))

            if len(X) < 10:
                logger.warning(
                    f"場所 {place.name} の訓練データが不足しています: {len(X)}件"
                )
                continue

            # 特徴量カラムを保存
            if self.feature_columns is None:
                self.feature_columns = X.columns.tolist()

            # データ分割
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, shuffle=False
            )

            # モデル訓練
            model = RandomForestRegressor(**self.model_params)
            model.fit(X_train, y_train)

            # 評価
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)

            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
            test_r2 = r2_score(y_test, test_pred)

            # 特徴量重要度
            feature_importance = pd.DataFrame(
                {"feature": X.columns, "importance": model.feature_importances_}
            ).sort_values("importance", ascending=False)

            # モデルを保存
            self.models[int(place.id)] = model

            # 結果を記録
            results[int(place.id)] = {
                "place_name": place.name,
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "train_mae": float(train_mae),
                "test_mae": float(test_mae),
                "test_rmse": float(test_rmse),
                "test_r2": float(test_r2),
                "top_features": feature_importance.head(10).to_dict("records"),
            }

            logger.info(
                f"場所 {place.name} のモデル訓練完了 - "
                f"MAE: {test_mae:.2f}, RMSE: {test_rmse:.2f}, R2: {test_r2:.3f}"
            )

        # モデルをファイルに保存
        self._save_models()

        # データベースにモデル情報を保存
        self._save_model_info_to_db(
            db, db_manager, {int(k): v for k, v in results.items()}
        )

        # 学習結果をファイルに保存
        train_result = {
            "status": "success",
            "trained_models": len(self.models),
            "results": results,
        }
        self._save_training_results_to_file(train_result)

        return train_result

    def predict(
        self,
        db: Session,
        place_id: int,
        target_datetime: datetime,
        hours_ahead: int = 24,
    ) -> list[dict[str, Any]]:
        """
        指定場所の混雑度を予測

        Args:
            db: データベースセッション
            place_id: 予測対象の場所ID
            target_datetime: 予測開始時刻
            hours_ahead: 予測時間（時間）

        Returns:
            予測結果のリスト
        """
        # モデルが存在しない場合はロード
        if place_id not in self.models:
            self._load_models()

        if place_id not in self.models:
            logger.error(f"場所ID {place_id} のモデルが存在しません")
            return []

        feature_engineer = FeatureEngineer(db)

        # 予測用特徴量の準備
        X_pred = feature_engineer.prepare_prediction_features(
            place_id=place_id,
            target_datetime=target_datetime,
            prediction_hours=hours_ahead,
        )

        if len(X_pred) == 0:
            logger.warning("予測用特徴量を作成できませんでした")
            return []

        # 予測時間を保存（特徴量から除外される前に）
        prediction_times = X_pred["prediction_datetime"].tolist()

        # 特徴量の順序を合わせる（prediction_datetimeは除外）
        if self.feature_columns:
            # prediction_datetimeカラムを除外して特徴量を調整
            feature_cols = [
                col for col in self.feature_columns if col != "prediction_datetime"
            ]
            X_pred_features = X_pred.drop(
                columns=["prediction_datetime"], errors="ignore"
            )

            missing_cols = set(feature_cols) - set(X_pred_features.columns)
            for col in missing_cols:
                X_pred_features[col] = -1  # 欠損値として-1を設定

            X_pred_features = X_pred_features.reindex(
                columns=feature_cols, fill_value=-1
            )
        else:
            X_pred_features = X_pred.drop(
                columns=["prediction_datetime"], errors="ignore"
            )

        # 予測実行
        model = self.models[place_id]
        predictions = model.predict(X_pred_features)

        # 予測結果を整形
        results = []
        for idx, pred_time in enumerate(prediction_times):
            results.append(
                {
                    "place_id": place_id,
                    "target_datetime": pred_time.isoformat(),
                    "predicted_score": int(
                        round(max(0, predictions[idx]))
                    ),  # 負の値は0に
                    "confidence": self._calculate_confidence(
                        model, X_pred_features.iloc[idx : idx + 1]
                    ),
                }
            )

        # 予測結果をファイルに保存
        self._save_predictions_to_file(place_id, target_datetime, results)

        # データベース状態を記録（予測実行後）
        self._save_database_status_after_prediction(db, place_id, target_datetime, len(results))

        return results

    def _save_predictions_to_file(
        self,
        place_id: int,
        target_datetime: datetime,
        predictions: list[dict[str, Any]],
    ) -> None:
        """予測結果をJSONファイルに保存"""
        timestamp = target_datetime.strftime("%Y%m%d_%H%M%S")
        filename = f"place_{place_id}_{timestamp}.json"
        filepath = self.predictions_dir / filename

        prediction_data = {
            "place_id": place_id,
            "prediction_timestamp": target_datetime.isoformat(),
            "model_params": self.model_params,
            "predictions": predictions,
            "metadata": {
                "total_predictions": len(predictions),
                "feature_columns": self.feature_columns,
                "saved_at": datetime.now().isoformat(),
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(prediction_data, f, indent=2, ensure_ascii=False)

        logger.info(f"予測結果を保存しました: {filepath}")

    def _save_training_results_to_file(self, train_result: dict[str, Any]) -> None:
        """学習結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_results_{timestamp}.json"
        filepath = self.model_dir / filename

        training_data = {
            "training_timestamp": datetime.now().isoformat(),
            "model_params": self.model_params,
            "feature_columns": self.feature_columns,
            "results": train_result,
            "metadata": {
                "saved_at": datetime.now().isoformat(),
                "model_type": "RandomForestRegressor",
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)

        logger.info(f"学習結果を保存しました: {filepath}")

    def _save_database_status_after_prediction(
        self, db: Session, place_id: int, target_datetime: datetime, prediction_count: int
    ) -> None:
        """予測実行後のデータベース状態を記録"""
        from .database import DatabaseManager

        db_manager = DatabaseManager()

        # 予測前の状態
        status_before = db_manager.get_database_status(db, f"BEFORE_PREDICTION_place_{place_id}")

        # 予測実行（実際の保存は別で行われる）

        # 予測後の状態
        status_after = db_manager.get_database_status(db, f"AFTER_PREDICTION_place_{place_id}")

        # ファイルに保存
        timestamp = target_datetime.strftime("%Y%m%d_%H%M%S")

        before_filepath = self.model_dir / f"db_status_before_prediction_place_{place_id}_{timestamp}.json"
        after_filepath = self.model_dir / f"db_status_after_prediction_place_{place_id}_{timestamp}.json"

        db_manager.save_database_status(db, status_before, str(before_filepath))
        db_manager.save_database_status(db, status_after, str(after_filepath))

        logger.info(f"データベース状態を記録しました: {before_filepath}, {after_filepath}")

    def _calculate_confidence(
        self, model: RandomForestRegressor, X: pd.DataFrame
    ) -> float:
        """
        予測の信頼度を計算（各決定木の予測のばらつきから）

        Args:
            model: ランダムフォレストモデル
            X: 入力特徴量

        Returns:
            信頼度（0-1）
        """
        # 各決定木の予測を取得
        tree_predictions = []
        for tree in model.estimators_:
            tree_predictions.append(tree.predict(X)[0])

        # 標準偏差から信頼度を計算
        std = np.std(tree_predictions)
        mean = np.mean(tree_predictions)

        # 変動係数の逆数を信頼度とする（最大1に正規化）
        if mean > 0:
            cv = std / mean
            confidence = min(1.0, 1.0 / (1.0 + cv))
        else:
            confidence = 0.5

        return float(confidence)

    def _save_models(self) -> None:
        """モデルをファイルに保存"""
        # モデル本体を保存
        model_path = self.model_dir / "models.pkl"
        with open(model_path, "wb") as f:
            pickle.dump(self.models, f)

        # メタデータを保存
        metadata = {
            "feature_columns": self.feature_columns,
            "model_params": self.model_params,
            "saved_at": datetime.now().isoformat(),
            "place_ids": list(self.models.keys()),
        }

        metadata_path = self.model_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"モデルを保存しました: {model_path}")

    def _load_models(self) -> None:
        """保存されたモデルをロード"""
        model_path = self.model_dir / "models.pkl"
        metadata_path = self.model_dir / "metadata.json"

        if not model_path.exists() or not metadata_path.exists():
            logger.warning("保存されたモデルが見つかりません")
            return

        # モデルをロード
        with open(model_path, "rb") as f:
            self.models = pickle.load(f)

        # メタデータをロード
        with open(metadata_path) as f:
            metadata = json.load(f)
            self.feature_columns = metadata.get("feature_columns")
            self.model_params = metadata.get("model_params", self.model_params)

        logger.info(f"モデルをロードしました: {len(self.models)}個")

    def _save_model_info_to_db(
        self,
        db: Session,
        db_manager: DatabaseManager,
        results: dict[int, dict[str, Any]],
    ) -> None:
        """モデル情報をデータベースに保存"""
        for place_id, result in results.items():
            # センサーIDを取得（簡単のため場所IDと同じと仮定）
            sensor = db.query(Sensor).filter(Sensor.place_id == place_id).first()

            if not sensor:
                # センサーが存在しない場合は作成
                sensor = Sensor(place_id=place_id)
                db.add(sensor)
                db.commit()
                db.refresh(sensor)

            # モデルパラメータを保存
            model_params = {
                "model_type": "RandomForestRegressor",
                "params": self.model_params,
                "metrics": {
                    "train_mae": result["train_mae"],
                    "test_mae": result["test_mae"],
                    "test_rmse": result["test_rmse"],
                    "test_r2": result["test_r2"],
                },
                "feature_columns": self.feature_columns,
                "train_samples": result["train_samples"],
                "test_samples": result["test_samples"],
            }

            db_manager.save_prediction_model(
                db=db, sensor_id=int(sensor.id), model_params=model_params
            )
