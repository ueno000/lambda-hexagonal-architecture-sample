import boto3
from aws_lambda_powertools import logging, tracing
from aws_lambda_powertools.event_handler import api_gateway
from aws_lambda_powertools.utilities import data_classes, typing

from app.adapters import dynamodb_query_service, dynamodb_unit_of_work
from app.domain.command_handlers import (
    create_product_command_handler,
    delete_product_command_handler,
    update_product_command_handler,
)
from app.domain.commands import (
    create_product_command,
    delete_product_command,
    update_product_command,
)
from app.domain.exceptions.domain_exception import DomainException
from app.entrypoints.api import config
from app.entrypoints.api.middleware import exception_handler, utils
from app.entrypoints.api.model import api_model

# ========== 設定セットアップ ==========
# アプリケーション設定を環境変数から読み込む
app_config = config.AppConfig(**config.config)
# CORS設定を初期化
cors_config = api_gateway.CORSConfig(**app_config.cors_config)

# API Gateway統合ハンドラーを作成
# strip_prefixes: APIゲートウェイのベースパス（/api など）をルートから除去
app = api_gateway.ApiGatewayResolver(
    cors=cors_config,
    strip_prefixes=[config.AppConfig.get_api_base_path()],
)

# ========== ロギングとトレーシング ==========
# CloudWatch ログの設定
logger = logging.Logger()
# AWS X-Ray トレーシングの有効化（Lambda関数とサービス間の呼び出しを追跡）
tracer = tracing.Tracer()

# ========== DynamoDB クライアント初期化 ==========
# DynamoDBクライアントを指定リージョンで作成
dynamodb_client = boto3.resource(
    "dynamodb",
    region_name=config.AppConfig.get_default_region(),
    endpoint_url="http://host.docker.internal:8000"
)
# Unit of Work パターン：複数の変更をトランザクションで管理
unit_of_work = dynamodb_unit_of_work.DynamoDBUnitOfWork(
    config.AppConfig.get_table_name(), dynamodb_client.meta.client
)
# CQRS パターン：読み取り専用のクエリサービス
products_query_service = dynamodb_query_service.DynamoDBProductsQueryService(
    config.AppConfig.get_table_name(), dynamodb_client.meta.client
)


@tracer.capture_method
@app.get("/products/<id>")
def get_product(id: str) -> api_model.GetProductResponse:
    """Returns a single product."""
    # クエリサービスで指定IDの商品を取得
    product = products_query_service.get_product_by_id(product_id=id)

    # 商品が見つからない場合は例外を発生
    if not product:
        raise DomainException(f"Could not locate product with id: {id}.")

    # ドメインモデルをAPIレスポンスモデルに変換
    response = api_model.GetProductResponse.parse_obj(product)
    return response.dict()


@tracer.capture_method
@app.get("/products")
def list_products() -> api_model.ListProductsResponse:
    """Returns a list of products with paging support."""
    # クエリパラメータからページサイズとページネーショントークンを取得
    page_size_str = app.current_event.get_query_string_value("pageSize")
    next_token = app.current_event.get_query_string_value("nextToken")

    # ページサイズのバリダション（数値必須）
    if not page_size_str or not page_size_str.isnumeric():
        raise DomainException(
            "pageSize should be provided in query string as a number."
        )

    # クエリサービスで商品リストをページング取得
    # last_evaluated_key: 次ページ取得時に使用するトークン
    products, last_evaluated_key = products_query_service.list_products(
        page_size=int(page_size_str),
        next_token=next_token,
    )
    # ドメインモデルをAPIレスポンスモデルに変換
    products_parsed = [api_model.Product.parse_obj(p.dict()) for p in products]
    # レスポンスを作成（次ページ情報を含む）
    response = api_model.ListProductsResponse(
        products=products_parsed, nextToken=last_evaluated_key
    )
    return response.dict()


@tracer.capture_method
@app.post("/products")
@utils.parse_event(model=api_model.CreateProductRequest, app_context=app)
def create_product(
    request: api_model.CreateProductRequest,
) -> api_model.CreateProductResponse:
    """Creates a product."""
    # APIリクエストをドメインコマンドに変換
    # コマンドハンドラーでビジネスロジックを実行
    id = create_product_command_handler.handle_create_product_command(
        command=create_product_command.CreateProductCommand(
            name=request.name,
            description=request.description,
        ),
        unit_of_work=unit_of_work,
    )
    # 作成された商品のIDを返す
    response = api_model.CreateProductResponse(id=id)
    return response.dict()


@tracer.capture_method
@app.put("/products/<id>")
@utils.parse_event(model=api_model.UpdateProductRequest, app_context=app)
def update_product(
    request: api_model.UpdateProductRequest, id: str
) -> api_model.UpdateProductResponse:
    """Updates a product."""
    # APIリクエストをドメインコマンドに変換
    # コマンドハンドラーで部分更新を実行
    updated_product_id = update_product_command_handler.handle_update_product_command(
        command=update_product_command.UpdateProductCommand(
            id=id,
            name=request.name,
            description=request.description,
        ),
        unit_of_work=unit_of_work,
    )
    # 更新された商品のIDを返す
    response = api_model.UpdateProductResponse(id=updated_product_id)
    return response.dict()


@tracer.capture_method
@app.delete("/products/<id>")
def delete_product(
    id: str,
) -> api_model.DeleteProductResponse:
    """Deletes a product."""
    # APIリクエストをドメインコマンドに変換
    # コマンドハンドラーで削除を実行
    deleted_product_id = delete_product_command_handler.handle_delete_product_command(
        command=delete_product_command.DeleteProductCommand(
            id=id,
        ),
        unit_of_work=unit_of_work,
    )
    # 削除された商品のIDを返す
    response = api_model.DeleteProductResponse(id=deleted_product_id)
    return response.dict()


@tracer.capture_lambda_handler  # X-Rayトレーシングを有効化
@logger.inject_lambda_context(log_event=True)  # Lambda コンテキストをログに追加
@data_classes.event_source(
    data_class=data_classes.api_gateway_proxy_event.APIGatewayProxyEvent
)
@exception_handler.handle_exceptions(
    user_exceptions=[Exception], cors_config=cors_config
)  # 例外処理ミドルウェア（ドメイン例外と予期しない例外を分離）
def handler(
    event: data_classes.api_gateway_proxy_event.APIGatewayProxyEvent,
    context: typing.LambdaContext,
):
    """
    Lambda エントリーポイント

    処理フロー：
    1. API Gateway からのイベントを受け取る
    2. ロギング + X-Ray トレーシング開始
    3. 例外ハンドリング中でリクエストをルーティング
    4. 適切なエンドポイント関数を呼び出す
    5. レスポンスを API Gateway 形式で返す
    """
    # API Gatewayイベントをルーティングして対応するエンドポイント関数を呼び出す
    return app.resolve(event, context)
