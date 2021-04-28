import pytz
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import Http404, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from crowdsourcedtagging.forms import *
from crowdsourcedtagging.models import *
from nltk.tokenize import word_tokenize, sent_tokenize
from collections import defaultdict
import math
import json
import datetime
from django.utils.translation import gettext
from django.db import transaction

POS_PAGE_CNT = 6
IMG_PAGE_CNT = 12
PAGE_DELTA = 5

POS_DICT = {
    "1": "Noun",
    "2": "Verb",
    "3": "Adjective",
    "4": "Adverb",
    "5": "Preposition",
    "6": "Pronoun",
    "7": "Conjunction",
    "8": "Interjection",
    "9": "Punctuation",
}
POS_COLOR_DICT = {
    "1": "bg-primary text-white",
    "2": "bg-secondary text-white",
    "3": "bg-success text-white",
    "4": "bg-danger text-white",
    "5": "bg-warning text-dark",
    "6": "bg-info text-white",
    "7": "bg-light text-dark",
    "8": "bg-dark text-white",
    "9": "bg-white text-dark",
}


####################
# homepage actions #
####################

def home(request):
    context = {
        'need_logged_in': not request.user.is_authenticated,
        'greeting': get_time_greeting()
    }
    return render(request, 'crowdsourcedtagging/homepage.html', context)


######################
# image task actions #
######################

@login_required
def image_all_tasks_action(request, page_num):
    # get all image tasks
    all_tasks = ImageTask.objects.all()[::-1]
    page_count = 1 + math.ceil(len(all_tasks) / IMG_PAGE_CNT)
    if page_num < 1 or page_num >= page_count:
        page_num = 1
    page_lower = max(1, page_num - PAGE_DELTA)
    page_upper = min(page_count, page_num + PAGE_DELTA)
    tasks = all_tasks[(page_num - 1) * IMG_PAGE_CNT:page_num * IMG_PAGE_CNT]
    for task in tasks:
        sub_tasks = task.sub_tasks.all()
        task.count = sub_tasks.count()
        if task.task_money and task.task_number and image_task_completed_count(task) < task.task_number:
            task.reward = round(task.task_money / task.task_number, 2)
        else:
            task.reward = 0.0
        # only display one url for all task list for now
        task.url = sub_tasks.first().image_task_url
        task.finished = is_user_completed_all_image_task(request.user, task)
    context = {
        'pageName': gettext('All Image Tasks'),
        'user': request.user,
        'tasks': tasks,
        'pageRange': range(page_lower, page_upper),
        'currPage': page_num
    }
    return render(request, 'crowdsourcedtagging/image_task_list.html', context)


@login_required
def image_sub_tasks_action(request, taskid):
    task = ImageTask.objects.filter(id=taskid)
    if not task:
        return _error_response(request, gettext("Invalid image subtask"))
    task = task.get()
    task_creator = task.task_creator
    sub_tasks = task.sub_tasks.all()
    if not sub_tasks or sub_tasks.count() == 0:
        return _error_response(request, gettext("Empty image subtask"))

    context = {
        'pageName': gettext('Images for ') + task.task_name,
        'user': request.user,
        "image_tasks": sub_tasks,
        "task_creator": task_creator
    }
    return render(request, 'crowdsourcedtagging/image_sub_task_list.html', context)


@login_required
def image_single_task_action(request, image_taskid):
    image_task = ImageSubTask.objects.filter(id=image_taskid)
    if not image_task:
        return _error_response(request, gettext("Invalid image subtask"))
    image_task = image_task.get()
    user_image_task = UserImageTask.objects.filter(user=request.user).filter(image_task=image_task)
    if user_image_task.count() != 0:
        user_image_task_tag = user_image_task.get().user_image_task_tag
    else:
        user_image_task_tag = "NULL"

    finished_task_count = -1  # not a task creator
    parent_task = ImageTask.objects.get(sub_tasks=image_task)
    if parent_task.task_creator == request.user:
        # when this task is created by request.user, navigate to creator view
        image_finished_tasks = UserImageTask.objects.filter(image_task=image_task)
        finished_task_count = image_finished_tasks.count()

    context = {
        'pageName': gettext('Image Task for ') + image_task.image_task_tag,
        'user': request.user,
        "image_task": image_task,
        "user_image_task_tag": gettext(user_image_task_tag),
        "taskid": image_task.imagetask_set.first().id,
        "finished_task_count": finished_task_count
    }
    return render(request, 'crowdsourcedtagging/image_single_task.html', context)


