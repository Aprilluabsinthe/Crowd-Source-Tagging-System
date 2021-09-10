Crowd Source Tagging System

# Prerequisites

This project runs on Python 3.8 and Django 3.1.7.

# Backlogs

See [here](https://github.com/cmu-webapps/s21_team_2/blob/main/BACKLOG.md).

# How to Get Started

## On the Server

### To Run Application

1. `source my_env/bin/activate` to activate virtual environment.
2. `source run_server.sh` to start server.

### To Terminate Application

1. Just remember to `deactivate` the virtual environment.

## Download ImageTask Data

1. Run `load_image_task_data.py` to download image data. This script will store the image urls into `image_task_output.json` file. You can modify the threshold for the numbers of images in each category in the Python script.
2. Run `save_image_to_db.py` to flush the image task data into `db.sqlite3`.

## Download NLTK Dataset

1. Run `python3 manage.py shell` or `save_pos_to_db.py`.
2. Enter `import nltk`, `nltk.download('punkt')`.
3. If there is an error, run `cp -r /home/ubuntu/nltk_data /home/ubuntu/s21_team_2/my_env/`.

## Run Project

1. Clone this repo, create a virtual environment in whichever way you want (`conda`, `venv`, you name it).
2. Activate that virtual environment and install `Django`.
3. Install `nltk` and download nltk dataset using `save_pos_to_db.py` if you haven't.
4. Run `python3 manage.py runserver`.

# How to Reset Database

In the root folder, run `chmod +x reset_db.sh && ./reset_db.sh`.

# Explanations on file names

1. `{image|pos}_task_list`: the page for all image/pos tagging tasks
2. `{image|pos)_sub_task_list`: the page for all sub-tasks within one image/pos tagging task
3. `{image|pos}_single_task`: the page for one single image/pos tagging task within a sub-task

# Enable OAuth

Run `pip3 install -r requirements.txt`.
