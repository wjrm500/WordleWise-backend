import boto3

s3 = boto3.client('s3')
BUCKET_NAME = 'wjrm500-wordle'
OBJECT_NAME = 'wordle.db'
def download(filename: str) -> None:
    print('Downloading SQLite database from AWS...')
    try:
        s3.download_file(BUCKET_NAME, OBJECT_NAME, filename)
        print('Database downloaded')
    except Exception as e:
        print(str(e))