import os
import sys
import django
import nltk

nltk.download('punkt')
from nltk.tokenize import sent_tokenize

sys.path.append("./crowdsourcedtagging")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapps.settings')
django.setup()

from crowdsourcedtagging.models import POSTask, POSSubTask, User, Profile


def read_file_into_lines(filename):
    sentences = []
    with open(filename, "r") as f:
        for sentence in f.readlines():
            sentences.append(sentence.strip())
        f.close()
    return sentences


def load_into_db(name, lines):
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

    print("Importing key {} with {} lines".format(name, len(lines)))
    # Save parent task
    task = POSTask()
    task.task_description = "Tag POS for " + name
    task.task_name = name
    task.task_creator = admin
    task.task_people = 100
    task.task_money = 1000.0
    task.save()
    # Save sub-tasks
    sentences = []
    for line in lines:
        sentences.extend(sent_tokenize(line))
    # Ignore too short sentences
    sentences = [x for x in sentences if len(x.split()) > 3]
    for (idx, sentence) in enumerate(sentences):
        sub_task = POSSubTask()
        sub_task.pos_task_text = sentence
        sub_task.pos_task_description = "Tag POS for " + name
        sub_task.pos_task_name = name
        sub_task.parent_task = task
        sub_task.save()
        if idx != 0:
            sub_task.prev_task_id = sub_task.id - 1
        if idx != len(sentences) - 1:
            sub_task.next_task_id = sub_task.id + 1
        sub_task.save()


if __name__ == '__main__':
    # Optionally clear task and postasks in database
    # ImageTask.objects.filter(task_type='pos').delete()
    # POSTask.objects.all().delete()

    # Read text files
    for i in range(10):
        filename = "pos_data/a{}.txt".format(i + 1)
        res = read_file_into_lines(filename)
        load_into_db(filename.split("/")[-1], res)
    print("Done!")
