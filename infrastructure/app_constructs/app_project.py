from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Sequence

import aws_cdk.aws_iam as aws_iam
import aws_cdk.aws_lambda as aws_lambda
import constructs

from infrastructure.app_constructs import app_project_function


# ========== データクラス定義 ==========
@dataclass
class AppLibrary:
    """アプリケーション依存ライブラリの定義"""
    name: str  # ライブラリ名
    entry: str  # requirements.txt のパス


@dataclass
class AppEntryPoint:
    """Lambda 関数のエントリーポイント定義"""
    name: str  # Lambda 関数名
    entry: str  # ハンドラーの位置（app/entrypoints/api など）
    root: str  # ソースコードのルートディレクトリ（app など）
    environment: Optional[Mapping[str, str]]  # 環境変数
    permissions: Sequence[Callable[[aws_iam.IGrantable], aws_iam.Grant]]  # IAM権限付与関数


class AppProject(constructs.Construct):
    """
    Lambda ベースのアプリケーション統合オーケストレーター

    Hexagonal Architecture に基づいて複数の Lambda 関数を統一的に管理
    """

    def __init__(
        self,
        scope: constructs.Construct,
        id: str,
        runtime: aws_lambda.Runtime,
        app_layers: Sequence[aws_lambda.ILayerVersion],
        app_entry_points: Sequence[AppEntryPoint],
    ) -> None:
        """
        Args:
            scope: CDK のスコープ（親オブジェクト）
            id: このコンストラクトの識別子
            runtime: Lambda ランタイム（Python など）
            app_layers: 複数の Lambda 関数で共有するレイヤー
            app_entry_points: Lambda 関数の設定リスト
        """
        super().__init__(scope, id)

        # 複数の Lambda 関数を辞書で一括管理
        # キー: 関数名、値: Lambda Function オブジェクト
        self._app_entry_functions: dict[str, aws_lambda.Function] = {
            app.name: app_project_function.AppProjectFunction(
                self,
                app.name,
                function_name=app.name,
                entry=app.entry,
                root=app.root,
                runtime=runtime,
                layers=app_layers,
                environment=app.environment,
                permissions=app.permissions or [],
            ).function
            for app in app_entry_points
        }

    @property
    def app_entries(self) -> dict[str, aws_lambda.Function]:
        """作成された Lambda 関数の辞書を取得"""
        return self._app_entry_functions
