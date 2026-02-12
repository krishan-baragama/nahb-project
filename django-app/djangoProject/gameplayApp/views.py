"""
Level 10 Views - All functionality for MVP
"""
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .models import Play
from collections import Counter

FLASK_API = settings.FLASK_API_URL


# ========== BROWSING VIEWS ==========

def story_list(request):
    """Display all published stories"""
    try:
        response = requests.get(f'{FLASK_API}/stories?status=published', timeout=5)
        stories = response.json() if response.status_code == 200 else []
    except:
        stories = []
        messages.error(request, 'Cannot connect to Flask API on port 5000!')
    
    return render(request, 'gameplay/story_list.html', {'stories': stories})


def story_detail(request, story_id):
    """Display single story details"""
    try:
        response = requests.get(f'{FLASK_API}/stories/{story_id}', timeout=5)
        story = response.json() if response.status_code == 200 else None
    except:
        story = None
        messages.error(request, 'Cannot load story')
    
    return render(request, 'gameplay/story_detail.html', {'story': story})


# ========== PLAYING VIEWS ==========

def play_story(request, story_id):
    """Start playing a story"""
    try:
        response = requests.get(f'{FLASK_API}/stories/{story_id}/start', timeout=5)
        if response.status_code == 200:
            page_data = response.json()
            return render(request, 'gameplay/play_story.html', {
                'story_id': story_id,
                'page': page_data
            })
        else:
            messages.error(request, 'Story has no starting page')
            return redirect('story_list')
    except:
        messages.error(request, 'Cannot connect to Flask API')
        return redirect('story_list')


def get_page(request, page_id):
    """Get next page and save play if ending"""
    try:
        response = requests.get(f'{FLASK_API}/pages/{page_id}', timeout=5)
        page_data = response.json() if response.status_code == 200 else None
        
        # If ending reached, save Play record
        if page_data and page_data.get('is_ending'):
            Play.objects.create(
                story_id=page_data['story_id'],
                ending_page_id=page_id
            )
            messages.success(request, '🎉 You reached the ending!')
        
        return render(request, 'gameplay/play_story.html', {
            'story_id': page_data.get('story_id') if page_data else None,
            'page': page_data
        })
    except:
        messages.error(request, 'Cannot load page')
        return redirect('story_list')


# ========== STATISTICS VIEW ==========

def statistics(request):
    """Show gameplay statistics"""
    plays = Play.objects.all()
    
    # Count plays per story
    story_plays = Counter(plays.values_list('story_id', flat=True))
    
    # Get story details from Flask
    story_details = {}
    for story_id in story_plays.keys():
        try:
            response = requests.get(f'{FLASK_API}/stories/{story_id}', timeout=5)
            if response.status_code == 200:
                story_details[story_id] = response.json()
        except:
            pass
    
    # Calculate ending distribution
    ending_distribution = {}
    for story_id in story_plays.keys():
        story_endings = plays.filter(story_id=story_id)
        ending_counts = Counter(story_endings.values_list('ending_page_id', flat=True))
        total = sum(ending_counts.values())
        
        ending_distribution[story_id] = {
            ending_id: {
                'count': count,
                'percentage': round(count / total * 100, 1)
            }
            for ending_id, count in ending_counts.items()
        }
    
    return render(request, 'gameplay/statistics.html', {
        'story_plays': dict(story_plays),
        'story_details': story_details,
        'ending_distribution': ending_distribution,
        'total_plays': plays.count()
    })


# ========== CREATION VIEWS ==========

def create_story(request):
    """Create new story"""
    if request.method == 'POST':
        data = {
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'status': 'published'
        }
        try:
            response = requests.post(f'{FLASK_API}/stories', json=data, timeout=5)
            if response.status_code == 201:
                messages.success(request, '✅ Story created!')
                story = response.json()
                return redirect('edit_story', story_id=story['id'])
            else:
                messages.error(request, 'Failed to create story')
        except:
            messages.error(request, 'Cannot connect to Flask API')
    
    return render(request, 'gameplay/create_story.html')


def edit_story(request, story_id):
    """Edit story - manage pages and choices"""
    try:
        # Get story
        response = requests.get(f'{FLASK_API}/stories/{story_id}', timeout=5)
        story = response.json() if response.status_code == 200 else None
        
        # Get pages
        response = requests.get(f'{FLASK_API}/stories/{story_id}/pages', timeout=5)
        pages = response.json() if response.status_code == 200 else []
        
        return render(request, 'gameplay/edit_story.html', {
            'story': story,
            'pages': pages
        })
    except:
        messages.error(request, 'Cannot load story')
        return redirect('story_list')


def create_page(request, story_id):
    """Add page to story"""
    if request.method == 'POST':
        data = {
            'text': request.POST.get('text'),
            'is_ending': request.POST.get('is_ending') == 'on'
        }
        try:
            response = requests.post(
                f'{FLASK_API}/stories/{story_id}/pages',
                json=data,
                timeout=5
            )
            if response.status_code == 201:
                messages.success(request, '✅ Page created!')
            else:
                messages.error(request, 'Failed to create page')
        except:
            messages.error(request, 'Cannot connect to Flask API')
    
    return redirect('edit_story', story_id=story_id)


def create_choice(request, page_id):
    """Add choice to page"""
    if request.method == 'POST':
        data = {
            'text': request.POST.get('text'),
            'next_page_id': int(request.POST.get('next_page_id'))
        }
        try:
            response = requests.post(
                f'{FLASK_API}/pages/{page_id}/choices',
                json=data,
                timeout=5
            )
            if response.status_code == 201:
                messages.success(request, '✅ Choice created!')
            else:
                error = response.json().get('error', 'Failed')
                messages.error(request, error)
        except:
            messages.error(request, 'Cannot connect to Flask API')
    
    # Redirect back to edit story
    try:
        response = requests.get(f'{FLASK_API}/pages/{page_id}', timeout=5)
        page_data = response.json()
        return redirect('edit_story', story_id=page_data['story_id'])
    except:
        return redirect('story_list')