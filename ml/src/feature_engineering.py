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
        # 全場所の情報を取得
        places = self.db_manager.get_all_places(self.db)
        place_ids = [int(p.id) for p in places]

        # 実測データを取得
        actual_scores = self.db_manager.get_actual_scores(
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

        # 特徴量を作成
        features = []
        targets = []

        for place in places:
            place_df = df[df["place_id"] == place.id].copy()

            if len(place_df) < 2:
                continue

            # 各時点での特徴量を作成
            for idx in range(1, len(place_df)):
                feature_dict = self._create_features(
                    place_df.iloc[idx], place_df.iloc[:idx], df, place_ids
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
        # 全場所の情報を取得
        places = self.db_manager.get_all_places(self.db)
        place_ids = [int(p.id) for p in places]

        # 過去データを取得（予測時点より前のデータ）
        historical_data = self.db_manager.get_actual_scores(
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

        # 予測時点を生成（5分間隔、正確な時刻に調整）
        prediction_times = []

        # 開始時刻を5分単位に切り上げ
        start_minute = (target_datetime.minute // 5 + 1) * 5
        if start_minute >= 60:
            current_time = target_datetime.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            current_time = target_datetime.replace(minute=start_minute, second=0, microsecond=0)

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

            feature_dict = self._create_features(
                current_record,
                past_data[past_data["place_id"] == place_id],
                past_data,
                place_ids,
            )

            if feature_dict:
                feature_dict["prediction_datetime"] = pred_time
                features.append(feature_dict)

        if not features:
            logger.warning("予測用特徴量を作成できませんでした")
            return pd.DataFrame()

        X = pd.DataFrame(features)
        X = self._handle_missing_values(X)

        logger.info(f"予測用特徴量カラム: {list(X.columns)}")

        return X

    def _create_features(
        self,
        current: pd.Series,
        past_data: pd.DataFrame,
        all_data: pd.DataFrame,
        place_ids: list[int],
    ) -> dict[str, Any]:
        """
        単一レコードの特徴量を作成

        Args:
            current: 現在のレコード
            past_data: 同じ場所の過去データ
            all_data: 全場所の過去データ
            place_ids: 全場所ID

        Returns:
            特徴量辞書
        """
        # 基本特徴量（時間的特徴は要件により使用しない）
        features = {
            "place_id": current["place_id"],
        }

        if len(past_data) == 0:
            return features

        # 過去の混雑度統計（時間的特徴は使用せず、短期的なトレンドに特化）
        if len(past_data) > 0:
            current_time = current["target_datetime"]

            # 直近15分の統計
            cutoff_15m = pd.Timestamp(current_time) - pd.Timedelta(minutes=15)
            recent_15m = past_data[
                pd.to_datetime(past_data["target_datetime"]) >= cutoff_15m
            ]
            if len(recent_15m) > 0:
                features["past_15m_mean"] = recent_15m["score"].mean()
                features["past_15m_max"] = recent_15m["score"].max()
                features["past_15m_min"] = recent_15m["score"].min()
                features["past_15m_count"] = len(recent_15m)
                # トレンド（最近の変化傾向）
                if len(recent_15m) >= 2:
                    recent_sorted = recent_15m.sort_values("target_datetime")
                    features["past_15m_trend"] = recent_sorted["score"].iloc[-1] - recent_sorted["score"].iloc[0]

            # 直近1時間の統計
            cutoff_1h = pd.Timestamp(current_time) - pd.Timedelta(hours=1)
            recent_1h = past_data[
                pd.to_datetime(past_data["target_datetime"]) >= cutoff_1h
            ]
            if len(recent_1h) > 0:
                features["past_1h_mean"] = recent_1h["score"].mean()
                features["past_1h_max"] = recent_1h["score"].max()
                features["past_1h_min"] = recent_1h["score"].min()
                features["past_1h_std"] = recent_1h["score"].std()
                features["past_1h_count"] = len(recent_1h)

            # 直近3時間の統計
            cutoff_3h = pd.Timestamp(current_time) - pd.Timedelta(hours=3)
            recent_3h = past_data[
                pd.to_datetime(past_data["target_datetime"]) >= cutoff_3h
            ]
            if len(recent_3h) > 0:
                features["past_3h_mean"] = recent_3h["score"].mean()
                features["past_3h_max"] = recent_3h["score"].max()
                features["past_3h_min"] = recent_3h["score"].min()
                features["past_3h_std"] = recent_3h["score"].std()

            # 最新値（直近のデータポイント）
            if len(past_data) > 0:
                latest_data = past_data.sort_values("target_datetime").iloc[-1]
                features["latest_score"] = latest_data["score"]

        # 他の場所の混雑度（相関を考慮）
        current_time_ts = pd.Timestamp(current["target_datetime"])
        time_window_start = current_time_ts - pd.Timedelta(minutes=30)

        for other_place_id in place_ids:
            if other_place_id != current["place_id"]:
                other_recent = all_data[
                    (all_data["place_id"] == other_place_id)
                    & (pd.to_datetime(all_data["target_datetime"]) >= time_window_start)
                    & (pd.to_datetime(all_data["target_datetime"]) <= current_time_ts)
                ]

                if len(other_recent) > 0:
                    features[f"place_{other_place_id}_recent_mean"] = other_recent[
                        "score"
                    ].mean()
                    features[f"place_{other_place_id}_recent_max"] = other_recent[
                        "score"
                    ].max()

        return features

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        欠損値の処理

        Args:
            df: 特徴量DataFrame

        Returns:
            欠損値処理済みのDataFrame
        """
        # 数値カラムの欠損値を-1で埋める（RandomForestで扱えるように）
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(-1)

        return df
