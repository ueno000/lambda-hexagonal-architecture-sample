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

            data = self.ai_user_profiles_query_service.get_ai_user_profile_by_id(req.id)

            if not data:
                raise ValueError("対象データが存在しません")

            req_data = req.model_dump(exclude_none=True, exclude={"id"})
            current_data = data if isinstance(data, dict) else data.model_dump()
            merged_data = {**current_data, **req_data, "id": req.id}
            merged_data.setdefault("character_type", 0)

            ai_user_profile = AIUserProfile(**merged_data)

            with self.unit_of_work:
                self.unit_of_work.ai_user_profile.update(ai_user_profile)
                self.unit_of_work.commit()

            return ai_user_profile

        except Exception as e:
            raise DataSaveException("保存に失敗しました") from e
