from datetime import datetime, timezone

from app.domain.commands import update_product_command
from app.domain.ports import unit_of_work


def handle_update_product_command(
    command: update_product_command.UpdateProductCommand,
    unit_of_work: unit_of_work.UnitOfWork,
) -> str:
    """
    商品更新コマンドを処理する関数

    Args:
        command: 商品更新コマンド（商品ID、name、descriptionを含む）
        unit_of_work: DynamoDBのトランザクション管理オブジェクト

    Returns:
        更新された商品のID
    """
    # 現在時刻をUTCで取得（更新日時として記録）
    current_time = datetime.now(timezone.utc).isoformat()

    # 更新対象の属性を辞書で管理（最後の更新日時は常に更新）
    attr_to_update = {
        "lastUpdateDate": current_time,
    }

    # 商品名が指定されていれば更新対象に追加
    if command.name:
        attr_to_update["name"] = command.name

    # 説明が指定されていれば更新対象に追加
    if command.description:
        attr_to_update["description"] = command.description

    # Unit of Workパターンでトランザクション実行
    with unit_of_work:
        # 指定された属性のみを部分更新（他の属性は保持）
        unit_of_work.products.update_attributes(product_id=command.id, **attr_to_update)
        # トランザクションをコミット（DynamoDBに変更を送信）
        unit_of_work.commit()

    # 更新された商品のIDを返す
    return command.id
