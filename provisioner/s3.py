from __future__ import annotations

import logging
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError


logger = logging.getLogger(__name__)


class S3Uploader:
    def __init__(
        self,
        *,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str,
        presign_ttl: int,
        endpoint_url: Optional[str] = None,
    ) -> None:
        session = boto3.session.Session()
        self.client = session.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            endpoint_url=endpoint_url,
        )
        self.bucket = bucket
        self.presign_ttl = presign_ttl

    def upload_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        except (BotoCoreError, ClientError):
            logger.exception("Failed to upload %s to S3", key)
            raise

    def generate_presigned_url(self, key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self.presign_ttl,
        )
