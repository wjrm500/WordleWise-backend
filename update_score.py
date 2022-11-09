from dotenv import load_dotenv
import os
import requests

load_dotenv()
url = os.environ.get('REMOTE_SERVER')

auth_token = input('Please enter auth token (open app in browser and take from Application -> Session Storage -> https://wjrm500.github.io -> token):\n')
date = input('Please enter date (format YYYY-MM-DD):\n')
user = input('Please enter user (wjrm500 or kjem500):\n')
score = int(input('Please enter score:\n'))

result = requests.post(
    f'{url}/addScore',
    json = {'date': date, 'user': user, 'score': score},
    headers = {'Authorization': f'Bearer {auth_token}'}
)
print(result)