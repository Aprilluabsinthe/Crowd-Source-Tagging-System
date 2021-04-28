import json
import os
import sys
import django

sys.path.append("./crowdsourcedtagging")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapps.settings')
django.setup()

from crowdsourcedtagging.models import ImageTask, ImageSubTask, User, Profile


# Run `load_image_task_data.py` first to generate the `image_task_output.json` file.

def load_into_db(filename):
    # If there is no admin in database, create an admin
    admin = User.objects.filter(username="admin")
    if admin.count() == 0:
        new_admin = User()
        new_admin.username = "admin"
        new_admin.password = "pbkdf2_sha256$216000$npxQtA07IEsm$2xuQIX9h1yXgXEAjyKIOAEnz6kvKQJbxg5pjIZNNVFk="
        new_admin.email = "admin@admin.admin"
        new_admin.save()
        new_profile = Profile.objects.create(user=new_admin)
        new_profile.save()
        admin = new_admin
    else:
        admin = admin.first()

    # Read json files
    with open(filename, 'r') as json_file:
        data = json.load(json_file)
        for key, urls in data.items():
            print("Importing key {} with {} rows".format(key, len(urls)))
            task = ImageTask()
            task.task_description = "Tag images for " + key
            task.task_name = key
            task.task_creator = admin
            task.task_money = 1000.0
            task.task_number = 100
            task.save()
            idx = 0
            for url in urls:
                sub_task = ImageSubTask()
                sub_task.image_task_url = url
                sub_task.image_task_tag = key
                sub_task.image_task_description = "Tag images for " + key
                sub_task.save()
                if idx != 0:
                    sub_task.prev_task_id = sub_task.id - 1
                if idx != len(urls) - 1:
                    sub_task.next_task_id = sub_task.id + 1
                sub_task.save()
                task.sub_tasks.add(sub_task)
                idx += 1
            task.save()
        print("Done!")
        json_file.close()


if __name__ == '__main__':
    # Optionally clear task and imagetasks in database
    # ImageTask.objects.filter(task_type='image').delete()
    # ImageSubTask.objects.all().delete()

    load_into_db("image_task_output.json")
