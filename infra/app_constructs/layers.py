from typing import List, Optional

from aws_cdk import aws_lambda, aws_lambda_python_alpha
from constructs import Construct


class SharedLayer(Construct):
    """
    Lambda レイヤーコンストラクト

    複数の Lambda 関数で共有する Python パッケージ依存関係を管理
    コードサイズを削減し、再利用性を向上させれる
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        compatible_runtimes: List[aws_lambda.Runtime],  # サポート対象のランタイム
        entry: str,  # requirements.txt のパス（library/layers など）
        layer_version_name: str,  # レイヤーバージョン名
        extra_bundling_options: Optional[
            aws_lambda_python_alpha.BundlingOptions
        ] = None,  # バンドリング時の追加オプション
    ) -> None:

        super().__init__(scope, construct_id)

        # ========== Python レイヤー作成 ==========
        # requirements.txt から依存パッケージを自動バンドル
        self._libraries_layer = aws_lambda_python_alpha.PythonLayerVersion(
            scope,
            "SimpleCrudAppLayers",
            layer_version_name=layer_version_name,
            entry=entry,  # requirements.txt を格納するディレクトリ
            compatible_runtimes=compatible_runtimes,
            bundling=extra_bundling_options,
        )

    @property
    def libraries_layer(self) -> aws_lambda_python_alpha.PythonLayerVersion:
        """作成された Lambda レイヤーを取得"""
        return self._libraries_layer
