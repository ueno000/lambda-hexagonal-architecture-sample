import unittest
from unittest.mock import patch
from datetime import datetime

from app.domain.model.ai_chat.ai_user_profile import AIUserProfile
from app.application.ai_chat.prompt_builder import (
    build_daily_guide_prompt,
    _build_line_queries,
    _build_topic_queries,
    _to_age_decade,
    _format_list,
    _normalize_list,
)


class PromptBuilderTests(unittest.TestCase):
    """prompt_builder モジュールのテストケース"""

    def _make_ai_user_profile(
        self,
        name="太郎",
        gender="男性",
        birth_year=1990,
        interest_topics=None,
        residence="東京都",
        lines=None,
    ):
        """テスト用の AIUserProfile を生成"""
        return AIUserProfile(
            id="user-1",
            line_user_id="line-user-1",
            name=name,
            gender=gender,
            birth_year=birth_year,
            interest_topics=interest_topics or [],
            residence=residence,
            lines=lines or [],
        )

    def test_build_daily_guide_prompt_with_full_profile(self):
        """すべてのフィールドが設定されている場合のプロンプト構築"""
        profile = self._make_ai_user_profile(
            name="太郎",
            gender="男性",
            birth_year=1990,
            interest_topics=["グルメ", "イベント"],
            residence="東京都",
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

    def test_build_daily_guide_prompt_with_none_optional_fields(self):
        """オプショナルフィールドが None の場合"""
        profile = self._make_ai_user_profile(
            name=None,
            gender=None,
            birth_year=None,
            residence=None,
        )

        prompt = build_daily_guide_prompt(profile)

        self.assertIn("未設定", prompt)
        self.assertIn("OutputFormat", prompt)

    def test_build_daily_guide_prompt_with_empty_lists(self):
        """リストフィールドが空の場合"""
        profile = self._make_ai_user_profile(
            interest_topics=[],
            lines=[],
        )

        prompt = build_daily_guide_prompt(profile)

        self.assertIn("未設定", prompt)
        self.assertIn("路線未設定の為、検索不要", prompt)

    def test_build_daily_guide_prompt_includes_timestamp(self):
        """プロンプトにタイムスタンプが含まれる"""
        profile = self._make_ai_user_profile()

        prompt = build_daily_guide_prompt(profile)

        # YYYY/MM/DD HH:MM形式のタイムスタンプが含まれることを確認
        self.assertRegex(prompt, r"\d{4}/\d{2}/\d{2} \d{2}:\d{2}")

    def test_build_line_queries_with_empty_list(self):
        """路線リストが空の場合"""
        result = _build_line_queries([])
        self.assertEqual(result, "「路線未設定の為、検索不要」")

    def test_build_line_queries_with_single_line(self):
        """1件の路線"""
        result = _build_line_queries(["山手線"])
        self.assertEqual(result, "「山手線 運行情報」")

    def test_build_line_queries_with_multiple_lines(self):
        """複数の路線"""
        result = _build_line_queries(["山手線", "中央線", "丸ノ内線"])
        self.assertEqual(
            result, "「山手線 運行情報」「中央線 運行情報」「丸ノ内線 運行情報」"
        )

    def test_build_line_queries_with_max_5_lines(self):
        """5件を超える路線は5件まで"""
        lines = ["線1", "線2", "線3", "線4", "線5", "線6"]
        result = _build_line_queries(lines)
        self.assertEqual(
            result,
            "「線1 運行情報」「線2 運行情報」「線3 運行情報」「線4 運行情報」「線5 運行情報」",
        )

    def test_build_topic_queries_with_empty_list(self):
        """トピックリストが空の場合"""
        result = _build_topic_queries([])
        self.assertEqual(result, "「未設定 最新」")

    def test_build_topic_queries_with_3_topics(self):
        """3件のトピック"""
        topics = ["グルメ", "イベント", "映画"]
        result = _build_topic_queries(topics)
        # 3件以下なので全件が含まれる
        self.assertIn("グルメ", result)
        self.assertIn("イベント", result)
        self.assertIn("映画", result)
        self.assertEqual(result.count("「"), 3)

    @patch("app.application.ai_chat.prompt_builder.random.sample")
    def test_build_topic_queries_with_4_topics(self, mock_sample):
        """4件のトピックはランダムに3件を抽出"""
        topics = ["グルメ", "イベント", "映画", "スポーツ"]
        mock_sample.return_value = ["グルメ", "映画", "イベント"]

        result = _build_topic_queries(topics)

        # ランダム抽出が呼ばれたことを確認
        mock_sample.assert_called_once_with(topics, 3)
        self.assertEqual(result.count("「"), 3)

    @patch("app.application.ai_chat.prompt_builder.random.sample")
    def test_build_topic_queries_with_5_topics(self, mock_sample):
        """5件のトピックはランダムに3件を抽出"""
        topics = ["グルメ", "イベント", "映画", "スポーツ", "音楽"]
        mock_sample.return_value = ["グルメ", "スポーツ", "音楽"]

        result = _build_topic_queries(topics)

        # ランダム抽出が呼ばれたことを確認
        mock_sample.assert_called_once_with(topics, 3)
        self.assertEqual(result.count("「"), 3)

    def test_to_age_decade_with_valid_birth_year(self):
        """有効な生年から年代を計算"""
        # 2026 - 1990 = 36歳 → 30代
        with patch("app.application.ai_chat.prompt_builder.datetime") as mock_datetime:
            mock_datetime.now.return_value.year = 2026
            result = _to_age_decade(1990)
            self.assertEqual(result, "30代")

    def test_to_age_decade_with_none(self):
        """生年が None の場合"""
        result = _to_age_decade(None)
        self.assertEqual(result, "未設定")

    def test_to_age_decade_with_negative_age(self):
        """生年が未来の場合（負の年齢）"""
        with patch("app.application.ai_chat.prompt_builder.datetime") as mock_datetime:
            mock_datetime.now.return_value.year = 2026
            result = _to_age_decade(2030)
            self.assertEqual(result, "未設定")

    def test_to_age_decade_with_invalid_type(self):
        """生年が無効な型の場合"""
        result = _to_age_decade("invalid")
        self.assertEqual(result, "未設定")

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
