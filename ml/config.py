"""
MLサービス用設定管理
"""

import os
from pathlib import Path

# ml/.envファイルを読み込み
from dotenv import load_dotenv

# ml/ディレクトリの.envファイルを読み込み
ml_dir = Path(__file__).parent
env_path = ml_dir / ".env"
load_dotenv(env_path)


class Config:
    """MLサービス設定クラス"""

    # データベース設定
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/congestion_watch"
    )

    # MLサービス設定
    ML_PORT: int = int(os.getenv("ML_PORT", "8001"))
    ENV: str = os.getenv("ENV", "development")
    AUTO_START_SCHEDULER: bool = (
        os.getenv("AUTO_START_SCHEDULER", "true").lower() == "true"
    )

    # ログ設定
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # モデル設定
    MODEL_DIR: str = os.getenv("MODEL_DIR", "models")
    MODEL_RETRAIN_HOUR: int = int(os.getenv("MODEL_RETRAIN_HOUR", "12"))
    PREDICTION_INTERVAL_MINUTES: int = int(
        os.getenv("PREDICTION_INTERVAL_MINUTES", "5")
    )

    # テスト用設定
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "sqlite:///test.db")

    @classmethod
    def get_database_url(cls, for_test: bool = False) -> str:
        """データベースURLを取得"""
        if for_test:
            return cls.TEST_DATABASE_URL
        return cls.DATABASE_URL

    @classmethod
    def is_development(cls) -> bool:
        """開発環境かどうか"""
        return cls.ENV == "development"

    @classmethod
    def is_production(cls) -> bool:
        """本番環境かどうか"""
        return cls.ENV == "production"


# グローバル設定インスタンス
config = Config()
