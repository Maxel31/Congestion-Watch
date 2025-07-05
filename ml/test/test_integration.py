"""
実際のデータベースを使用した統合テスト
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# PostgreSQL統合テスト用環境変数設定
os.environ["DATABASE_URL"] = (
    "postgresql://postgres:postgres@localhost:5432/congestion_watch"
)

from src.database import DatabaseManager, get_db  # noqa: E402
from src.feature_engineering import FeatureEngineer  # noqa: E402
from src.model import CongestionPredictionModel  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def check_postgresql_connection() -> bool:
    """PostgreSQL接続を確認"""
    logger.info("PostgreSQL接続確認開始")
    try:
        with get_db() as db:
            from sqlalchemy import text

            result = db.execute(text("SELECT version()")).fetchone()
            if result:
                logger.info(f"PostgreSQL接続成功: {result[0][:50]}...")
            else:
                logger.error("PostgreSQL接続結果が空です")
                return False
            return True
    except Exception as e:
        logger.error(f"PostgreSQL接続失敗: {str(e)}")
        logger.error(
            "Docker Composeでpostgresサービスが起動していることを確認してください"
        )
        return False


def test_full_integration() -> None:
    """完全な統合テスト"""
    logger.info("=== PostgreSQL統合テスト開始 ===")

    # 1. PostgreSQL接続確認
    if not check_postgresql_connection():
        logger.error("PostgreSQL接続に失敗しました。テストを中止します。")
        return

    # 2. データベース接続確認
    logger.info("\n--- データベース接続確認 ---")
    with get_db() as db:
        db_manager = DatabaseManager()
        places = db_manager.get_all_places(db)
        actual_scores = db_manager.get_actual_scores(db)

        logger.info(f"場所データ: {len(places)}件")
        logger.info(f"実測データ: {len(actual_scores)}件")

        assert len(places) > 0, "場所データが存在しません"
        assert len(actual_scores) > 0, "実測データが存在しません"

    # 3. 特徴量エンジニアリング
    logger.info("\n--- 特徴量エンジニアリング ---")
    with get_db() as db:
        feature_engineer = FeatureEngineer(db)
        X, y = feature_engineer.prepare_training_data()

        logger.info(f"訓練データ: {len(X)}件")
        logger.info(f"特徴量数: {len(X.columns) if not X.empty else 0}")

        if not X.empty:
            logger.info(f"特徴量例: {list(X.columns)[:5]}")
            logger.info(
                f"ターゲット統計: 平均={y.mean():.2f}, 最小={y.min()}, 最大={y.max()}"
            )

        assert not X.empty, "特徴量が作成されませんでした"
        assert len(y) > 10, "十分な訓練データがありません"

    # 4. モデル訓練
    logger.info("\n--- モデル訓練 ---")
    model = CongestionPredictionModel(model_dir="test_models")

    with get_db() as db:
        train_results = model.train(db, test_size=0.3)

        logger.info(f"訓練結果: {train_results['status']}")
        logger.info(f"訓練済みモデル数: {train_results['trained_models']}")

        assert train_results["status"] == "success", (
            f"モデル訓練失敗: {train_results.get('message', '')}"
        )
        assert train_results["trained_models"] > 0, "モデルが訓練されませんでした"

        # 詳細結果表示
        for place_id, result in train_results.get("results", {}).items():
            logger.info(
                f"場所ID {place_id}: "
                f"MAE={result.get('test_mae', 0):.2f}, "
                f"RMSE={result.get('test_rmse', 0):.2f}, "
                f"R2={result.get('test_r2', 0):.3f}"
            )

    # 5. 予測実行
    logger.info("\n--- 予測実行 ---")
    with get_db() as db:
        db_manager = DatabaseManager()
        places = db_manager.get_all_places(db)

        for place in places[:2]:  # 最初の2場所で予測
            target_time = datetime.now()
            predictions = model.predict(
                db=db,
                place_id=int(place.id),
                target_datetime=target_time,
                hours_ahead=3,  # 3時間先まで
            )

            logger.info(f"場所 {place.name} の予測: {len(predictions)}件")

            assert len(predictions) > 0, (
                f"場所 {place.name} の予測が生成されませんでした"
            )

            # 予測サンプル表示
            if predictions:
                for i, pred in enumerate(predictions[:3]):
                    logger.info(
                        f"  {i + 1}: {pred['target_datetime']} -> "
                        f"スコア={pred['predicted_score']}, "
                        f"信頼度={pred['confidence']:.3f}"
                    )

    # 6. 予測データ保存
    logger.info("\n--- 予測データ保存 ---")
    with get_db() as db:
        db_manager = DatabaseManager()

        test_predictions = [
            {
                "model_id": 1,
                "score": 45,
                "place_id": 1,
                "target_datetime": datetime.now() + timedelta(minutes=5),
            },
            {
                "model_id": 1,
                "score": 50,
                "place_id": 2,
                "target_datetime": datetime.now() + timedelta(minutes=10),
            },
        ]

        saved = db_manager.save_predictions(db, test_predictions)
        logger.info(f"予測データ保存: {len(saved)}件")

        assert len(saved) > 0, "予測データが保存されませんでした"

    logger.info("\n=== PostgreSQL統合テスト完了 ===")
    logger.info("全ての機能が正常に動作しました！")


if __name__ == "__main__":
    test_full_integration()
