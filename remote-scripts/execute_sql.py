from dotenv import load_dotenv
import os
import requests

load_dotenv()
url = os.environ.get('REMOTE_SERVER')

auth_token = input('Please enter auth token (open app in browser and take from Application -> Session Storage -> https://wjrm500.github.io -> token):\n')
sql_filename = input('Please enter the name of the SQL file you want to execute on the production SQLite database')

with open(f'sql/{sql_filename}', 'r') as file:
    sql = file.read()
print(sql)
exit()

result = requests.post(
    f'{url}/executeSql',
    json = {'sql': sql},
    headers = {'Authorization': f'Bearer {auth_token}'}
)
print(result)