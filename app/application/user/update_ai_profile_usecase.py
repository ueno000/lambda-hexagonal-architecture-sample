from aws_lambda_powertools import Logger

from app.adapters.data_save_exception import DataSaveException
from app.domain.model.ai_chat.ai_user_profile import AIUserProfile
from app.domain.model.user.ai_profile_request import AIUserProfileRequestUpdate


class UpdateAIProfileUseCase:
    logger = Logger()

    def __init__(self, unit_of_work, ai_user_profiles_query_service):
        self.unit_of_work = unit_of_work
        self.ai_user_profiles_query_service = ai_user_profiles_query_service

    def execute(self, req: AIUserProfileRequestUpdate) -> AIUserProfile:

        try:
            if not req.id:
                self.logger.error(f"AIUserProfileId:{req.id} が存在しません。")
                raise ValueError("idは必須です")

            data = self.ai_user_profiles_query_service.get_by_id(req.id)

            if not data:
                raise ValueError("対象データが存在しません")

            req_data = req.model_dump(exclude_none=True, exclude={"id"})

            ai_user_profile = AIUserProfile(
                id=req.id, line_user_id=data.line_user_id, **req_data
            )

            with self.unit_of_work:
                self.unit_of_work.ai_user_profile.update(ai_user_profile)
                self.unit_of_work.commit()

            return ai_user_profile

        except Exception as e:
            raise DataSaveException("保存に失敗しました") from e
