"""
S3 Service - Async wrapper for S3 file storage operations.

Provides upload/download operations for slide library.
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import aioboto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Global singleton
_s3_service_instance = None


def get_s3_service() -> 'S3Service':
    """Get singleton instance of S3Service."""
    global _s3_service_instance
    if _s3_service_instance is None:
        _s3_service_instance = S3Service()
    return _s3_service_instance


class S3Service:
    """
    S3 service for slide library file storage.
    
    Handles S3 uploads/downloads with hash-based naming.
    """

    def __init__(self):
        self.session = None
        self.bucket_name: Optional[str] = None
        self._initialized = False

    async def initialize(
        self,
        bucket_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None
    ):
        """
        Initialize S3 session.

        Args:
            bucket_name: S3 bucket name (defaults to env S3_BUCKET_NAME)
            aws_access_key_id: AWS access key (defaults to env AWS_ACCESS_KEY_ID)
            aws_secret_access_key: AWS secret key (defaults to env AWS_SECRET_ACCESS_KEY)
            region_name: AWS region (defaults to env AWS_REGION or us-east-1)
        """
        if self._initialized:
            print("S3 already initialized")
            return

        self.bucket_name = bucket_name or os.getenv("S3_BUCKET_NAME")
        aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if region_name is None:
            region_name = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"

        if not self.bucket_name:
            raise ValueError("S3 bucket name is required")

        try:
            session_kwargs = {'region_name': region_name}
            if aws_access_key_id:
                session_kwargs['aws_access_key_id'] = aws_access_key_id
            if aws_secret_access_key:
                session_kwargs['aws_secret_access_key'] = aws_secret_access_key

            self.session = aioboto3.Session(**session_kwargs)

            # Verify bucket exists
            async with self.session.client('s3') as client:
                await client.head_bucket(Bucket=self.bucket_name)

            self._initialized = True
            print(f"S3 initialized: bucket={self.bucket_name}")
        except ClientError as e:
            print(f"S3 initialization failed: {e}")
            raise

    def _generate_file_hash(self, file_path: Path) -> str:
        """Generate SHA256 hash of file content."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def upload_file_with_hash(
        self,
        file_path: Path,
        original_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Upload a file to S3 with hash-based naming.

        Args:
            file_path: Local file path
            original_name: Original filename
            metadata: Optional metadata dict

        Returns:
            Mapping data with hash, s3_key, etc.
        """
        if not self._initialized:
            raise RuntimeError("S3 not initialized")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_hash = self._generate_file_hash(file_path)
        original_name = original_name or file_path.name
        
        try:
            file_size_bytes = file_path.stat().st_size
        except Exception:
            file_size_bytes = None
        
        file_ext = Path(original_name).suffix.lower().lstrip(".")

        # Check if file already exists
        if await self.file_exists(file_hash):
            print(f"File with hash {file_hash} already exists in S3")
            return {
                "hash": file_hash,
                "original_name": original_name,
                "s3_key": file_hash,
                "s3_url": f"s3://{self.bucket_name}/{file_hash}",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "size": file_size_bytes,
                "file_type": file_ext,
            }

        # Upload to S3
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata

            async with self.session.client('s3') as client:
                await client.upload_file(
                    str(file_path),
                    self.bucket_name,
                    file_hash,
                    ExtraArgs=extra_args
                )

            mapping_data = {
                "hash": file_hash,
                "original_name": original_name,
                "s3_key": file_hash,
                "s3_url": f"s3://{self.bucket_name}/{file_hash}",
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "size": file_size_bytes,
                "file_type": file_ext,
            }

            print(f"Uploaded file with hash: {file_hash}")
            return mapping_data
        except ClientError as e:
            print(f"Upload failed: {e}")
            raise

    async def download_file(self, s3_key: str, local_path: Path) -> Path:
        """
        Download a file from S3.

        Args:
            s3_key: S3 object key
            local_path: Local destination path

        Returns:
            Path to downloaded file
        """
        if not self._initialized:
            raise RuntimeError("S3 not initialized")

        try:
            local_path.parent.mkdir(parents=True, exist_ok=True)

            async with self.session.client('s3') as client:
                await client.download_file(
                    self.bucket_name,
                    s3_key,
                    str(local_path)
                )

            print(f"Downloaded file: {s3_key} -> {local_path}")
            return local_path
        except ClientError as e:
            print(f"Download failed: {e}")
            raise

    async def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: S3 object key

        Returns:
            True if deleted
        """
        if not self._initialized:
            raise RuntimeError("S3 not initialized")

        try:
            async with self.session.client('s3') as client:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
            print(f"Deleted file: {s3_key}")
            return True
        except ClientError as e:
            print(f"Delete failed: {e}")
            return False

    async def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3."""
        if not self._initialized:
            raise RuntimeError("S3 not initialized")

        try:
            async with self.session.client('s3') as client:
                await client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
