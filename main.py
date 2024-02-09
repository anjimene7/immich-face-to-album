import os
import requests
import time
from datetime import datetime

def request_api(method, url, headers, request_type, payload=None):
    response = requests.request(method, url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Error:{request_type} - {response.status_code} - {response.reason}")
        exit(1)
    return response.json()


def face_to_album(key, server, face, album):
    headers = {"Accept": "application/json", "x-api-key": key}

    url = f"{server}/api/person/{face}/assets"
    face_data = request_api("GET", url, headers, "GetFaceAssets")
    face_assets = [item["id"] for item in face_data]

    url = f"{server}/api/album/{album}"
    album_data = request_api("GET", url, headers, "GetAlbumAssets")
    album_assets = [item["id"] for item in album_data["assets"]]

    assets_to_add = [item for item in face_assets if item not in album_assets]

    if not assets_to_add:
        print("No assets to add")
        return

    url = f"{server}/api/album/{album}/assets"
    payload = {"ids": assets_to_add}
    request_api("PUT", url, headers, "PutAssetsToAlbum", payload)
    print(f"Added {len(assets_to_add)} asset(s) to the album")


if __name__ == "__main__":
    print('Starting...')
    keys = os.environ.get('IMMICH_KEY').split(',') # Key by user
    server = os.environ.get('IMMICH_SERVER')
    faces = os.environ.get('IMMICH_FACE').split(',') # Face id by user, same order as keys
    album = os.environ.get('IMMICH_ALBUM')
    time_sleep = os.environ.get('SLEEP', 3600)
    if None in (keys, server, faces, album):
        print(f"Not all variables are set, please set IMMICH_KEY, IMMICH_SERVER, IMMICH_FACE, IMMICH_ALBUM")
        exit(1)
    else:
        print(f"server: {server}, face id: {faces}, album id: {album}, sleep: {time_sleep}")
    while True:
        print(datetime.now())
        for face, key in zip(faces, keys):
            print(f"Calling api for face ID: {face}")
            face_to_album(key, server, face, album)
        print('-------------------------------------')
        time.sleep(int(time_sleep))

