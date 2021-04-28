from crowdsourcedtagging import views
from django.urls import path
from django.contrib.auth import views as auth_views

handler404 = views.error_404

urlpatterns = [
    path('', views.home, name='home'),
    path('login', views.login_action, name='login'),
    path('login_google', auth_views.logout_then_login, name='login_google'),
    path('register', views.register_action, name='register'),
    path('logout', views.logout_action, name='logout'),
    path('profile/<int:userid>', views.profile_action, name='profile'),
    path('profile/<str:redirect_page>', views.redirect_profile, name='redirect_page'),
    path('get_avatar/<int:userid>', views.avatar_action, name='avatar'),
    path('image_task_list/<int:page_num>', views.image_all_tasks_action, name='imagetasklist'),
    path('image_sub_task_list/<int:taskid>', views.image_sub_tasks_action, name='imagesublist'),
    path('image_single_task/<int:image_taskid>', views.image_single_task_action, name='imagesingletask'),
    path('image_tag', views.image_tag_action, name='imagetag'),
    path('pos_task_list/<int:page_num>', views.pos_all_tasks_action, name='postasklist'),
    path('pos_sub_task_list/<int:taskid>', views.pos_sub_tasks_action, name='possublist'),
    path('pos_single_task/<int:pos_taskid>', views.pos_single_task_action, name='possingletask'),
    path('pos_tag', views.pos_tag_action, name='postag'),
    path('finished_img_task/<int:userid>', views.finished_img_task, name='finished_img_task'),
    path('finished_pos_task/<int:userid>', views.finished_pos_task, name='finished_pos_task'),
    path('finished_img_sub_task', views.finished_img_sub_task, name='finished_img_sub_task'),
    path('finished_pos_sub_task', views.finished_pos_sub_task, name='finished_pos_sub_task'),
    path('uploaded_img_task/<int:userid>/<int:page_num>', views.uploaded_img_task, name='uploaded_img_task'),
    path('uploaded_pos_task/<int:userid>/<int:page_num>', views.uploaded_pos_task, name='uploaded_pos_task'),
    path('upload_image_task', views.upload_image_action, name='upload_image_task'),
    path('export_image_task/<int:image_subtaskid>', views.image_export_action, name='export_image_task'),
    path('upload_pos_task', views.upload_pos_action, name='upload_pos_task'),
    path('export_pos_task', views.pos_export_action, name='export_pos_task'),
    path('add_money', views.add_money_action, name='add_money_to_user'),
    path('mylang', views.mylang, name='mylang'),
]
