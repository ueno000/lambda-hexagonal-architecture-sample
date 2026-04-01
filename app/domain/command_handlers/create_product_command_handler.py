import uuid
from datetime import datetime, timezone

from app.domain.commands import create_product_command
from app.domain.model import product
from app.domain.ports import unit_of_work


def handle_create_product_command(
    command: create_product_command.CreateProductCommand,
    unit_of_work: unit_of_work.UnitOfWork,
) -> str:
    """
    商品作成コマンドを処理する関数

    Args:
        command: 商品作成コマンド（name, descriptionを含む）
        unit_of_work: DynamoDBのトランザクション管理オブジェクト

    Returns:
        作成された商品のID
    """
    # 現在時刻をUTCで取得（ISO 8601形式）
    current_time = datetime.now(timezone.utc).isoformat()

    # 商品情報の一意なIDを生成
    id = str(uuid.uuid4())

    # ドメインモデルの商品オブジェクトを作成
    product_obj = product.Product(
        id=id,
        name=command.name,
        description=command.description,
        createDate=current_time,
        lastUpdateDate=current_time,
    )

    # Unit of Workパターンでトランザクション実行
    with unit_of_work:
        # 商品をリポジトリに追加（DynamoDBには未送信）
        unit_of_work.products.add(product_obj)
        # トランザクションをコミット（最大25件の変更をまとめて送信）
        unit_of_work.commit()

    return id
