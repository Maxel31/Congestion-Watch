"""
データベース接続設定モジュール
作成日: 2025-06-25
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """データベース設定クラス"""

    host: str
    port: int
    user: str
    password: str
    database: str

    @property
    def connection_string(self) -> str:
        """PostgreSQLの接続文字列を生成"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def asyncpg_dsn(self) -> str:
        """asyncpg用のDSNを生成"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def psycopg2_dsn(self) -> str:
        """psycopg2用のDSNを生成"""
        return f"host={self.host} port={self.port} user={self.user} password={self.password} dbname={self.database}"


def get_database_config() -> DatabaseConfig:
    """
    環境変数からデータベース設定を読み込む

    Returns:
        DatabaseConfig: データベース設定オブジェクト
    """
    return DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "congestion_user"),
        password=os.getenv("POSTGRES_PASSWORD", "secure_password"),
        database=os.getenv("POSTGRES_DB", "congestion_watch"),
    )


def get_test_database_config() -> DatabaseConfig:
    """
    テスト用データベース設定を取得

    Returns:
        DatabaseConfig: テスト用データベース設定オブジェクト
    """
    config = get_database_config()
    # テスト用データベース名に変更
    config.database = f"{config.database}_test"
    return config


class DatabaseConnectionManager:
    """データベース接続管理クラス"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or get_database_config()

    def get_connection_string(self) -> str:
        """接続文字列を取得"""
        return self.config.connection_string

    def get_asyncpg_dsn(self) -> str:
        """asyncpg用DSNを取得"""
        return self.config.asyncpg_dsn

    def get_psycopg2_dsn(self) -> str:
        """psycopg2用DSNを取得"""
        return self.config.psycopg2_dsn
