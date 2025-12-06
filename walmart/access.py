import requests

url = "https://marketplace.walmartapis.com/v3/token"

headers = {
    "Authorization": "Basic eW91cl9pZDp5b3VyX3NlY3JldA==",
    "Accept": "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
}

data = {
    "grant_type": "client_credentials",
}

response = requests.post(url, headers=headers, data=data)
print(response.status_code)
print(response.text)
