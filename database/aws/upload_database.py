import boto3

s3 = boto3.client('s3')
BUCKET_NAME = 'wjrm500-wordle'
OBJECT_NAME = 'wordle.db'
FILE_NAME = OBJECT_NAME
def upload_database() -> None:
    print('Uploading SQLite database to AWS...')
    try:
        s3.put_object(
            Bucket = BUCKET_NAME,
            Key = OBJECT_NAME,
            Body = open(OBJECT_NAME, 'rb')
        )
        print('Database uploaded')
    except Exception as e:
        print(str(e))