import constructs
from aws_cdk import RemovalPolicy, aws_apigateway, aws_lambda, aws_logs, aws_iam
import cdk_nag


class AppProjectApi(constructs.Construct):
    """
    API Gateway 統合コンストラクト

    Lambda 関数を HTTP エンドポイントとして公開し、
    CORS、ロギング、トレーシング、バリデーションを設定
    """

    def __init__(
        self,
        scope: constructs.Construct,
        id: str,
        handler: aws_lambda.IFunction,
    ) -> None:
        """
        Args:
            scope: CDK のスコープ（親オブジェクト）
            id: このコンストラクトの識別子
            handler: API Gateway が呼び出す Lambda 関数
        """
        super().__init__(scope, id)

        # ========== アクセスログ設定 ==========
        # CloudWatch にアクセスログを送信するロググループを作成
        access_log_group = aws_logs.LogGroup(
            self,
            "SimpleCrudAppRestApiAccessLogGroup",
            log_group_name="simple-crud-api-access-log-group",
            removal_policy=RemovalPolicy.RETAIN,  # スタック削除後もログを保持
            retention=aws_logs.RetentionDays.TWO_MONTHS,  # 2ヶ月のログ保持期間
        )

        # ========== ステージ設定 ==========
        # API Gateway の dev ステージの詳細設定
        stage_options = aws_apigateway.StageOptions(
            stage_name="dev",
            # CloudWatch にアクセスログを送信
            access_log_destination=aws_apigateway.LogGroupLogDestination(
                access_log_group
            ),
            # JSON形式でアクセスログを記録（呼び出し元識別情報、HTTPメソッド、IP、時間など）
            access_log_format=aws_apigateway.AccessLogFormat.json_with_standard_fields(
                caller=True,
                http_method=True,
                ip=True,
                protocol=True,
                request_time=True,
                resource_path=True,
                response_length=True,
                status=True,
                user=True,
            ),
            logging_level=aws_apigateway.MethodLoggingLevel.INFO,  # ログレベルを INFO に設定
            data_trace_enabled=True,  # リクエスト/レスポンスボディをログに記録
            metrics_enabled=True,  # CloudWatch メトリクスを有効化
            tracing_enabled=True,  # X-Ray トレーシングを有効化
        )

        # ========== API Gateway 作成 ==========
        # Lambda を HTTP エンドポイントとして公開
        self._api = aws_apigateway.LambdaRestApi(
            self,
            "SimpleCrudAppRestApi",
            handler=handler,
            proxy=False,  # 自動プロキシ無効（明示的なルート定義を使用）
            description="Products API proxy to the Lambda",
            deploy_options=stage_options,
            rest_api_name="simple-crud-app-rest-api",
        )

        # ========== セキュリティ設定（cdk_nag 対応） ==========
        # CloudWatch ロールを取得
        cw_role = [p for p in self._api.node.children if isinstance(p, aws_iam.Role)][0]
        # CloudWatch ロール用の管理ポリシー使用を許可（CDK が自動生成）
        cdk_nag.NagSuppressions.add_resource_suppressions(
            construct=cw_role,
            suppressions=[
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM4",
                    reason="CloudWatch role is configured by CDK itself.",
                    applies_to=["Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"]
                ),
            ],
        )

        # ========== エラーレスポンス設定 ==========
        # 4xx エラー時のレスポンスを設定（CORS対応）
        self._api.add_gateway_response(
            "client-error-response",
            type=aws_apigateway.ResponseType.DEFAULT_4_XX,
            response_headers={
                "Access-Control-Allow-Origin": "'*'",  # すべてのオリジンからのアクセスを許可
                "Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,\
                    X-Api-Key,x-amz-security-token'",
                "Access-Control-Allow-Methods": "'OPTIONS,GET,POST,PUT,DELETE'",
            },
            templates={
                "application/json": '{ "message": $context.error.messageString }'
            },
        )

        # 5xx エラー時のレスポンスを設定（CORS対応）
        self._api.add_gateway_response(
            "server-error-response",
            type=aws_apigateway.ResponseType.DEFAULT_5_XX,
            response_headers={
                "Access-Control-Allow-Origin": "'*'",  # すべてのオリジンからのアクセスを許可
                "Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,\
                    X-Api-Key,x-amz-security-token'",
                "Access-Control-Allow-Methods": "'OPTIONS,GET,POST,PUT,DELETE'",
            },
            templates={
                "application/json": '{ "message": $context.error.messageString }'
            },
        )

        # ========== リクエストバリデーション ==========
        # API Gateway でリクエストボディやヘッダーの検証を実施
        aws_apigateway.RequestValidator(self, "api-gw-request-validator",
            rest_api=self._api,
        )

    @property
    def api(self) -> aws_apigateway.SpecRestApi:
        """作成された API Gateway インスタンスを取得"""
        return self._api
