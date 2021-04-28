from django.db import models
from django.contrib.auth.models import User


# Profiles

class Profile(models.Model):
    profile_picture = models.FileField(blank=True, upload_to='../images')
    content_type = models.CharField(max_length=50)
    user = models.ForeignKey(User, default=None, on_delete=models.PROTECT, related_name="profile")
    money = models.FloatField(default=0)


# ImageTasks

class ImageSubTask(models.Model):
    image_task_description = models.CharField(max_length=200)
    image_task_url = models.CharField(max_length=200)
    image_task_tag = models.CharField(max_length=200)
    prev_task_id = models.IntegerField(blank=True, null=True)
    next_task_id = models.IntegerField(blank=True, null=True)


class ImageTask(models.Model):
    sub_tasks = models.ManyToManyField(ImageSubTask)
    task_name = models.CharField(max_length=200)
    task_description = models.CharField(max_length=200)
    task_creator = models.ForeignKey(User, on_delete=models.PROTECT, blank=True, null=True)
    task_money = models.FloatField(blank=True, null=True)  # total money for task
    task_number = models.IntegerField(blank=True, null=True)  # number of tags needed


class UserImageTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    image_task = models.ForeignKey(ImageSubTask, on_delete=models.PROTECT)
    user_image_task_tag = models.CharField(max_length=1000)
    time = models.DateTimeField(auto_now_add=True)


# POS Tasks


class POSTask(models.Model):
    task_name = models.CharField(max_length=200)
    task_description = models.CharField(max_length=200)
    task_creator = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    task_people = models.IntegerField()
    task_money = models.FloatField()


class POSSubTask(models.Model):
    pos_task_description = models.CharField(max_length=200)
    pos_task_text = models.CharField(max_length=1000)
    pos_task_name = models.CharField(max_length=200)
    prev_task_id = models.IntegerField(blank=True, null=True)
    next_task_id = models.IntegerField(blank=True, null=True)
    parent_task = models.ForeignKey(POSTask, on_delete=models.PROTECT)


class UserPosTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    pos_task = models.ForeignKey(POSSubTask, on_delete=models.PROTECT)
    pos_task_dict = models.CharField(max_length=1000)
    time = models.DateTimeField(auto_now_add=True)


class MoneyRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    money = models.TextField(null=True)  # JSON-serialized (text) version of money change records
