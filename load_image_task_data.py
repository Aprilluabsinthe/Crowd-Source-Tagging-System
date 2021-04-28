# Script to retrieve image labels and urls for image tagging task
#
# All original data come from https://storage.googleapis.com/openimages/web/download.html
# The subset of data used is the validation dataset under "Subset with Image-Level Labels (19,958 classes)" category
#
# Author: Kuixi Song
# Date: Mar 25, 2021

from collections import defaultdict
from urllib.request import urlopen
import json

if __name__ == "__main__":
    id_images_map = defaultdict(list)

    # read all human-validated classes and image ids
    data = urlopen(
        'https://storage.googleapis.com/openimages/v5/validation-annotations-human-imagelabels.csv').readlines()
    for line in data[1:]:
        arr = line.decode('utf8').split(",")
        if int(arr[-1]) == 1:
            id_images_map[arr[2]].append(arr[0])

    # get all images with count >= 1000
    # you can adjust the threshold here
    eligible_ids = set([x.strip() for x, y in id_images_map.items() if 10 <= len(y) <= 20])

    # map those ids into class names
    id_name_map = defaultdict(str)
    data = urlopen('https://storage.googleapis.com/openimages/v6/oidv6-class-descriptions.csv').readlines()
    for line in data[1:]:
        arr = line.decode('utf8').split(",")
        if arr[0] in eligible_ids:
            id_name_map[arr[0]] = arr[1].strip()

    # get all image urls
    image_url_map = {}
    data = urlopen(
        'https://storage.googleapis.com/openimages/2018_04/validation/validation-images-with-rotation.csv').readlines()
    for line in data[1:]:
        arr = line.decode('utf8').split(",")
        image_url_map[arr[0]] = arr[2]

    # construct final dictionary
    final_map = defaultdict(list)
    for class_id, class_name in id_name_map.items():
        for image_id in id_images_map[class_id]:
            final_map[class_name].append(image_url_map[image_id])

    # write to a file
    with open('./image_task_output.json', 'w') as f:
        f.write(json.dumps(final_map, indent=4))
    f.close()
