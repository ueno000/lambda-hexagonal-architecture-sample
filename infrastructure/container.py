# app/infrastructure/container.py

from __future__ import annotations

import boto3
from functools import lru_cache

from app.config import AppConfig
from app.adapters import dynamodb_unit_of_work
from app.adapters import dynamodb_query_service


# --- low-level (shared) -------------------------------------------------------

@lru_cache(maxsize=1)
def _get_dynamodb_resource():
    # ローカル/本番で分岐したい場合は AppConfig 内で吸収
    return boto3.resource(
        "dynamodb",
        region_name=AppConfig.get_default_region(),
        endpoint_url=AppConfig.get_dynamodb_endpoint_url(),  # None なら本番
    )


def _get_dynamodb_client():
    # resource と同じコネクションを共有
    return _get_dynamodb_resource().meta.client


def _get_table_name() -> str:
    table = AppConfig.get_table_name()
    if not table:
        raise RuntimeError("TABLE_NAME is empty")
    return table


# --- factories (per request / per use) ---------------------------------------

def create_unit_of_work() -> dynamodb_unit_of_work.DynamoDBUnitOfWork:
    """
    状態を持つ可能性があるので毎回生成する。
    """
    return dynamodb_unit_of_work.DynamoDBUnitOfWork(
        _get_table_name(),
        _get_dynamodb_client(),
    )


def create_products_query_service() -> (
    dynamodb_query_service.DynamoDBProductsQueryService
):
    """
    読み取り専用。軽量なので都度生成でOK（共有したければ @lru_cache も可）。
    """
    return dynamodb_query_service.DynamoDBProductsQueryService(
        _get_table_name(),
        _get_dynamodb_client(),
    )


# --- (optional) higher-level wiring -------------------------------------------

def build_command_handler():
    """
    必要ならここでハンドラに依存をまとめて渡す。
    今回は UoW を都度渡す前提なのでシンプルにしている。
    """
    return {
        "create_uow": create_unit_of_work,
        "create_query": create_products_query_service,
    }
