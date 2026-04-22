import json
from typing import Optional

from aws_lambda_powertools import Logger

from app.application.user.user_profile_fetcher import get_profile
from app.application.user.verify_access_token import verify_access_token
from app.domain.model.user.exist_user_result import ExistUserResult


class ExistLineUserUseCase:
    logger = Logger()

    def __init__(self, ai_user_profiles_query_service):
        self.ai_user_profiles_query_service = ai_user_profiles_query_service

    def extract_access_token(self, body: str) -> Optional[str]:
        """リクエストボディからアクセストークンを取得する"""
        doc = json.loads(body)
        access_token = doc.get("accessToken")

        if access_token:
            return access_token

        self.logger.warning("有効なアクセストークンが見つからないか、無効な値です。")
        return None

    def extract_user_id(self, req_body: str) -> Optional[str]:
        """アクセストークンから LINE の user_Id を取得する"""
        accessToken = self.extract_access_token(req_body)
        if not accessToken:
            self.logger.warning("アクセストークンの取得に失敗しました。")
            return None

        access_token_result = verify_access_token(accessToken)
        if not access_token_result:
            self.logger.warning("アクセストークンの検証に失敗しました。")
            return None

        user_profile_result = get_profile(accessToken)
        if not user_profile_result:
            self.logger.warning("ユーザープロファイルの取得に失敗しました。")
            return None

        return user_profile_result.user_id

    def execute(self, req_body: str) -> Optional[ExistUserResult]:
        try:
            user_id = self.extract_user_id(req_body)
            if not user_id:
                return None

            ai_user_profile = (
                self.ai_user_profiles_query_service.get_ai_user_profile_by_line_user_id(
                    user_id
                )
            )

            # 存在しない場合
            if not ai_user_profile:
                return ExistUserResult(
                    is_exist=False,
                    user_profile_id=None,
                    name=None,
                    gender=None,
                    age=None,
                    region=None,
                    region_cd=None,
                    lines=None,
                    interest_topics=None,
                )

            # 存在する場合
            return ExistUserResult(
                is_exist=True,
                user_profile_id=ai_user_profile.get("id"),
                name=ai_user_profile.get("name"),
                gender=ai_user_profile.get("gender"),
                age=ai_user_profile.get("age"),
                region=ai_user_profile.get("region"),
                region_cd=ai_user_profile.get("region_cd"),
                lines=ai_user_profile.get("lines"),
                interest_topics=ai_user_profile.get("interest_topics"),
            )

        except Exception as e:
            self.logger.exception(e, "DynamoDBエラー")
            return None
