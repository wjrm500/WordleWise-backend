from database.Database import Database
from database.aws.upload_database import upload_database
from database.aws.download_database import download_database

download_database()
database = Database(database_url = 'sqlite:///wordle-dev.db')
data = database.get_data()
print(data)
database.delete_day("2022-11-04")
data = database.get_data()
print(data)
upload_database()