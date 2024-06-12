import requests
import json
import time
from os import environ
from time import sleep
from datetime import datetime


def login_to_api(server_url, email, password):
    print("Attempting to log in...")
    login_url = f"{server_url}/api/auth/login"
    login_payload = json.dumps({"email": email, "password": password})
    login_headers = {'Content-Type': 'application/json'}
    response = requests.post(login_url, headers=login_headers, data=login_payload)
    #print(response.text)

    if response.status_code in [200, 201]:
        print(f"Login successful: {response.status_code}")
        return response.json()
    else:
        print(f"Failed to login. Status code: {response.status_code}")
        return None


def get_personId_time_bucket_assets(server_url, token, personId, bucket, size='MONTH'):
    url = f"{server_url}/api/timeline/bucket"
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    params = {
        'personId': personId,
        'timeBucket': bucket,
        'size': size
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch assets. Status code: {response.status_code}, Response text: {response.text}")
        return []


def get_time_buckets(server_url, token, user_id, size='MONTH'):
    print("Fetching time buckets...")
    url = f"{server_url}/api/timeline/buckets"
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    params = {'userId': user_id, 'size': size}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        print("Time buckets fetched successfully.")
        buckets = response.json()
        #print(f"Time buckets: {buckets}")
        return buckets
    else:
        print(f"Failed to fetch time buckets. Status code: {response.status_code}, Response text: {response.text}")
        return []


def add_assets_to_album(url, token, album_id, asset_ids, key=None):
    url = f"{url}/api/albums/{album_id}/assets"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    payload = json.dumps({"ids": asset_ids})
    params = {'key': key} if key else {}
    print(f"Sending request to {url} with payload: REDACTED and params: {params}")

    response = requests.put(url, headers=headers, data=payload, params=params)

    if response.status_code == 200:
        print("Assets successfully added to the album.")
        for el in response.json():
            if not el.get('success'):
                if not el.get('error') == 'duplicate':
                    print(f"Error with {el['id']}: {el['error']}")
        return True
    else:
        try:
            error_response = response.json()
            print(f"Error adding assets to album: {error_response.get('error', 'Unknown error')}")
        except json.JSONDecodeError:
            print(
                f"Failed to decode JSON response. Status code: {response.status_code}, Response text: {response.text}")
        return False


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def main():
    server_url = environ.get('IMMICH_SERVER')
    emails = environ.get('IMMICH_EMAIL').split(',')
    passwords = environ.get('IMMICH_PASSWORD').split(',')
    person_ids = environ.get('IMMICH_FACE').split(',')
    album_id = environ.get('IMMICH_ALBUM')
    time_sleep = environ.get('SLEEP', 3600)

    while True:
        print(datetime.now())
        for email, password, person_id in zip(emails, passwords, person_ids):
            print(f"Calling api for face ID: {person_id} from {email}")
            login_response = login_to_api(server_url, email, password)
            if login_response:
                token = login_response['accessToken']
                user_id = login_response['userId']
                time_buckets = get_time_buckets(server_url, token, user_id, size='MONTH')

                unique_asset_ids = set()
                for bucket in time_buckets:
                    assets = get_personId_time_bucket_assets(server_url, token, person_id, bucket['timeBucket'])
                    for asset in assets:
                        unique_asset_ids.add(asset['id'])

                print(f"Total unique assets: {len(unique_asset_ids)}")
                asset_ids_list = list(unique_asset_ids)

                for asset_chunk in chunker(asset_ids_list, 500):
                    add_assets_to_album(server_url, token, album_id, asset_chunk, key=None)
                    time.sleep(2)
            else:
                print("Failed to log in; cannot proceed with fetching assets.")
        print('#####################################3')
        sleep(int(time_sleep))


if __name__ == "__main__":
    main()