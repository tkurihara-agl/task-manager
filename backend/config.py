# ============================================================
# config.py - アプリケーション設定
# ============================================================
# 秘密情報はコードに一切書かない。
#
# 設定値の取得順:
#   1. USE_PARAMETER_STORE=true の場合 → AWS Parameter Store から取得
#   2. それ以外 → 環境変数（.env ファイルまたはOS環境変数）から取得
#   3. 必須値が見つからなければ起動時にエラー
#
# ローカル開発:
#   .env ファイルに DB_PASSWORD などを書く（.gitignore 済み）
#
# 本番（AWS EC2）:
#   USE_PARAMETER_STORE=true を設定
#   Parameter Store に /taskmanager/prod/DB_PASSWORD などを保存
#   EC2 に IAM ロール（ssm:GetParameter 権限）をアタッチ

import os
from dotenv import load_dotenv

# ----------------------------------------------------------------
# .env ファイルを読み込む（ファイルがなければ何もしない）
# ----------------------------------------------------------------
load_dotenv()


# ----------------------------------------------------------------
# Parameter Store からの値取得（本番のみ）
# ----------------------------------------------------------------
USE_PARAMETER_STORE = os.getenv("USE_PARAMETER_STORE", "false").lower() == "true"

if USE_PARAMETER_STORE:
    import boto3

    AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
    PARAM_PREFIX = os.getenv("PARAM_STORE_PREFIX", "/taskmanager/prod")

    ssm_client = boto3.client("ssm", region_name=AWS_REGION)

    def _fetch_from_ssm(param_name: str) -> str | None:
        """Parameter Storeから値を取得する（見つからなければNone）"""
        try:
            response = ssm_client.get_parameter(
                Name=f"{PARAM_PREFIX}/{param_name}",
                WithDecryption=True,  # SecureStringを復号する
            )
            return response["Parameter"]["Value"]
        except Exception:
            return None

    # 対象の環境変数を Parameter Store の値で上書きする
    _SSM_KEYS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD", "SECRET_KEY"]
    for key in _SSM_KEYS:
        value = _fetch_from_ssm(key)
        if value is not None:
            os.environ[key] = value


# ----------------------------------------------------------------
# 必須値のチェック（見つからなければ起動時にエラー）
# ----------------------------------------------------------------
def _require(key: str) -> str:
    """必須の環境変数を取得する。なければ例外を投げる"""
    value = os.environ.get(key)
    if not value:
        raise ValueError(
            f"必須の環境変数 '{key}' が設定されていません。\n"
            f"ローカル開発: .env ファイルに記載してください。\n"
            f"本番: Parameter Store に /taskmanager/prod/{key} を設定してください。"
        )
    return value


# ----------------------------------------------------------------
# データベース接続
# ----------------------------------------------------------------
DB_HOST = _require("DB_HOST")
DB_PORT = _require("DB_PORT")
DB_NAME = _require("DB_NAME")
DB_USER = _require("DB_USER")
DB_PASSWORD = _require("DB_PASSWORD")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# ----------------------------------------------------------------
# 認証設定
# ----------------------------------------------------------------
SECRET_KEY = _require("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


# ----------------------------------------------------------------
# アプリ設定
# ----------------------------------------------------------------
TASK_STATUSES = ["todo", "in_progress", "done"]
TASK_PRIORITIES = ["low", "medium", "high"]
