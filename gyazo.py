import argparse
import datetime
import logging
import os

import filedate
import requests

logger = logging.getLogger("gyazo")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class Gyazo:
    BASE_URL = r"https://api.gyazo.com/api"

    def __init__(self, access_token: str, save_folder: str):
        self._save_folder = save_folder
        self._access_token = access_token

        self.headers = {"Authorization": f"Bearer {self._access_token}"}

    def get_images(self):
        logger.info(f"Collecting your images")
        per_page = 100
        params = {"per_page": per_page}
        response = self.get("/images", params=params)
        images = response.json()
        total_count = response.headers["X-Total-Count"]
        total_pages = int(total_count) // per_page + 2
        for page in range(2, total_pages):
            logger.info(f"Collecting your images ({page}/{total_pages - 1})")
            params["page"] = page
            response = self.get("/images", params=params)
            images.extend(response.json())

        return images

    def get(self, path: str, params: dict):
        url = self.BASE_URL + path
        with requests.get(url, params=params, headers=self.headers) as response:
            return response

    def post(self, path: str, params: dict):
        url = self.BASE_URL + path
        with requests.post(url, params=params, headers=self.headers) as response:
            return response

    def change_datetime(self, image):
        image_name = image["metadata"]["title"]
        logger.info(f"Changing date for: {image_name}")
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
    logger.info(f"Found {len(gyazo_images)} images on Gyazo")
    local_images = {image_name for image_name in os.listdir(args.save_folder) if
                    os.path.isfile(os.path.join(args.save_folder, image_name))}

    for image in gyazo_images:
        try:
            gyazo.change_datetime(image)
        except:
            logger.warning(f"File not found or has unknown characters. Skipping: {image['metadata']['title']}")
            continue