@login_required
@ensure_csrf_cookie
def image_tag_action(request):
    if request.method != 'POST':
        return _error_response(request, gettext("You must use a POST request for this operation"), status=404)

    if 'image_task_id' not in request.POST or not request.POST['image_task_id']:
        return _error_response(request, gettext("You should not change image task id"))

    if 'image_task_tag' not in request.POST or not request.POST['image_task_tag']:
        return _error_response(request, gettext("You should not change image task tag"))

    response_data = {
        "message": gettext("You've successfully submitted an image tagging subtask")
    }
    image_task = ImageSubTask.objects.get(id=request.POST['image_task_id'])
    task = UserImageTask.objects.filter(user=request.user, image_task=image_task)

    task_tag = request.POST['image_task_tag']
    json_tag = json.loads(task_tag)
    # user submit an empty tag, we don't delete it in database, just update it
    if len(json_tag["objects"]) == 0:
        if task.count() != 0:
            response_data = {
                "message": gettext("You've successfully deleted an image tagging subtask")
            }
    else:
        if task.count() == 0:
            new_image_tag = UserImageTask(image_task=image_task,
                                          user_image_task_tag=task_tag,
                                          user=request.user)
            new_image_tag.save()
            parent_task = ImageTask.objects.get(sub_tasks=image_task)
            if is_user_completed_all_image_task(request.user, parent_task):
                response_data = {
                    "message": gettext("You have completed all sub-tasks for task " + parent_task.task_name + "!")
                }
                # add money into user's account
                # when this user first finished all subtasks in this task
                # and this task still has available position to get money
                if image_task_completed_count(parent_task) <= parent_task.task_number:
                    add_money_to_user(request, parent_task.task_money / parent_task.task_number)
        else:
            task = task.first()
            task.user_image_task_tag = task_tag
            task.save()

    response = HttpResponse(json.dumps(response_data), content_type='application/json')
    response['Access-Control-Allow-Origin'] = '*'
    return response


