"""
データベース接続とML機能の統合テスト
"""

import logging
from datetime import datetime, timedelta
import sys
from typing import Dict
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db, DatabaseManager  # noqa: E402
from src.model import CongestionPredictionModel  # noqa: E402
from src.feature_engineering import FeatureEngineer  # noqa: E402

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_connection() -> None:
    """データベース接続テスト"""
    logger.info("データベース接続テスト開始")

    try:
        with get_db() as db:
            # 接続確認
            from sqlalchemy import text

            result = db.execute(text("SELECT 1")).fetchone()
            logger.info(f"データベース接続成功: {result}")
            assert result is not None

            # テーブル存在確認
            db_manager = DatabaseManager()
            places = db_manager.get_all_places(db)
            logger.info(f"場所データ取得: {len(places)}件")

            for place in places:
                logger.info(f"  - 場所ID: {place.id}, 名前: {place.name}")

            # 実測データ確認
            actual_scores = db_manager.get_actual_scores(db)
            logger.info(f"実測データ取得: {len(actual_scores)}件")

            if actual_scores:
                latest = actual_scores[-1]
                logger.info(
                    f"  - 最新データ: 場所ID={latest.place_id}, スコア={latest.score}, 時刻={latest.target_datetime}"
                )

    except Exception as e:
        logger.error(f"データベース接続エラー: {str(e)}")
        assert False, f"データベース接続エラー: {str(e)}"


def test_feature_engineering() -> None:
    """特徴量エンジニアリングテスト"""
    logger.info("特徴量エンジニアリングテスト開始")

    try:
        with get_db() as db:
            feature_engineer = FeatureEngineer(db)

            # 訓練データ準備
            X, y = feature_engineer.prepare_training_data()
            logger.info(
                f"訓練データ作成: {len(X)}件, 特徴量数: {len(X.columns) if not X.empty else 0}"
            )

            if not X.empty:
                logger.info(f"特徴量: {list(X.columns)[:10]}...")  # 最初の10個
                logger.info(
                    f"ターゲット統計: 平均={y.mean():.2f}, 最小={y.min()}, 最大={y.max()}"
                )

            assert not X.empty, "訓練データが作成されませんでした"

    except Exception as e:
        logger.error(f"特徴量エンジニアリングエラー: {str(e)}")
        assert False, f"特徴量エンジニアリングエラー: {str(e)}"


def test_model_training() -> None:
    """モデル訓練テスト"""
    logger.info("モデル訓練テスト開始")

    try:
        model = CongestionPredictionModel(model_dir="test_models")

        with get_db() as db:
            results = model.train(db, test_size=0.3)

            logger.info(f"訓練結果: {results['status']}")
            logger.info(f"訓練済みモデル数: {results['trained_models']}")

            for place_id, result in results.get("results", {}).items():
                logger.info(
                    f"場所ID {place_id}: "
                    f"MAE={result.get('test_mae', 0):.2f}, "
                    f"R2={result.get('test_r2', 0):.3f}"
                )

            assert results["status"] == "success", (
                f"モデル訓練失敗: {results.get('message', '')}"
            )

    except Exception as e:
        logger.error(f"モデル訓練エラー: {str(e)}")
        assert False, f"モデル訓練エラー: {str(e)}"


def test_prediction() -> None:
    """予測テスト"""
    logger.info("予測テスト開始")

    try:
        model = CongestionPredictionModel(model_dir="test_models")

        with get_db() as db:
            # 場所データを取得
            db_manager = DatabaseManager()
            places = db_manager.get_all_places(db)

            assert places, "場所データが存在しません"

            place_id = int(places[0].id)
            target_time = datetime.now()

            predictions = model.predict(
                db=db,
                place_id=place_id,
                target_datetime=target_time,
                hours_ahead=2,  # 2時間先まで
            )

            logger.info(f"予測結果: {len(predictions)}件")

            if predictions:
                logger.info("予測サンプル:")
                for i, pred in enumerate(predictions[:5]):  # 最初の5件
                    logger.info(
                        f"  {i + 1}: {pred['target_datetime']} -> "
                        f"スコア={pred['predicted_score']}, "
                        f"信頼度={pred['confidence']:.3f}"
                    )

            assert len(predictions) > 0, "予測結果が0件でした"

    except Exception as e:
        logger.error(f"予測エラー: {str(e)}")
        assert False, f"予測エラー: {str(e)}"


def test_prediction_storage() -> None:
    """予測データの保存テスト"""
    logger.info("予測データ保存テスト開始")

    try:
        with get_db() as db:
            db_manager = DatabaseManager()

            # テスト用予測データ
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
                    "place_id": 1,
                    "target_datetime": datetime.now() + timedelta(minutes=10),
                },
            ]

            # 予測データ保存
            saved_predictions = db_manager.save_predictions(db, test_predictions)
            logger.info(f"予測データ保存: {len(saved_predictions)}件")

            assert len(saved_predictions) > 0, "予測データが保存されませんでした"

    except Exception as e:
        logger.error(f"予測データ保存エラー: {str(e)}")
        assert False, f"予測データ保存エラー: {str(e)}"


def run_integration_tests() -> bool:
    """統合テスト実行"""
    logger.info("=== ML統合テスト開始 ===")

    # テスト実行
    tests = [
        ("データベース接続", test_database_connection),
        ("特徴量エンジニアリング", test_feature_engineering),
        ("モデル訓練", test_model_training),
        ("予測", test_prediction),
        ("予測データ保存", test_prediction_storage),
    ]

    results: Dict[str, bool] = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name}テスト ---")
        try:
            result = test_func()
            results[test_name] = result is not None
            status = "成功" if results[test_name] else "失敗"
            logger.info(f"{test_name}テスト: {status}")
        except Exception as e:
            logger.error(f"{test_name}テストでエラー: {str(e)}")
            results[test_name] = False

    # 結果サマリー
    logger.info("\n=== テスト結果サマリー ===")
    success_count = sum(results.values())
    total_count = len(results)

    for test_name, success in results.items():
        status = "✓" if success else "✗"
        logger.info(f"{status} {test_name}")

    logger.info(f"\n成功: {success_count}/{total_count}")

    if success_count == total_count:
        logger.info("全てのテストが成功しました！")
    else:
        logger.warning("一部のテストが失敗しました")

    return bool(success_count == total_count)


if __name__ == "__main__":
    run_integration_tests()
