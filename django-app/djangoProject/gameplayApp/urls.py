from django.urls import path
from . import views

urlpatterns = [
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
]
