import boto3
from urllib.parse import urlparse

from django.conf import settings

def generate_presigned_url(key: str, content_type: str = 'image/jpeg', expires_in: int = 300) -> str:
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    return s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.AWS_S3_STORAGE_BUCKET_NAME,
            'Key': key,
            'ContentType': content_type,
        },
        ExpiresIn=expires_in
    )

def delete_old_profile_picture(file_url: str):
    s3 = boto3.client('s3')
    
    parsed_url = urlparse(file_url)
    bucket_name = parsed_url.netloc.split('.')[0]
    key = parsed_url.path.lstrip('/')

    s3.delete_object(Bucket=bucket_name, Key=key)
