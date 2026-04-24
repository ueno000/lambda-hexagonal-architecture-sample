import sys
import types
import unittest
from dataclasses import dataclass
from unittest.mock import patch


@dataclass
class AIUserProfile:
    id: str
    line_user_id: str
    name: str = None
    gender: str = None
    age: str = None
    region: str = None
    region_cd: str = None
    lines: list | None = None
    interest_topics: list | None = None


sys.modules["app.application.ai_chat.get_wether"] = types.SimpleNamespace(
    get_wether=lambda region_code: ""
)
fake_ai_chat_package = types.ModuleType("app.domain.model.ai_chat")
fake_ai_user_profile_module = types.ModuleType(
    "app.domain.model.ai_chat.ai_user_profile"
)
fake_ai_chat_package.AIUserProfile = AIUserProfile
fake_ai_user_profile_module.AIUserProfile = AIUserProfile
sys.modules["app.domain.model.ai_chat"] = fake_ai_chat_package
sys.modules["app.domain.model.ai_chat.ai_user_profile"] = fake_ai_user_profile_module

from app.application.ai_chat.prompt_builder import (
    _build_line_queries,
    _build_topic_queries,
    _format_list,
    _normalize_list,
    build_daily_guide_prompt,
)


class PromptBuilderTests(unittest.TestCase):
    """prompt_builder モジュールのテストケース"""

    def _make_ai_user_profile(
        self,
        name="太郎",
        gender="男性",
        age="10代",
        interest_topics=None,
        region="東京都",
        region_code="130000",
        lines=None,
    ):
        """テスト用の AIUserProfile を生成"""
        return AIUserProfile(
            id="user-1",
            line_user_id="line-user-1",
            name=name,
            gender=gender,
            age=age,
            interest_topics=interest_topics or [],
            region=region,
            region_cd=region_code,
            lines=lines or [],
        )

    @patch(
        "app.application.ai_chat.prompt_builder.get_wether",
        return_value="天気:130000",
    )
    def test_build_daily_guide_prompt_with_full_profile(self, mock_get_wether):
        """すべてのフィールドが設定されている場合のプロンプト構築"""
        profile = self._make_ai_user_profile(
            name="太郎",
            gender="男性",
            age="30代",
            interest_topics=["グルメ", "イベント"],
            region="東京都",
            region_code="130000",
            lines=["山手線", "中央線"],
        )

        prompt = build_daily_guide_prompt(profile)

        self.assertIn("役割定義", prompt)
        self.assertIn("太郎", prompt)
        self.assertIn("30代", prompt)
        self.assertIn("男性", prompt)
        self.assertIn("グルメ、イベント", prompt)
        self.assertIn("東京都", prompt)
        self.assertIn("山手線", prompt)
        self.assertIn("天気:130000", prompt)
        mock_get_wether.assert_called_once_with("130000")

    @patch(
        "app.application.ai_chat.prompt_builder.get_wether",
        return_value="天気:130000",
    )
    def test_build_daily_guide_prompt_with_none_optional_fields(self, mock_get_wether):
        """オプショナルフィールドが None の場合"""
        profile = self._make_ai_user_profile(
            name=None,
            gender=None,
            age=None,
            region=None,
        )

        prompt = build_daily_guide_prompt(profile)

        self.assertIn("- 名前: None", prompt)
        self.assertIn("- 年代: None", prompt)
        self.assertIn("- 性別: None", prompt)
        self.assertIn("東京都", prompt)
        self.assertIn("OutputFormat", prompt)
        mock_get_wether.assert_called_once_with("130000")

    @patch(
        "app.application.ai_chat.prompt_builder.get_wether",
        return_value="天気:130000",
    )
    def test_build_daily_guide_prompt_with_empty_lists(self, mock_get_wether):
        """リストフィールドが空の場合"""
        profile = self._make_ai_user_profile(
            interest_topics=[],
            lines=[],
        )

        prompt = build_daily_guide_prompt(profile)

        self.assertIn("未設定", prompt)
        self.assertIn("路線未設定の為、検索不要", prompt)
        mock_get_wether.assert_called_once_with("130000")

    @patch(
        "app.application.ai_chat.prompt_builder.get_wether",
        return_value="天気:130000",
    )
    def test_build_daily_guide_prompt_includes_timestamp(self, mock_get_wether):
        """プロンプトにタイムスタンプが含まれる"""
        profile = self._make_ai_user_profile()

        prompt = build_daily_guide_prompt(profile)

        # YYYY/MM/DD HH:MM形式のタイムスタンプが含まれることを確認
        self.assertRegex(prompt, r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}")
        mock_get_wether.assert_called_once_with("130000")

    def test_build_line_queries_with_empty_list(self):
        """路線リストが空の場合"""
        result = _build_line_queries([])
        self.assertEqual(result, "「路線未設定の為、検索不要」")

    def test_build_line_queries_with_single_line(self):
        """1件の路線"""
        result = _build_line_queries(["11302"])
        self.assertEqual(result, "「JR東日本 JR山手線 運行情報」")

    def test_build_line_queries_with_multiple_lines(self):
        """複数の路線"""
        result = _build_line_queries(["1004", "11302"])
        self.assertEqual(
            result,
            "「JR東日本 東北新幹線 運行情報」「JR東日本 JR山手線 運行情報」",
        )

    def test_build_topic_queries_with_empty_list(self):
        """トピックリストが空の場合、ランダムに3件設定"""
        result = _build_topic_queries([])
        self.assertEqual(result.count("「"), 3)

    def test_build_topic_queries_with_3_topics(self):
        """3件のトピック"""
        topics = ["1001", "1002", "1003"]
        result = _build_topic_queries(topics)
        # 3件以下なので全件が含まれる
        self.assertIn("グルメ", result)
        self.assertIn("料理", result)
        self.assertIn("カフェ", result)
        self.assertEqual(result.count("「"), 3)

    def test_format_list_with_empty_list(self):
        """空のリスト"""
        result = _format_list([])
        self.assertEqual(result, "未設定")

    def test_format_list_with_single_item(self):
        """1件のリスト"""
        result = _format_list(["東京"])
        self.assertEqual(result, "東京")

    def test_format_list_with_multiple_items(self):
        """複数件のリスト"""
        result = _format_list(["東京", "大阪", "京都"])
        self.assertEqual(result, "東京、大阪、京都")

    def test_normalize_list_with_none(self):
        """None の値"""
        result = _normalize_list(None)
        self.assertEqual(result, [])

    def test_normalize_list_with_empty_list(self):
        """空のリスト"""
        result = _normalize_list([])
        self.assertEqual(result, [])

    def test_normalize_list_with_list(self):
        """リスト形式"""
        result = _normalize_list(["東京", "大阪"])
        self.assertEqual(result, ["東京", "大阪"])

    def test_normalize_list_with_string(self):
        """文字列形式"""
        result = _normalize_list("東京")
        self.assertEqual(result, ["東京"])

    def test_normalize_list_filters_empty_strings(self):
        """空文字列はフィルタリング"""
        result = _normalize_list(["東京", "", "大阪"])
        self.assertEqual(result, ["東京", "大阪"])

    def test_normalize_list_with_mixed_types(self):
        """混合型のリスト"""
        result = _normalize_list([1, "東京", 3])
        self.assertEqual(result, ["1", "東京", "3"])


if __name__ == "__main__":
    unittest.main()
