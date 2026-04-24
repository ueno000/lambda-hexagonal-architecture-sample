import json
from typing import Optional

from aws_lambda_powertools import Logger

from app.application.user.userinfo_fetcher import get_info
from app.application.user.verify_access_token import verify_access_token
from app.domain.model.user.exist_user_result import ExistUserResult


class ExistLineUserUseCase:
    logger = Logger()

    def __init__(self, line_users_query_service, ai_user_profiles_query_service):
        self.line_users_query_service = line_users_query_service
        self.ai_user_profiles_query_service = ai_user_profiles_query_service

    def extract_access_token(self, body: str) -> Optional[str]:
        self.logger.info(f"raw body: {body}")

        try:
            doc = json.loads(body)
        except Exception as e:
            self.logger.error(f"json parse error: {e}")
            return None

        self.logger.info(f"parsed body: {doc}")

        access_token = doc.get("accessToken")

        if access_token:
            self.logger.info("accessToken取得成功")
            return access_token

        self.logger.warning("accessTokenが存在しない")
        return None

    def extract_user_id(self, req_body: str) -> Optional[str]:
        self.logger.info("extract_user_id start")

        accessToken = self.extract_access_token(req_body)
        if not accessToken:
            self.logger.warning("アクセストークン取得失敗")
            return None

        self.logger.info("アクセストークン取得成功")

        access_token_result = verify_access_token(accessToken)
        if not access_token_result:
            self.logger.warning("トークン検証失敗")
            return None

        self.logger.info("トークン検証成功")

        user_info_result = get_info(accessToken)
        if not user_info_result:
            self.logger.warning("プロフィール取得失敗")
            return None

        self.logger.info(f"プロフィール取得成功 user_id取得成功: {user_info_result}")

        return user_info_result.sub

    def execute(self, req_body: str) -> Optional[ExistUserResult]:
        try:
            user_id = self.extract_user_id(req_body)
            if not user_id:
                self.logger.warning("useridの取得に失敗しました。")
                return None

            line_user = self.line_users_query_service.get_line_user_by_line_id(user_id)
            if not line_user:
                self.logger.info(f"LINEUser:{user_id} は存在しません。")

            self.logger.info(f"LINEUser:{user_id} 取得成功 {line_user}")

            ai_user_profile = (
                self.ai_user_profiles_query_service.get_ai_user_profile_by_line_user_id(
                    line_user.id
                )
            )

            # AIUserProfileが存在しない場合
            if not ai_user_profile:
                self.logger.info(f"AIUserProfile:{line_user.id} は存在しません。")
                return ExistUserResult(
                    is_exist=False,
                    line_user_id=line_user.id,
                    user_profile_id=None,
                    name=None,
                    gender=None,
                    age=None,
                    region=None,
                    region_cd=None,
                    lines=None,
                    interest_topics=None,
                )

            # AIUserProfileが存在する場合
            return ExistUserResult(
                is_exist=True,
                line_user_id=line_user.id,
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