@login_required
def image_export_action(request, image_subtaskid):
    image_subtask = ImageSubTask.objects.get(id=image_subtaskid)
    if not image_subtask:
        return _error_response(request, gettext("Invalid image subtask id"))

    parent_task = ImageTask.objects.get(sub_tasks=image_subtask)
    if parent_task.task_creator != request.user:
        return _error_response(request, gettext("You are not the creator of this task"))

    finished_img_subtasks = UserImageTask.objects.filter(image_task=image_subtask)
    finished_task_count = finished_img_subtasks.count()
    if finished_task_count == 0:
        return _error_response(request, gettext("No result yet for this task"))

    image_results = []
    for finished_subtask in finished_img_subtasks:
        image_results.append(json.loads(finished_subtask.user_image_task_tag))
    file_data = json.dumps(image_results)
    response = HttpResponse(file_data, content_type='application/text charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="Result for ' + image_subtask.image_task_tag + '.txt"'
    return response


def image_task_completed_count(image_task):
    all_completed_user_count = 0
    for user in User.objects.all():
        if is_user_completed_all_image_task(user, image_task):
            all_completed_user_count += 1
    return all_completed_user_count


####################
# pos task actions #
####################

@login_required
def pos_all_tasks_action(request, page_num):
    all_tasks = POSTask.objects.all()[::-1]
    page_count = 1 + math.ceil(len(all_tasks) / POS_PAGE_CNT)
    if page_num < 1 or page_num >= page_count:
        page_num = 1
    page_lower = max(1, page_num - PAGE_DELTA)
    page_upper = min(page_count, page_num + PAGE_DELTA)
    tasks = all_tasks[(page_num - 1) * POS_PAGE_CNT:page_num * POS_PAGE_CNT]
    for task in tasks:
        task.count = task.possubtask_set.count()
        if task.task_money and task.task_people:
            # if the number people who completed this task has reached the goal, set reward to 0.0
            if pos_task_completed_count(task) >= task.task_people:
                task.reward = 0.0
            else:
                task.reward = round(task.task_money / task.task_people, 2)
        else:
            task.reward = 0.0
        task.finished = is_user_completed_all_pos_task(request.user, task)
    context = {
        'pageName': gettext('All POS Tasks'),
        'user': request.user,
        'tasks': tasks,
        'pageRange': range(page_lower, page_upper),
        'currPage': page_num
    }
    return render(request, 'crowdsourcedtagging/pos_task_list.html', context)


@login_required
def pos_sub_tasks_action(request, taskid):
    task = POSTask.objects.filter(id=taskid)
    if not task:
        return _error_response(request, gettext("Invalid POS subtask"))
    task = task.get()
    pos_tasks = task.possubtask_set.all()
    if not pos_tasks or pos_tasks.count() == 0:
        return _error_response(request, gettext("Empty POS subtask"))
    # get all sub pos tasks
    context = {
        'pageName': gettext('Sentences for ') + task.task_name,
        'user': request.user,
        "pos_tasks": pos_tasks
    }
    return render(request, 'crowdsourcedtagging/pos_sub_task_list.html', context)


@login_required
def pos_single_task_action(request, pos_taskid):
    pos_task = POSSubTask.objects.filter(id=pos_taskid)
    if not pos_task:
        return _error_response(request, gettext("Invalid POS task"))
    pos_task = pos_task.get()
    pos_task.words = word_tokenize(pos_task.pos_task_text)

    if pos_task.parent_task.task_creator == request.user:
        # when this task is created by request.user, navigate to creator view
        pos_finished_tasks = UserPosTask.objects.filter(pos_task=pos_task)
        finished_task_count = pos_finished_tasks.count()

        # Get all results for this task
        pos_results = [defaultdict(int) for _ in range(len(pos_task.words))]
        for finished_task in pos_finished_tasks:
            result = finished_task.pos_task_dict.split(",")
            for (idx, each_result) in enumerate(result):
                pos_results[idx][each_result] += 1

        # Convert result into percentage
        for pos_result in pos_results:
            for (k, v) in pos_result.items():
                pos_result[k] = round(v / finished_task_count * 100, 1)

        context = {
            'pageName': gettext('POS Task for ') + pos_task.pos_task_name,
            'user': request.user,
            'pos_task': pos_task,
            'pos_dict': POS_DICT,
            'pos_color_dict': POS_COLOR_DICT,
            'pos_task_finished_count': finished_task_count,
            'pos_task_all_count': pos_task.parent_task.task_people,
            'pos_task_progress': finished_task_count / pos_task.parent_task.task_people * 100.0,
            'pos_result': pos_results
        }

        return render(request, 'crowdsourcedtagging/pos_single_task_creator.html', context)
    else:
        # when this task is NOT created by request.user, navigate to tag view
        context = {
            'pageName': gettext('POS Task for ') + pos_task.pos_task_name,
            'user': request.user,
            'pos_task': pos_task,
            'pos_dict': POS_DICT,
        }

        # if the user has finished this task, display the user's old choices
        pos_user_task = UserPosTask.objects.filter(user=request.user, pos_task_id=pos_taskid)
        if pos_user_task.count() > 0:
            context['prev_selection'] = pos_user_task.first().pos_task_dict.split(",")

        return render(request, 'crowdsourcedtagging/pos_single_task.html', context)


@login_required
@ensure_csrf_cookie
def pos_tag_action(request):
    if request.method != 'POST':
        return _error_response(request, gettext("You must use a POST request for this operation"), status=404)

    if 'pos_task_id' not in request.POST or not request.POST['pos_task_id']:
        return _error_response(request, gettext("Invalid POS task id"))

    pos_selections = []
    for (k, v) in request.POST.items():
        if k.startswith('pos_selection'):
            pos_selections.append(v)
    if len(pos_selections) == 0:
        return _error_response(request, "Empty POS tag result")
    if any(x not in POS_DICT.keys() for x in pos_selections):
        return _error_response(request, "Invalid POS tag result")
    pos_selection_str = ','.join(pos_selections)

    pos_task_id = request.POST['pos_task_id']
    pos_task = POSSubTask.objects.get(id=pos_task_id)
    words = word_tokenize(pos_task.pos_task_text)
    if len(pos_selections) != len(words):
        return _error_response(request, "Tagging count mismatched")
    parent_task = pos_task.parent_task
    task = UserPosTask.objects.filter(user=request.user, pos_task=pos_task)
    if task.count() == 0:
        new_pos_task = UserPosTask(pos_task=pos_task, user=request.user, pos_task_dict=pos_selection_str)
        new_pos_task.save()

        if is_user_completed_all_pos_task(request.user, parent_task):
            context = {
                "pageName": gettext("Congratulations!"),
                "message": gettext("You have completed all sub-tasks for task " + parent_task.task_name + "!")
            }
            # add money into user's account
            # when this user first finished all subtasks in this task
            # and this task still has available position to get money
            if pos_task_completed_count(parent_task) <= parent_task.task_people:
                add_money_to_user(request, parent_task.task_money / parent_task.task_people)
            return render(request, "crowdsourcedtagging/completion.html", context)
    else:
        # modify previous result
        task = task.first()
        task.pos_task_dict = pos_selection_str
        task.save()

    if pos_task.next_task_id:
        return pos_single_task_action(request, pos_task.next_task_id)
    else:
        return redirect('possublist', parent_task.id)


@login_required
@ensure_csrf_cookie
def pos_export_action(request):
    if request.method != 'POST':
        return _error_response(request, gettext("You must use a POST request for this operation"), status=404)

    if 'pos_task_id' not in request.POST or not request.POST['pos_task_id']:
        return _error_response(request, gettext("Invalid POS task id"))

    pos_task_id = request.POST['pos_task_id']
    pos_task = POSSubTask.objects.get(id=pos_task_id)

    if not pos_task:
        return _error_response(request, gettext("Invalid POS task id"))
    if pos_task.parent_task.task_creator != request.user:
        return _error_response(request, gettext("You are not the creator of this task"))

    # Get all results for this task
    pos_finished_tasks = UserPosTask.objects.filter(pos_task=pos_task)
    finished_task_count = pos_finished_tasks.count()
    if finished_task_count == 0:
        return _error_response(request, gettext("No result yet for this task"))
    else:
        words = word_tokenize(pos_task.pos_task_text)
        pos_results = [(words[i], defaultdict(int)) for i in range(len(words))]
        for finished_task in pos_finished_tasks:
            result = finished_task.pos_task_dict.split(",")
            for (idx, each_result) in enumerate(result):
                pos_results[idx][1][POS_DICT[each_result]] += 1

        # Convert result into percentage
        for (_, pos_result) in pos_results:
            for (k, v) in pos_result.items():
                pos_result[k] = round(v / finished_task_count, 2)

        # Generate a file for download
        file_data = json.dumps(pos_results)
        response = HttpResponse(file_data, content_type='application/text charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="Result for ' + pos_task.pos_task_name + '.txt"'
        return response


def pos_task_completed_count(pos_task):
    all_completed_user_count = 0
    for user in User.objects.all():
        if is_user_completed_all_pos_task(user, pos_task):
            all_completed_user_count += 1
    return all_completed_user_count


#######################
# upload task actions #
#######################

@login_required
def upload_image_action(request):
    context = {
        'pageName': gettext("Upload Image Task")
    }
    if request.method == "GET":
        context['form'] = UploadImageForm()
        profile = get_profile(request)
        context['money'] = round(profile.money, 2)
        return render(request, 'crowdsourcedtagging/upload_image.html', context)
    else:
        for key in ["task_name", "task_description", "task_money", "task_number", "task_content"]:
            if key not in request.POST or not request.POST[key]:
                return _error_response(request, "Upload Image form is not complete")
        try:
            task_money = float(request.POST["task_money"])
            task_number = int(request.POST["task_number"])
        except:
            return _error_response(request, "Invalid money or number of tasks in form")
        # save parent task
        task_name = request.POST["task_name"]
        task_description = request.POST["task_description"]
        image_task = ImageTask()
        image_task.task_name = task_name
        image_task.task_description = task_description
        image_task.task_number = task_number
        image_task.task_creator = request.user
        image_task.task_money = task_money
        image_task.save()
        # save sub tasks
        image_urls = request.POST["task_content"].splitlines()
        for (idx, image_url) in enumerate(image_urls):
            sub_task = ImageSubTask()
            sub_task.image_task_url = image_url
            sub_task.image_task_description = task_description
            sub_task.image_task_tag = task_name
            sub_task.save()
            if idx != 0:
                sub_task.prev_task_id = sub_task.id - 1
            if idx != len(image_urls) - 1:
                sub_task.next_task_id = sub_task.id + 1
            sub_task.save()
            image_task.sub_tasks.add(sub_task)
        image_task.save()
        context['form'] = UploadImageForm()
        context['message'] = gettext("Successfully uploaded task ") + task_name + "!"
        context['image_task_id'] = image_task.id
        # deduct money from user's account
        deduct_money_from_user(request, image_task.task_money)
        return render(request, 'crowdsourcedtagging/upload_image.html', context)


@login_required
def upload_pos_action(request):
    context = {
        'pageName': gettext("Upload POS Task")
    }
    if request.method == "GET":
        context['form'] = UploadPOSForm()
        profile = get_profile(request)
        context['money'] = round(profile.money, 2)
        return render(request, 'crowdsourcedtagging/upload_pos.html', context)
    else:
        for key in ["task_name", "task_description", "task_money", "task_number", "task_content"]:
            if key not in request.POST or not request.POST[key]:
                return _error_response(request, "Upload POS form is not complete")
        try:
            task_money = float(request.POST["task_money"])
            task_number = int(request.POST["task_number"])
        except:
            return _error_response(request, "Invalid money or number of tasks in form")
        # save parent task
        task_name = request.POST["task_name"]
        task_description = request.POST["task_description"]
        pos_task = POSTask()
        pos_task.task_name = task_name
        pos_task.task_description = task_description
        pos_task.task_creator = request.user
        pos_task.task_money = task_money
        pos_task.task_people = task_number
        pos_task.save()
        # save sub tasks
        sentences = sent_tokenize(request.POST["task_content"])
        for (idx, sentence) in enumerate(sentences):
            sub_task = POSSubTask()
            sub_task.pos_task_text = sentence
            sub_task.pos_task_description = task_description
            sub_task.pos_task_name = task_name
            sub_task.parent_task = pos_task
            sub_task.save()
            if idx != 0:
                sub_task.prev_task_id = sub_task.id - 1
            if idx != len(sentences) - 1:
                sub_task.next_task_id = sub_task.id + 1
            sub_task.save()
        context['form'] = UploadPOSForm()
        context['message'] = gettext("Successfully uploaded task ") + task_name + "!"
        context['pos_task_id'] = pos_task.id
        # deduct money from user's account
        deduct_money_from_user(request, pos_task.task_money)
        return render(request, 'crowdsourcedtagging/upload_pos.html', context)


###################
# utility actions #
###################

@login_required
def profile_action(request, userid):
    if userid == request.user.id:
        profile_owner = request.user
        profile = get_profile(request)
    else:
        profile_owner = User.objects.filter(id=userid)
        if profile_owner.count() == 0:
            return _error_response(request, "Invalid user id")
        profile_owner = profile_owner.first()
        profile = get_profile_byid(request, userid)

    context = {
        'pageName': gettext("Profile Page for ") + profile_owner.username,
    }

    if request.method == "GET":
        form = ProfileForm(instance=profile)
        profile = get_profile_byid(request, profile_owner.id)
        infoform = InformationForm(instance=profile_owner)
        context['money'] = round(profile.money, 2)
        context['infoform'] = infoform
    else:  # POST
        if userid != request.user.id:
            return _error_response(request, gettext("This profile does not belong to you."))
        if request.FILES and "profile_picture" in request.FILES:
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                profile.profile_picture = form.cleaned_data["profile_picture"]
                profile.content_type = form.cleaned_data["profile_picture"].content_type
                form.save()
                profile.save()
            infoform = InformationForm(instance=profile_owner)
            context['infoform'] = infoform
        elif "profile_picture" in request.POST and request.POST["profile_picture"] == '':
            # empty upload
            form = ProfileForm(instance=profile)
            infoform = InformationForm(instance=profile_owner)
            context['infoform'] = infoform
        else:  # request for change user information
            if Profile.objects.filter(user_id=profile_owner.id).exists():
                profile = get_profile_byid(request, profile_owner.id)
                form = ProfileForm(instance=profile)
            else:
                profile = get_profile_byid(request, profile_owner.id)
                form = ProfileForm(profile)
            infoform = InformationForm(request.POST, instance=profile_owner)
            if not infoform.is_valid():
                return _error_response(request, "The form is not valid!")
            thisuser = profile_owner
            thisuser.username = infoform.cleaned_data['username'] if infoform.cleaned_data[
                'username'] else profile_owner.username
            thisuser.last_name = infoform.cleaned_data['last_name'] if infoform.cleaned_data[
                'last_name'] else profile_owner.last_name
            thisuser.first_name = infoform.cleaned_data['first_name'] if infoform.cleaned_data[
                'first_name'] else profile_owner.first_name
            infoform.save()
            context['pageName'] = gettext("Profile Page for " + thisuser.username)
            context['infoform'] = infoform

    # basic utility
    context['form'] = form
    context['money_form'] = AddMoneyForm()
    context['profile'] = profile
    context['greeting'] = get_time_greeting()

    # finished tasks utility
    tasks_list = ""
    img_task_objlist = UserImageTask.objects.filter(user_id=profile_owner.id)
    img_task_count = img_task_objlist.count()
    for obj in img_task_objlist:
        mainimg_obj = get_parent_img(obj)
        tasks_list += "Image Task," + mainimg_obj.task_name + "\n"

    pos_task_objlist = UserPosTask.objects.filter(user_id=profile_owner.id)
    pos_task_count = pos_task_objlist.count()
    for obj in pos_task_objlist:
        mainposobj = get_parent_POS(obj)
        tasks_list += "POS Task," + mainposobj.task_name + "\n"

    context['img_tasks_number'] = img_task_count
    context['pos_tasks_number'] = pos_task_count
    context['tasks_list'] = tasks_list

    # money utility in profile
    try:
        MoneyRecord.objects.get(user=profile_owner)
    except MoneyRecord.DoesNotExist:
        changelist = datetime.datetime.now().isoformat(' ', 'seconds') + ',' + str(profile.money) + '\n'
        MoneyRecord.objects.create(user=profile_owner, money=changelist).save()
    context['money_changelist'] = get_money_changelist(profile_owner)
    context['money'] = round(profile.money, 2)

    # uploaded tasks
    upload_list = ""
    img_upload_objlist = ImageTask.objects.filter(task_creator_id=profile_owner.id)
    img_upload_count = img_upload_objlist.count()
    for obj in img_upload_objlist:
        mainimg_obj = obj
        subimg_count = mainimg_obj.sub_tasks.count()
        upload_list += "Image Task," + mainimg_obj.task_name + "," + str(subimg_count) + "\n"

    pos_upload_objlist = POSTask.objects.filter(task_creator_id=profile_owner.id)
    pos_upload_count = pos_upload_objlist.count()
    for obj in pos_upload_objlist:
        mainposobj = obj
        subpos_count = POSSubTask.objects.filter(parent_task=mainposobj).count()
        upload_list += "POS Task," + mainposobj.task_name + "," + str(subpos_count) + "\n"

    context['img_upload_number'] = img_upload_count
    context['pos_upload_number'] = pos_upload_count
    context['upload_list'] = upload_list

    return render(request, 'crowdsourcedtagging/my_profile.html', context)


def get_profile_byid(request, userid):
    profile = Profile.objects.get(user_id=userid)
    # if the profile doesn't exist
    if not profile:
        try:
            user = User.objects.get(id=userid)
        except:
            return _error_response(request, gettext("No such user."))

        new_profile = Profile.objects.create(user=user)
        new_profile.save()
        profile = new_profile
    return profile


def login_action(request):
    context = {
        'pageName': gettext("Login"),
        'form': LoginForm()
    }
    if request.method == "GET":
        return render(request, 'crowdsourcedtagging/login.html', context)

    form = LoginForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, 'crowdsourcedtagging/login.html', context)

    new_user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
    if new_user:
        login(request, new_user)
        return redirect(reverse('home'))
    else:
        return render(request, 'crowdsourcedtagging/login.html', context)


@transaction.atomic
def register_action(request):
    context = {
        'pageName': gettext("Register"),
        'form': RegisterForm()
    }
    if request.method == "GET":
        return render(request, 'crowdsourcedtagging/register.html', context)

    form = RegisterForm(request.POST)
    context['form'] = form
    if not form.is_valid():
        return render(request, 'crowdsourcedtagging/register.html', context)

    new_user = User.objects.create_user(username=form.cleaned_data['username'],
                                        password=form.cleaned_data['password'],
                                        email=form.cleaned_data['email'])
    new_user.save()
    # add an empty profile for this user
    new_profile = Profile.objects.create(user=new_user)
    new_profile.save()

    new_user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
    if new_user:
        login(request, new_user)
        return redirect(reverse('home'))
    else:
        return render(request, 'crowdsourcedtagging/register.html', context)


@login_required
def logout_action(request):
    logout(request)
    return redirect(reverse('login'))


@login_required
def avatar_action(request, userid):
    profile = get_object_or_404(Profile, user_id=userid)
    if not profile.profile_picture:
        return Http404
    return HttpResponse(profile.profile_picture, content_type=profile.content_type)


def get_profile(request):
    profile = request.user.profile.first()
    # if the profile doesn't exist
    if not profile:
        try:
            user = User.objects.get(username=request.user)
        except:
            return _error_response(request, gettext("No such user."))

        new_profile = Profile.objects.create(user=user)
        new_profile.save()
        profile = new_profile
    return profile


@login_required
@ensure_csrf_cookie
def add_money_action(request):
    if request.method != "POST":
        return _error_response(request, gettext("You must use POST for this method"))
    if not request.POST["amount"]:
        return _error_response(request, gettext("Amount not in request"))
    try:
        amount_num = float(request.POST["amount"])
        add_money_to_user(request, amount_num)
        return redirect(reverse('profile', kwargs={'userid': request.user.id}))
    except:
        return _error_response(request, gettext("Invalid amount number"))


@transaction.atomic
def add_money_to_user(request, amount):
    profile = get_profile(request)
    profile.money += amount
    profile.save()
    update_money_changelist(request.user, datetime.datetime.now().isoformat(' ', 'seconds'), profile.money)


@transaction.atomic
def deduct_money_from_user(request, amount):
    profile = get_profile(request)
    if profile.money < amount:
        return None
    profile.money -= amount
    profile.save()
    update_money_changelist(request.user, datetime.datetime.now().isoformat(' ', 'seconds'), profile.money)


def get_time_greeting():
    now = datetime.datetime.now()
    if now.hour < 12:
        greeting = gettext('Good morning,')
    elif 12 <= now.hour < 18:
        greeting = gettext('Good afternoon,')
    else:
        greeting = gettext('Good evening,')
    print(greeting,now)
    return greeting


@login_required
def finished_img_task(request, userid):
    image_tasks_ids = list()
    image_tasks_time = dict()
    for image in UserImageTask.objects.filter(user_id=userid):
        image_tasks_ids.append(image.image_task_id)
        image_tasks_time[image.image_task_id] = image.time

    image_tasks = ImageSubTask.objects.filter(id__in=image_tasks_ids)
    try:
        thisuser = User.objects.get(id=userid)
    except User.DoesNotExist:
        return _error_response(request,gettext("No such user."))
    context = {
        'pageName': gettext("{}'s Finished Image Tasks").format(thisuser.username),
        'user': request.user,
        "image_tasks": image_tasks,
        "time": image_tasks_time
    }
    return render(request, 'crowdsourcedtagging/image_sub_task_list.html', context)


@login_required
def finished_img_sub_task(request, taskname):
    image_tasks_ids = list()
    image_tasks_time = dict()

    img_task_objlist = UserImageTask.objects.filter(user_id=request.user.id)

    image_tasks_ids = []
    for image in img_task_objlist:
        mainimg_obj = get_parent_img(image)
        if taskname == mainimg_obj.task_name:
            image_tasks_ids.append(image.image_task_id)
            image_tasks_time[image.image_task_id] = image.time

    image_tasks = ImageSubTask.objects.filter(id__in=image_tasks_ids)

    context = {
        'pageName': gettext('Your finished Image Task for ') + taskname,
        'user': request.user,
        "image_tasks": image_tasks,
        "time": image_tasks_time
    }
    return render(request, 'crowdsourcedtagging/image_sub_task_list.html', context)


@login_required
def finished_pos_task(request, userid):
    pos_tasks_ids = list()
    pos_tasks_time = dict()

    for pos in UserPosTask.objects.filter(user_id=userid):
        pos_tasks_ids.append(pos.pos_task_id)
        pos_tasks_time[pos.pos_task_id] = pos.time

    pos_tasks = POSSubTask.objects.filter(id__in=pos_tasks_ids)

    try:
        thisuser = User.objects.get(id=userid)
    except User.DoesNotExist:
        return _error_response(request,gettext("No such user."))

    context = {
        'pageName': gettext("{}'s Finished POS Tasks").format(thisuser.username),
        'user': request.user,
        "pos_tasks": pos_tasks,
        "time": pos_tasks_time
    }
    return render(request, 'crowdsourcedtagging/pos_sub_task_list.html', context)


@login_required
def finished_pos_sub_task(request, taskname):
    pos_tasks_ids = list()
    pos_tasks_time = dict()

    pos_task_objlist = UserPosTask.objects.filter(user_id=request.user.id)

    pos_tasks_ids = []
    for pos in pos_task_objlist:
        mainimg_obj = get_parent_POS(pos)
        if taskname == mainimg_obj.task_name:
            pos_tasks_ids.append(pos.pos_task_id)
            pos_tasks_time[pos.pos_task_id] = pos.time

    pos_tasks = POSTask.objects.filter(id__in=pos_tasks_ids)

    context = {
        'pageName': gettext('Your finished POS Task for ') + taskname,
        'user': request.user,
        "image_tasks": pos_tasks,
        "time": pos_tasks_time
    }
    return render(request, 'crowdsourcedtagging/image_sub_task_list.html', context)


@login_required
def uploaded_img_task(request, userid, page_num):
    # get all image tasks
    try:
        thisuser = User.objects.get(id=userid)
    except User.DoesNotExist:
        return _error_response(request,gettext("No such user."))

    all_tasks = ImageTask.objects.filter(task_creator_id=userid)
    page_count = 1 + math.ceil(len(all_tasks) / IMG_PAGE_CNT)
    if page_num < 1 or page_num >= page_count:
        page_num = 1
    page_lower = max(1, page_num - PAGE_DELTA)
    page_upper = min(page_count, page_num + PAGE_DELTA)
    tasks = all_tasks[(page_num - 1) * IMG_PAGE_CNT:page_num * IMG_PAGE_CNT]
    for task in tasks:
        sub_tasks = task.sub_tasks.all()
        task.count = sub_tasks.count()
        if task.task_money and task.task_number:
            task.reward = round(task.task_money / task.task_number, 2)
        else:
            task.reward = 0.0
        task.url = sub_tasks.first().image_task_url
    context = {
        'pageName': gettext("{}'s Uploaded Image Tasks").format(thisuser.username),
        'user': thisuser,
        'tasks': tasks,
        'pageRange': range(page_lower, page_upper),
        'currPage': page_num,
    }
    return render(request, 'crowdsourcedtagging/image_task_list.html', context)


@login_required
def uploaded_pos_task(request, userid, page_num):
    try:
        thisuser = User.objects.get(id=userid)
    except User.DoesNotExist:
        return _error_response(request,gettext("No such user."))

    all_tasks = POSTask.objects.filter(task_creator_id=userid)
    page_count = 1 + math.ceil(len(all_tasks) / POS_PAGE_CNT)
    if page_num < 1 or page_num >= page_count:
        page_num = 1
    page_lower = max(1, page_num - PAGE_DELTA)
    page_upper = min(page_count, page_num + PAGE_DELTA)
    tasks = all_tasks[(page_num - 1) * POS_PAGE_CNT:page_num * POS_PAGE_CNT]

    for task in tasks:
        task.count = task.possubtask_set.count()
        if task.task_money and task.task_people:
            # if the number people who completed this task has reached the goal, set reward to 0.0
            if pos_task_completed_count(task) >= task.task_people:
                task.reward = 0.0
            else:
                task.reward = round(task.task_money / task.task_people, 2)
        else:
            task.reward = 0.0
        task.finished = is_user_completed_all_pos_task(thisuser, task)
    context = {
        'pageName': gettext("{}'s Uploaded POS Tasks").format(thisuser.username),
        'user': thisuser,
        'tasks': tasks,
        'pageRange': range(page_lower, page_upper),
        'currPage': page_num
    }
    return render(request, 'crowdsourcedtagging/pos_task_list.html', context)


def is_user_completed_all_image_task(user, parent_task):
    all_subtasks = ImageTask.objects.get(id=parent_task.id).sub_tasks.all()
    task_count = UserImageTask.objects.filter(user=user, image_task__in=all_subtasks).count()
    return task_count == all_subtasks.count()


def is_user_completed_all_pos_task(user, parent_task):
    all_subtasks = POSSubTask.objects.filter(parent_task=parent_task)
    task_count = UserPosTask.objects.filter(user=user, pos_task__in=all_subtasks).count()
    return task_count == all_subtasks.count()


##################
# error checking #
##################

def _error_response(request, message, status=200):
    context = {
        'pageName': gettext('Error'),
        'errors': [message]
    }
    return render(request, 'crowdsourcedtagging/errors.html', context)


def error_404(request, exception):
    return render(request, 'crowdsourcedtagging/404.html', {})


##########
# helper #
##########


def get_parent_img(img_obj):
    subimage_task = ImageSubTask.objects.get(id=img_obj.image_task_id)
    mainimg_obj = ImageTask.objects.get(sub_tasks=subimage_task)
    return mainimg_obj


def get_parent_POS(POS_obj):
    subpos_task = POSSubTask.objects.get(id=POS_obj.pos_task_id)
    mainposobj = subpos_task.parent_task
    return mainposobj


def update_money_changelist(user, time, balance):
    try:
        user_record = MoneyRecord.objects.get(user=user)
    except:
        changelist = time + ',' + str(user.profile.get().money) + '\n'
        user_record = MoneyRecord.objects.create(user=user, money=changelist)
        user_record.save()

    changelist = user_record.money
    changelist += (time + ',' + str(balance) + '\n')
    user_record.money = changelist
    user_record.save()


def get_money_changelist(user):
    user_record = MoneyRecord.objects.get(user=user)
    return user_record.money


def mylang(request):
    return HttpResponse("request.LANGUAGE_CODE = %s\n" % request.LANGUAGE_CODE)


def redirect_profile(request, redirect_page):
    if "uploaded_img_task" in redirect_page or "uploaded_pos_task" in redirect_page:
        pagename = '_'.join(redirect_page.split('_')[:-1])
        user_id = redirect_page.split('_')[-1]
        return redirect(reverse(pagename, kwargs={"userid": user_id, "page_num": 1}))
    if "finished_img_sub_task" in redirect_page or "finished_pos_sub_task" in redirect_page:
        return redirect(reverse(redirect_page))
    if "finished_img_task" in redirect_page:
        user_id = redirect_page.split('_')[-1]
        return redirect(reverse('finished_img_task', kwargs={"userid": user_id}))
    if "finished_pos_task" in redirect_page:
        user_id = redirect_page.split('_')[-1]
        return redirect(reverse('finished_pos_task', kwargs={"userid": user_id}))
    return render(request, "crowdsourcedtagging/404.html", {})
