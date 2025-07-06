"""
MLサービス用設定管理
"""

import os
from pathlib import Path

# ml/.envファイルを読み込み
from dotenv import load_dotenv

# ml/ディレクトリの.envファイルを読み込み（src/から見て1つ上のディレクトリ）
ml_dir = Path(__file__).parent.parent
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

    # ログ設定
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # モデル設定
    MODEL_DIR: str = os.getenv("MODEL_DIR", "models")


    @classmethod
    def get_database_url(cls) -> str:
        """データベースURLを取得"""
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
