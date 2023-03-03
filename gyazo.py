import argparse
import datetime
import os

import filedate
import requests


class Gyazo:
    BASE_URL = r"https://api.gyazo.com/api"

    def __init__(self, access_token: str, save_folder: str):
        self._save_folder = save_folder
        self._access_token = access_token

        self.params = {"access_token": self._access_token}

    def get_images(self):
        params = {"per_page": 2}
        response = self.get("/images", params=params)
        images = response.json()
        total_count = response.headers["X-Total-Count"]

        for page in range(2, int(total_count) // 2 + 2):
            params["page"] = page
            response = self.get("/images", params=params)
            images.extend(response.json())

        return images

    def get(self, path: str, params: dict):
        url = self.BASE_URL + path
        params.update({"access_token": self._access_token})
        with requests.get(url, params=params) as response:
            return response

    def download_image(self, image: dict):
        image_id = image["image_id"]
        file_name = image["metadata"]["title"]
        url = image["url"]
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(os.path.join(self._save_folder, file_name), "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        print(f"Downloaded {image_id} to {file_name}")

    def change_datetime(self, image):
        image_name = image["metadata"]["title"]
        new_date = datetime.datetime.strptime(image["created_at"], "%Y-%m-%dT%H:%M:%S+%f").strftime("%Y-%m-%d %H:%M:%S")
        file = filedate.File(os.path.join(self._save_folder, image_name))
        file.set(
            created=new_date,
            modified=new_date,
            accessed=new_date
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--access-token", type=str, required=True)
    parser.add_argument("--save-folder", type=str, required=True)
    args = parser.parse_args()
    gyazo = Gyazo(args.access_token, args.save_folder)

    os.makedirs(args.save_folder, exist_ok=True)

    gyazo_images = gyazo.get_images()
    local_images = {image_name for image_name in os.listdir(args.save_folder) if os.path.isfile(image_name)}

    for image in gyazo_images:
        image_name = image["metadata"]["title"]
        if image_name not in local_images:
            gyazo.download_image(image)
        gyazo.change_datetime(image)
