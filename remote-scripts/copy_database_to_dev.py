import boto3
from dotenv import load_dotenv

load_dotenv()

def copy_database(source_object_name: str, destination_object_name: str) -> None:
    print("Copying SQLite database from production to development...")
    try:
        s3 = boto3.client('s3')
        BUCKET_NAME = 'wjrm500-wordle'  # The bucket name remains the same for both environments

        # Perform the copy operation
        copy_source = {
            'Bucket': BUCKET_NAME,
            'Key': source_object_name
        }

        s3.copy_object(Bucket=BUCKET_NAME, CopySource=copy_source, Key=destination_object_name)
        print(f"Database copied from {source_object_name} to {destination_object_name}")

    except Exception as e:
        print(str(e))

if __name__ == "__main__":
    source_object_name = 'wordle-prod.db'  # Production DB
    destination_object_name = 'wordle-dev.db'  # Development DB
    copy_database(source_object_name, destination_object_name)
