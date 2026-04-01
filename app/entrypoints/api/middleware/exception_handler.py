import json
import os
from http.client import BAD_REQUEST, INTERNAL_SERVER_ERROR

from aws_lambda_powertools import logging
from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

# ロガーを初期化（環境変数 LOG_LEVEL で制御、デフォルトは INFO）
logger = logging.Logger(level=os.environ.get("LOG_LEVEL", "INFO"))


@lambda_handler_decorator
def handle_exceptions(handler, event, context, user_exceptions, cors_config):
    """
    Lambda ハンドラーの例外処理ミドルウェア

    ドメイン例外（ユーザー入力エラー）と予期しない例外を分離して処理

    Args:
        handler: ラップするハンドラー関数
        event: Lambda イベント
        context: Lambda コンテキスト
        user_exceptions: ドメイン例外のタプル（400エラーとして返す）
        cors_config: CORS ヘッダー設定

    Returns:
        API Gateway レスポンス形式の辞書
    """
    try:
        # メインの処理を実行
        return handler(event, context)
    except Exception as e:
        # ドメイン例外（ビジネスロジック上の予期された例外）を捕捉
        if isinstance(e, tuple(user_exceptions)):
            # ドメイン例外をログに出力
            logger.exception("User exception.")
            # 400 Bad Request で応答（クライアント側の入力エラー）
            return {
                "statusCode": BAD_REQUEST,
                "headers": cors_config.to_dict(origin="*"),
                "body": json.dumps({"message": str(e)}),
                "isBase64Encoded": False,
            }
        else:
            # 予期しない例外をログに出力
            logger.exception("Unhandled exception.")
            # 500 Internal Server Error で応答（サーバー側エラー）
            return {
                "statusCode": INTERNAL_SERVER_ERROR,
                "headers": cors_config.to_dict(origin="*"),
                "body": json.dumps({"message": "Internal server error."}),
                "isBase64Encoded": False,
            }
