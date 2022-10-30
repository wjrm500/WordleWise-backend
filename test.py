from database.Database import Database
from database.aws.upload_database import upload_database
from database.aws.download_database import download_database

download_database()
database = Database(database_url = 'sqlite:///wordle.db')
# database.truncate_day_table()
data = database.get_data()
print(data)
# upload_database()