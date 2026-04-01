from app.domain.commands import delete_product_command
from app.domain.ports import unit_of_work


def handle_delete_product_command(
    command: delete_product_command.DeleteProductCommand,
    unit_of_work: unit_of_work.UnitOfWork,
) -> str:
    """
    商品削除コマンドを処理する関数

    Args:
        command: 商品削除コマンド（削除対象の商品IDを含む）
        unit_of_work: DynamoDBのトランザクション管理オブジェクト

    Returns:
        削除された商品のID
    """
    # Unit of Workパターンでトランザクション実行
    with unit_of_work:
        # 指定されたIDの商品をリポジトリから削除
        unit_of_work.products.delete(product_id=command.id)
        # トランザクションをコミット（DynamoDBに変更を送信）
        unit_of_work.commit()

    # 削除された商品のIDを返す
    return command.id
