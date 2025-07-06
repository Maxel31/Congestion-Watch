"""
特徴量エンジニアリング
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from .database import DatabaseManager

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """特徴量エンジニアリングクラス"""

    def __init__(self, db: Session):
        self.db = db
        self.db_manager = DatabaseManager()

    def prepare_training_data(
        self, place_id: int | None = None, start_date: datetime | None = None
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        訓練データの準備

        Args:
            place_id: 対象場所ID（Noneの場合は全場所）
            start_date: データ取得開始日時

        Returns:
            X: 特徴量DataFrame
            y: ターゲット（混雑度）Series
        """
        # 実測データが存在する場所IDのみを取得
        from sqlalchemy import text

        actual_places_result = self.db.execute(
            text("SELECT DISTINCT place_id FROM actual_score ORDER BY place_id")
        ).fetchall()
        place_ids = (
            [row[0] for row in actual_places_result] if actual_places_result else []
        )

        # 全場所の情報を取得（リレーション用）
        places = self.db_manager.get_all_places(self.db)

        # 実測データを取得
        actual_scores = self.db_manager.get_actual_scores(
            self.db, place_id=place_id, start_date=start_date
        )

        # 予測データを取得（予測誤差計算用）
        predicted_scores = self.db_manager.get_predicted_scores(
            self.db, place_id=place_id, start_date=start_date
        )

        if not actual_scores:
            logger.warning("実測データが存在しません")
            return pd.DataFrame(), pd.Series()

        # DataFrameに変換
        data = []
        for score in actual_scores:
            data.append(
                {
                    "place_id": score.place_id,
                    "target_datetime": score.target_datetime,
                    "score": score.score,
                    "created_at": score.created_at,
                }
            )

        df = pd.DataFrame(data)
        df["target_datetime"] = pd.to_datetime(df["target_datetime"])
        df = df.sort_values(["place_id", "target_datetime"])

        # 予測データをDataFrameに変換
        pred_data = []
        for pred in predicted_scores:
            pred_data.append(
                {
                    "place_id": pred.place_id,
                    "target_datetime": pred.target_datetime,
                    "predicted_score": pred.score,
                    "model_id": pred.model_id,
                }
            )

        pred_df = pd.DataFrame(pred_data)
        if not pred_df.empty:
            pred_df["target_datetime"] = pd.to_datetime(pred_df["target_datetime"])
            pred_df = pred_df.sort_values(["place_id", "target_datetime"])

        # 特徴量を作成
        features = []
        targets = []

        for place in places:
            place_df = df[df["place_id"] == place.id].copy()

            if len(place_df) < 2:
                continue

            # 各時点での特徴量を作成
            for idx in range(1, len(place_df)):
                # 該当場所の予測データを取得
                place_pred_df = (
                    pred_df[pred_df["place_id"] == place.id]
                    if not pred_df.empty
                    else pd.DataFrame()
                )

                feature_dict = self._create_features(
                    place_df.iloc[idx],
                    place_df.iloc[:idx],
                    df,
                    place_ids,
                    place_pred_df,
                )

                if feature_dict:
                    features.append(feature_dict)
                    targets.append(place_df.iloc[idx]["score"])

        if not features:
            logger.warning("特徴量を作成できませんでした")
            return pd.DataFrame(), pd.Series()

        X = pd.DataFrame(features)
        y = pd.Series(targets)

        # 欠損値の処理
        X = self._handle_missing_values(X)

        logger.info(f"訓練データ作成完了: {len(X)}件")
        return X, y

    def prepare_prediction_features(
        self, place_id: int, target_datetime: datetime, prediction_hours: int = 24
    ) -> pd.DataFrame:
        """
        予測用の特徴量を準備

        Args:
            place_id: 予測対象の場所ID
            target_datetime: 予測開始時刻
            prediction_hours: 予測時間（時間）

        Returns:
            予測用特徴量DataFrame
        """
        # 実測データが存在する場所IDのみを取得
        from sqlalchemy import text

        actual_places_result = self.db.execute(
            text("SELECT DISTINCT place_id FROM actual_score ORDER BY place_id")
        ).fetchall()
        place_ids = (
            [row[0] for row in actual_places_result] if actual_places_result else []
        )

        # 過去データを取得（予測時点より前のデータ）
        historical_data = self.db_manager.get_actual_scores(
            self.db, end_date=target_datetime
        )

        # 過去の予測データを取得
        historical_predictions = self.db_manager.get_predicted_scores(
            self.db, end_date=target_datetime
        )

        if not historical_data:
            logger.warning("過去データが存在しません")
            return pd.DataFrame()

        # DataFrameに変換
        hist_df = pd.DataFrame(
            [
                {
                    "place_id": score.place_id,
                    "target_datetime": score.target_datetime,
                    "score": score.score,
                }
                for score in historical_data
            ]
        )

        hist_df["target_datetime"] = pd.to_datetime(hist_df["target_datetime"])

        # 過去の予測データをDataFrameに変換
        hist_pred_df = pd.DataFrame(
            [
                {
                    "place_id": pred.place_id,
                    "target_datetime": pred.target_datetime,
                    "predicted_score": pred.score,
                    "model_id": pred.model_id,
                }
                for pred in historical_predictions
            ]
        )
        if not hist_pred_df.empty:
            hist_pred_df["target_datetime"] = pd.to_datetime(
                hist_pred_df["target_datetime"]
            )

        # 予測時点を生成（5分間隔、正確な時刻に調整）
        prediction_times = []

        # 開始時刻を5分単位に切り上げ
        start_minute = (target_datetime.minute // 5 + 1) * 5
        if start_minute >= 60:
            current_time = target_datetime.replace(
                minute=0, second=0, microsecond=0
            ) + timedelta(hours=1)
        else:
            current_time = target_datetime.replace(
                minute=start_minute, second=0, microsecond=0
            )

        end_time = target_datetime + timedelta(hours=prediction_hours)

        while current_time <= end_time:
            prediction_times.append(current_time)
            current_time += timedelta(minutes=5)

        # 各予測時点の特徴量を作成
        features = []
        for pred_time in prediction_times:
            # 予測時点のダミーレコード
            current_record = pd.Series(
                {
                    "place_id": place_id,
                    "target_datetime": pred_time,
                    "score": np.nan,  # 予測時のスコアは不明
                }
            )

            # 過去データ（予測時点より前）
            past_data = hist_df[hist_df["target_datetime"] < pred_time]

            # 該当場所の過去予測データ
            past_pred_data = (
                hist_pred_df[
                    (hist_pred_df["place_id"] == place_id)
                    & (hist_pred_df["target_datetime"] < pred_time)
                ]
                if not hist_pred_df.empty
                else pd.DataFrame()
            )

            feature_dict = self._create_features(
                current_record,
                past_data[past_data["place_id"] == place_id],
                past_data,
                place_ids,
                past_pred_data,
            )

            if feature_dict:
                feature_dict["prediction_datetime"] = pred_time
                features.append(feature_dict)

        if not features:
            logger.warning("予測用特徴量を作成できませんでした")
            return pd.DataFrame()

        X = pd.DataFrame(features)
        X = self._handle_missing_values(X)

        # 特徴量の種類別に整理して表示
        feature_categories = self._categorize_features(list(X.columns))
        logger.info(f"予測用特徴量数: {len(X.columns)}")
        for category, feature_list in feature_categories.items():
            if feature_list:
                logger.info(
                    f"  {category}: {len(feature_list)}個 - {feature_list[:5]}{'...' if len(feature_list) > 5 else ''}"
                )

        return X

    def _create_features(
        self,
        current: pd.Series,
        past_data: pd.DataFrame,
        all_data: pd.DataFrame,
        place_ids: list[int],
        past_pred_data: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        """
        単一レコードの特徴量を作成

        Args:
            current: 現在のレコード
            past_data: 同じ場所の過去データ
            all_data: 全場所の過去データ
            place_ids: 全場所ID
            past_pred_data: 同じ場所の過去予測データ

        Returns:
            特徴量辞書
        """
        # 基本特徴量（時間的特徴は要件により使用しない）
        features = {
            "place_id": current["place_id"],
        }

        if len(past_data) == 0:
            return features

        # 時系列パターンに重点を置いた特徴量（シンプル版）
        if len(past_data) > 0:
            current_time = current["target_datetime"]
            past_data_sorted = past_data.sort_values("target_datetime")
            latest_data = past_data_sorted.iloc[-1]

            # 核となる時系列特徴量のみに絞る（最も重要な15分と30分の窓）
            core_windows = [15, 30]  # 分
            for minutes_back in core_windows:
                cutoff = pd.Timestamp(current_time) - pd.Timedelta(minutes=minutes_back)
                window_data = past_data[
                    pd.to_datetime(past_data["target_datetime"]) >= cutoff
                ]
                if len(window_data) > 0:
                    features[f"mean_{minutes_back}m"] = window_data["score"].mean()
                    features[f"std_{minutes_back}m"] = window_data["score"].std()
                    # トレンド（線形回帰の傾き的な指標）
                    if len(window_data) >= 2:
                        sorted_data = window_data.sort_values("target_datetime")
                        first_score = sorted_data.iloc[0]["score"]
                        last_score = sorted_data.iloc[-1]["score"]
                        features[f"trend_{minutes_back}m"] = (
                            last_score - first_score
                        ) / max(first_score, 1)

            # 短期と中期の比較（最も重要な1つの比較のみ）
            if "mean_15m" in features and "mean_30m" in features:
                features["short_vs_long_ratio"] = features["mean_15m"] / max(
                    features["mean_30m"], 1
                )

            # 直近1時間の全体傾向（シンプルな統計のみ）
            cutoff_1h = pd.Timestamp(current_time) - pd.Timedelta(hours=1)
            recent_1h = past_data[
                pd.to_datetime(past_data["target_datetime"]) >= cutoff_1h
            ]
            if len(recent_1h) > 0:
                features["hour_mean"] = recent_1h["score"].mean()
                # レンジ内での現在位置
                hour_max = recent_1h["score"].max()
                hour_min = recent_1h["score"].min()
                hour_range = hour_max - hour_min
                if hour_range > 0:
                    features["position_in_hour_range"] = (
                        latest_data["score"] - hour_min
                    ) / hour_range

        # 他の場所との相対関係（場所が複数ある場合のみ、シンプル版）
        if len(place_ids) > 1:
            current_time_ts = pd.Timestamp(current["target_datetime"])
            time_window_start = current_time_ts - pd.Timedelta(minutes=30)

            # 自分以外の場所の最近の混雑度を取得
            other_places_data = all_data[
                (all_data["place_id"] != current["place_id"])
                & (pd.to_datetime(all_data["target_datetime"]) >= time_window_start)
                & (pd.to_datetime(all_data["target_datetime"]) <= current_time_ts)
            ]

            if len(other_places_data) > 0:
                other_mean = other_places_data["score"].mean()
                # 自分の平均と他の場所の平均の比較（1つの指標のみ）
                if "mean_15m" in features:
                    features["self_vs_others_ratio"] = features["mean_15m"] / max(
                        other_mean, 1
                    )
            else:
                features["self_vs_others_ratio"] = None
        else:
            # 場所が1つしかない場合は欠損値として扱う
            features["self_vs_others_ratio"] = None

        # 予測誤差特徴量を追加（シンプル版）
        if past_pred_data is not None and not past_pred_data.empty:
            current_time_ts = pd.Timestamp(current["target_datetime"])

            # 実測データと予測データをマージして誤差を計算
            past_actual_with_time = past_data.copy()
            past_actual_with_time["target_datetime"] = pd.to_datetime(
                past_actual_with_time["target_datetime"]
            )

            # 時刻でマージ（内部結合）
            merged_data = pd.merge(
                past_actual_with_time[["target_datetime", "score"]],
                past_pred_data[["target_datetime", "predicted_score"]],
                on="target_datetime",
                how="inner",
            )

            if not merged_data.empty:
                # 予測誤差を計算（実測値 - 予測値）
                merged_data["prediction_error"] = (
                    merged_data["score"] - merged_data["predicted_score"]
                )

                # 直近の予測誤差統計（最も重要な指標のみ）
                recent_errors = merged_data[
                    merged_data["target_datetime"]
                    >= (current_time_ts - pd.Timedelta(hours=1))
                ]

                if not recent_errors.empty:
                    features["recent_prediction_error_abs_mean"] = (
                        recent_errors["prediction_error"].abs().mean()
                    )
                else:
                    features["recent_prediction_error_abs_mean"] = -1
            else:
                features["recent_prediction_error_abs_mean"] = -1
        else:
            features["recent_prediction_error_abs_mean"] = -1

        return features

    def _categorize_features(self, feature_names: list[str]) -> dict[str, list[str]]:
        """特徴量をカテゴリ別に分類"""
        categories: dict[str, list[str]] = {
            "基本特徴量": [],
            "時系列パターン": [],
            "他の場所の混雑度": [],
            "予測誤差": [],
            "その他": [],
        }

        for feature in feature_names:
            if feature == "place_id":
                categories["基本特徴量"].append(feature)
            elif any(keyword in feature for keyword in ["self_vs_others_"]):
                categories["他の場所の混雑度"].append(feature)
            elif any(
                prefix in feature
                for prefix in ["mean_", "std_", "trend_", "ratio", "hour_", "position_"]
            ):
                categories["時系列パターン"].append(feature)
            elif any(keyword in feature for keyword in ["prediction_error"]):
                categories["予測誤差"].append(feature)
            else:
                categories["その他"].append(feature)

        return categories

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        欠損値の処理

        Args:
            df: 特徴量DataFrame

        Returns:
            欠損値処理済みのDataFrame
        """
        # 他の場所に依存する特徴量の特別処理
        other_place_features = ["self_vs_others_ratio"]

        for feature in other_place_features:
            if feature in df.columns:
                # 場所が1つしかない場合や他の場所のデータがない場合のNone値を-1で埋める
                df[feature] = df[feature].fillna(-1)

        # その他の数値カラムの欠損値を-1で埋める（RandomForestで扱えるように）
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(-1)

        return df
