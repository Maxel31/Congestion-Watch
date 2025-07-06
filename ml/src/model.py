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

from .config import config
from .database import DatabaseManager, Sensor
from .feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class CongestionPredictionModel:
    """混雑度予測モデル"""

    def __init__(self, model_dir: str | None = None):
        # 本番環境ではローカルファイル保存を無効化するため、model_dirは使用しない
        if model_dir is None:
            model_dir = config.MODEL_DIR
        self.model_dir = Path(model_dir)
        # 本番環境ではディレクトリ作成をスキップ
        if config.is_development():
            self.model_dir.mkdir(exist_ok=True)

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

        # 実測データが存在する場所のみを取得
        from sqlalchemy import text

        # 実測データが存在する場所IDを取得
        actual_places_result = db.execute(
            text("SELECT DISTINCT place_id FROM actual_score ORDER BY place_id")
        ).fetchall()

        if not actual_places_result:
            logger.error("実測データが存在しません")
            return {"status": "error", "message": "実測データが存在しません"}

        actual_place_ids = [row[0] for row in actual_places_result]

        # 実測データが存在する場所の情報を取得
        places = db_manager.get_all_places(db)
        actual_places = [place for place in places if place.id in actual_place_ids]

        results = {}

        # 実測データが存在する場所のみでモデルを訓練
        for place in actual_places:
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

        # 開発環境でのみモデルをファイルに保存
        if config.is_development():
            self._save_models()

        # データベースにモデル情報を保存
        self._save_model_info_to_db(
            db, db_manager, {int(k): v for k, v in results.items()}
        )

        # 学習結果を返す
        train_result = {
            "status": "success",
            "trained_models": len(self.models),
            "results": results,
        }

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
            if config.is_development():
                self._load_models()
            else:
                # 本番環境ではデータベースからモデルを再構築
                self._load_models_from_db(db, place_id)

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

            # 不要な特徴量を削除（訓練時にない特徴量）
            extra_cols = set(X_pred_features.columns) - set(feature_cols)
            if extra_cols:
                logger.warning(f"不要な特徴量を削除: {extra_cols}")
                X_pred_features = X_pred_features.drop(columns=list(extra_cols))

            # 欠損している特徴量を追加
            missing_cols = set(feature_cols) - set(X_pred_features.columns)
            for col in missing_cols:
                X_pred_features[col] = -1  # 欠損値として-1を設定

            # 特徴量カラムの順序を訓練時と同じに揃える
            X_pred_features = X_pred_features.reindex(
                columns=feature_cols, fill_value=-1
            )

            logger.info(f"予測時の特徴量数: {len(X_pred_features.columns)}")
            logger.info(f"訓練時の特徴量数: {len(feature_cols)}")
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
                        model, X_pred_features.iloc[idx : idx + 1].values
                    ),
                }
            )

        # 本番環境では予測結果のファイル保存を無効化

        # 予測結果をデータベースに保存
        self._save_predictions_to_db(db, place_id, results)

        # 本番環境ではデータベース状態記録を無効化

        return results

    # 本番環境では予測結果のファイル保存を無効化

    # 本番環境では学習結果のファイル保存を無効化

    # 本番環境ではデータベース状態記録を無効化

    def _save_predictions_to_db(
        self, db: Session, place_id: int, predictions: list[dict[str, Any]]
    ) -> None:
        """予測結果をデータベースに保存"""
        db_manager = DatabaseManager()

        # 現在のセンサーとモデルIDを取得
        sensor = db.query(Sensor).filter(Sensor.place_id == place_id).first()
        if not sensor:
            logger.warning(f"場所ID {place_id} のセンサーが見つかりません")
            return

        # 最新のモデルIDを取得
        latest_model = db_manager.get_latest_model(db, int(sensor.id))
        if not latest_model:
            logger.warning(f"センサーID {sensor.id} のモデルが見つかりません")
            return

        # 予測結果をデータベース形式に変換
        prediction_data = []
        for pred in predictions:
            prediction_data.append(
                {
                    "model_id": latest_model.id,
                    "score": int(round(pred["predicted_score"])),
                    "place_id": place_id,
                    "target_datetime": pred["target_datetime"],
                }
            )

        # データベースに保存
        saved_predictions = db_manager.save_predictions(db, prediction_data)
        logger.info(f"予測結果をデータベースに保存しました: {len(saved_predictions)}件")

    def _calculate_confidence(
        self, model: RandomForestRegressor, X: np.ndarray[Any, Any] | pd.DataFrame
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

    def _load_models_from_db(self, db: Session, place_id: int) -> None:
        """本番環境でデータベースからモデルパラメータを取得してモデルを再構築"""
        db_manager = DatabaseManager()

        # センサーIDを取得
        sensor = db.query(Sensor).filter(Sensor.place_id == place_id).first()
        if not sensor:
            logger.warning(f"場所ID {place_id} のセンサーが見つかりません")
            return

        # 最新のモデル情報を取得
        latest_model = db_manager.get_latest_model(db, int(sensor.id))
        if not latest_model:
            logger.warning(f"センサーID {sensor.id} のモデルが見つかりません")
            return

        try:
            # モデルパラメータを取得
            model_params = latest_model.model_params
            if isinstance(model_params, dict):
                # モデルのハイパーパラメータを取得
                self.feature_columns = model_params.get("feature_columns")

                # 新しいモデルインスタンスを作成（本番環境では再訓練）
                # 注：実際の本番環境では、モデル自体もDBに保存するか、再訓練が必要
                logger.warning(
                    f"本番環境でモデルパラメータを取得しましたが、モデル本体の再構築が必要です: 場所ID {place_id}"
                )

        except Exception as e:
            logger.error(f"モデル情報の読み込みエラー: {e}")

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
