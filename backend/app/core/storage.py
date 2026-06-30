import uuid
from datetime import datetime

import boto3

from app.core.config import settings

_s3_client = None


def get_s3_client():
    """Lazy-init S3 client pointing at Cloudflare R2."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.r2_endpoint_url,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            region_name="auto",
        )
    return _s3_client


def upload_report(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    user_id: str,
) -> str:
    """
    Upload report file to R2.
    Returns the R2 object key (not a URL).
    Never log file_bytes — GLBA NPI.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    date_prefix = datetime.utcnow().strftime("%Y-%m")
    object_key = f"reports/{user_id}/{date_prefix}/{uuid.uuid4()}.{ext}"

    get_s3_client().put_object(
        Bucket=settings.r2_bucket_name,
        Key=object_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return object_key


def generate_presigned_url(object_key: str, expiry_seconds: int = 900) -> str:
    """
    Generate a 15-minute presigned URL for a report file.
    Never return permanent URLs — GLBA requirement.
    """
    return get_s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.r2_bucket_name, "Key": object_key},
        ExpiresIn=expiry_seconds,
    )


def delete_file(object_key: str) -> None:
    """Permanently delete a file from R2 (right-to-deletion / retention expiry)."""
    get_s3_client().delete_object(
        Bucket=settings.r2_bucket_name,
        Key=object_key,
    )
