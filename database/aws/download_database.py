import boto3
from dotenv import load_dotenv
import os

load_dotenv()

s3 = boto3.client('s3')
BUCKET_NAME = 'wjrm500-wordle'
OBJECT_NAME = os.environ.get('AWS_S3_OBJECT_NAME')
FILE_NAME = OBJECT_NAME
def download_database() -> None:
    print('Downloading SQLite database from AWS...')
    try:
        s3.download_file(BUCKET_NAME, OBJECT_NAME, FILE_NAME)
        print('Database downloaded')
    except Exception as e:
        print(str(e))