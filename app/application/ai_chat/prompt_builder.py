from datetime import datetime
from typing import Any
import random

from app.domain.model.ai_chat.ai_user_profile import AIUserProfile

# プロンプトテンプレート定数
ROLE_DEFINITION = "# 役割定義 \
    あなたは「情報収集」と「応援メッセージ生成」を行う朝情報アシスタントです。\
    まず事実ベースで情報収集し、その後に取得情報を用いて応援メッセージを生成してください。"

OUTPUT_FORMAT = (
    "# OutputFormat\n"
    "{{\n"
    '  "timestamp": "{timestamp}",\n'
    '  "train": [{{"line": "", "status": "", "source_url": ""}}],\n'
    '  "news": [{{"title": "", "source_url": ""}}, {{"title": "", "source_url": ""}}, {{"title": "", "source_url": ""}}],\n'
    '  "topics": [{{"type": "interest_topic", "title": "", "source_url": ""}}],\n'
    '  "message": ""\n'
    "}}"
)

ABSOLUTE_RULES = (
    "# 絶対ルール\n"
    "- 必ず検索を実行し、検索結果に含まれる情報のみ使用すること。\n"
    "- URLは検索結果に含まれるもののみ使用し、生成・補完は禁止。\n"
    "- 情報が確認できない場合は「情報が取得できませんでした」と明示すること。\n"
    "- 古い情報は禁止（可能な限り直近48時間〜当日の情報を優先）。\n"
    "- 公式サイト・大手メディア（例：鉄道会社、気象サービス、主要報道機関）を最優先すること。\n"
    "- 同一項目で複数ソースがある場合は、最も信頼性が高いものを1つ選択すること。"
)

USER_PROFILE_TEMPLATE = (
    "# User Profile\n"
    "- 名前: {name}\n"
    "- 年代: {age_decade}\n"
    "- 性別: {gender}\n"
    "- 関心トピック: {interest_topics}\n"
    "- 居住地: {residence}\n"
    "- お気に入り路線: {lines}"
)

SEARCH_QUERY_TEMPLATE = (
    "# 検索クエリ\n"
    "以下のクエリで検索し、最上位の信頼できる情報を使用すること。\n"
    "【運行情報】 {line_queries}\n"
    "【最新ニュース】 「最新ニュース 日本」\n"
    "【関心トピック】 {topic_queries}"
)

DATA_EXTRACTION_RULES = (
    "# データ抽出ルール\n"
    "【運行情報】\n"
    "  - 「平常運転」「遅延」「運転見合わせ」など公式表現をそのまま使用\n"
    "  - 不明な場合は必ず「情報が取得できませんでした」\n"
    "【ニュース】\n"
    "  - 日本の主要ニュースを3件\n"
    "  - タイトルは改変せず、検索結果の見出しをそのまま使用\n"
    "【関心トピック】\n"
    "  - 各トピックにつき1件ずつ取得\n"
    "  - 最新性・話題性を優先"
)

OUTPUT_CONSTRAINTS = (
    "# 補足\n"
    "【可変長リスト】\n"
    '  - "train": お気に入り路線の数に応じて出力（順序固定）\n'
    '  - "topics": 関心トピックの中から3件出力（順序固定）\n'
    "【出力制約】\n"
    "  - JSONのみ出力（説明文・補足・コードブロック禁止）\n"
    "  - キー名・構造は完全一致\n"
    "  - 空欄は禁止（不明時は「情報が取得できませんでした」）"
)

MESSAGE_RULES = (
    "# Message Rules\n"
    "- 500文字以内\n"
    "- User Profile / 天気 / train / news / topics を自然に織り込む\n"
    "- 事実部分は検索結果のみ使用\n"
    "- 応援表現のみ創作可\n"
    "- キャラクター設定を反映する\n"
    "- 過度なポエム調禁止\n"
    "- 朝に読むことを想定した簡潔な文章にする\n"
)

CHARACTER = (
    "# Character\n"
    "- 高校2年生の女の子\n"
    "- ギャル\n"
    "- 明るく元気\n"
    "- ちょっとおせっかい\n"
    "- 情報通で好奇心旺盛\n"
    "- 友達思いで優しい\n"
)


