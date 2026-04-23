import uuid

from aws_lambda_powertools import Logger

from app.adapters.data_save_exception import DataSaveException
from app.domain.model.ai_chat.ai_user_profile import AIUserProfile
from app.domain.model.user.ai_profile_request import AIUserProfileRequestCreate


class CreateAIProfileUseCase:
    logger = Logger()

    def __init__(self, unit_of_work):
        self.unit_of_work = unit_of_work

    def execute(self, req: AIUserProfileRequestCreate) -> AIUserProfile:

        new_ai_user_profile = AIUserProfile(
            id=str(uuid.uuid4()),
            line_user_id="",
            name=req.name,
            gender=req.gender,
            age=req.age,
            region=req.region,
            region_cd=req.region_cd,
            lines=req.lines,
            interest_topics=req.interest_topics,
        )

        try:
            with self.unit_of_work:
                self.unit_of_work.ai_user_profile.add(new_ai_user_profile)
                self.unit_of_work.commit()
                self.logger.info(
                    "Created new AI User Profile with ID: %s", new_ai_user_profile.id
                )
            return new_ai_user_profile

        except Exception as e:
            raise DataSaveException("保存に失敗しました") from e
