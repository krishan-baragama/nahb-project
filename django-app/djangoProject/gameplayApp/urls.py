from django.urls import path
from . import views

urlpatterns = [
    # Authentication (Level 16)
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Browsing
    path('', views.story_list, name='story_list'),
    path('story/<int:story_id>/', views.story_detail, name='story_detail'),
    
    # Playing
    path('story/<int:story_id>/play/', views.play_story, name='play_story'),
    path('page/<int:page_id>/', views.get_page, name='get_page'),
    
    # Statistics
    path('statistics/', views.statistics, name='statistics'),
    
    # Creation
    path('story/create/', views.create_story, name='create_story'),
    path('story/<int:story_id>/edit/', views.edit_story, name='edit_story'),
    path('story/<int:story_id>/page/create/', views.create_page, name='create_page'),
    path('page/<int:page_id>/choice/create/', views.create_choice, name='create_choice'),

    # Level 18: Ratings & Reports
    path('story/<int:story_id>/rate/', views.rate_story, name='rate_story'),
    path('story/<int:story_id>/report/', views.report_story, name='report_story'),
    path('management/reports/', views.admin_reports, name='admin_reports'),
    path('management/story/<int:story_id>/suspend/', views.admin_suspend_story, name='admin_suspend_story'),

    # Level 20: Visualizations
    path('story/<int:story_id>/tree/', views.story_tree, name='story_tree'),
    path('story/<int:story_id>/paths/', views.player_path, name='player_path'),
]