def build_daily_guide_prompt(ai_user_profile: AIUserProfile) -> str:
    """AIユーザープロフィールに基づいて日次ガイドプロンプトを構築します。

    Args:
        ai_user_profile: AIUserProfileモデルのインスタンス

    Returns:
        構築されたプロンプト文字列
    """
    # ユーザー情報の抽出と正規化
    name = ai_user_profile.name
    age_decade = _to_age_decade(ai_user_profile.birth_year)
    gender = ai_user_profile.gender or "未設定"
    residence = ai_user_profile.residence or "未設定"

    # リスト形式のデータを正規化
    interest_topics_list = _normalize_list(ai_user_profile.interest_topics)
    lines_list = _normalize_list(ai_user_profile.lines)

    # 表示用フォーマット
    interest_topics = _format_list(interest_topics_list)
    lines = _format_list(lines_list)

    # 天気の情報は先に取得してプロンプトに組み込む
    wether_info = "# 本日の天気 晴れたり曇ったり 昼間は暖かい 今日は晴れたり曇ったり、穏やかな天気。ただ、多摩エリアでは夕方以降ににわか雨が心配です。昼間は暖かく感じられそう。朝晩と昼間の体感差が大きくなるため、服装で上手に調節をしてください。"

    # 検索クエリの構築
    line_queries = _build_line_queries(lines_list)
    topic_queries = _build_topic_queries(interest_topics_list)

    # タイムスタンプ
    timestamp = datetime.now().strftime("%Y/%m/%d %H:%M")

    # OUTPUT_FORMAT をまず format() で処理してから f-string に組み込む
    output_format = OUTPUT_FORMAT.format(timestamp=timestamp)

    # プロンプトの構築
    prompt = (
        f"{ROLE_DEFINITION}\n\n"
        f"{output_format}\n\n"
        f"{ABSOLUTE_RULES}\n\n"
        f"{USER_PROFILE_TEMPLATE.format(name=name, age_decade=age_decade, gender=gender, interest_topics=interest_topics, residence=residence, lines=lines)}\n\n"
        f"{wether_info}\n\n"
        f"{SEARCH_QUERY_TEMPLATE.format(residence=residence, line_queries=line_queries, topic_queries=topic_queries)}\n\n"
        f"{DATA_EXTRACTION_RULES}\n\n"
        f"{OUTPUT_CONSTRAINTS}"
        f"{MESSAGE_RULES}\n\n"
        f"{CHARACTER}"
    )
    return prompt


def _build_line_queries(lines_list: list[str]) -> str:
    """配列が空の場合は「未設定」と表示し、クエリも「未設定」で検索しないようにします。

    Args:
        lines_list: 路線リスト

    Returns:
        フォーマットされた検索クエリ文字列
    """
    if not lines_list:
        return "「路線未設定の為、検索不要」"
    return "".join(f"「{line} 運行情報」" for line in lines_list[:5])


def _build_topic_queries(topics_list: list[str]) -> str:
    """トピックは3件までを検索クエリに含めます。4件以上ある場合はランダムに3件を抽出します。

    Args:
        topics_list: トピックリスト（3〜5件）

    Returns:
        フォーマットされた検索クエリ文字列
    """
    if not topics_list:
        return "「未設定 最新」"

    # 4件以上の場合はランダムに3件を抽出、3件以下の場合はそのまま使用
    selected_topics = random.sample(topics_list, min(3, len(topics_list)))
    return "".join(f"「{topic} 最新」" for topic in selected_topics)


def _to_age_decade(birth_year: Any) -> str:
    """生年から年代表記を生成します。

    Args:
        birth_year: 生年

    Returns:
        年代表記文字列（例：「30代」、「未設定」）
    """
    if not birth_year:
        return "未設定"

    try:
        current_year = datetime.now().year
        age = current_year - int(birth_year)
        if age < 0:
            return "未設定"
        return f"{(age // 10) * 10}代"
    except (ValueError, TypeError):
        return "未設定"


def _format_list(value: list[str]) -> str:
    """リストを表示用の文字列にフォーマットします。

    Args:
        value: リスト

    Returns:
        「、」で結合された文字列、または「未設定」
    """
    if not value:
        return "未設定"
    return "、".join(value)


def _normalize_list(value: Any) -> list[str]:
    """値をリスト形式に正規化します。

    Args:
        value: 任意の値（リスト、文字列、None等）

    Returns:
        正規化されたリスト
    """
    if not value:
        return []

    if isinstance(value, list):
        return [str(item) for item in value if item]

    return [str(value)]
