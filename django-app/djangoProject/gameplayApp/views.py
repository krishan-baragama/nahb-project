"""
Level 13 Views - Enhanced UX with search, auto-save, draft support
"""
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .models import Play, PlaySession
from collections import Counter
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

FLASK_API = settings.FLASK_API_URL


# ========== BROWSING VIEWS ==========

def story_list(request):
    """Display published stories with search"""
    search_query = request.GET.get('search', '')
    
    try:
        # Always fetch published stories only
        response = requests.get(f'{FLASK_API}/stories?status=published', timeout=5)
        stories = response.json() if response.status_code == 200 else []
        
        # Filter by search query (client-side)
        if search_query:
            stories = [s for s in stories if search_query.lower() in s['title'].lower()]
        
    except:
        stories = []
        messages.error(request, 'Cannot connect to Flask API on port 5000!')
    
    return render(request, 'gameplay/story_list.html', {
        'stories': stories,
        'search_query': search_query
    })


def story_detail(request, story_id):
    """Display single story details"""
    try:
        response = requests.get(f'{FLASK_API}/stories/{story_id}', timeout=5)
        story = response.json() if response.status_code == 200 else None
    except:
        story = None
        messages.error(request, 'Cannot load story')
    
    return render(request, 'gameplay/story_detail.html', {'story': story})


# ========== PLAYING VIEWS WITH AUTO-SAVE ==========

def play_story(request, story_id):
    """Start or resume playing a story"""
    session_key = request.session.session_key or request.session.create()
    
    # Check for existing session (resume)
    try:
        play_session = PlaySession.objects.get(
            session_key=session_key,
            story_id=story_id
        )
        # Resume from saved page
        try:
            response = requests.get(f'{FLASK_API}/pages/{play_session.current_page_id}', timeout=5)
            if response.status_code == 200:
                page_data = response.json()
                messages.info(request, '📖 Resumed from where you left off!')
                return render(request, 'gameplay/play_story.html', {
                    'story_id': story_id,
                    'page': page_data
                })
        except:
            pass
    except PlaySession.DoesNotExist:
        pass
    
    # Start from beginning
    try:
        response = requests.get(f'{FLASK_API}/stories/{story_id}/start', timeout=5)
        if response.status_code == 200:
            page_data = response.json()
            
            # Save initial session
            PlaySession.objects.update_or_create(
                session_key=session_key,
                story_id=story_id,
                defaults={'current_page_id': page_data['id']}
            )
            
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
    """Get next page with auto-save"""
    session_key = request.session.session_key or request.session.create()
    
    try:
        response = requests.get(f'{FLASK_API}/pages/{page_id}', timeout=5)
        page_data = response.json() if response.status_code == 200 else None
        
        if page_data:
            # Update session with current page
            PlaySession.objects.update_or_create(
                session_key=session_key,
                story_id=page_data['story_id'],
                defaults={'current_page_id': page_id}
            )
            
            # If ending reached, save Play record and delete session
            if page_data.get('is_ending'):
                Play.objects.create(
                    story_id=page_data['story_id'],
                    ending_page_id=page_id,
                    user=request.user if request.user.is_authenticated else None
                )
                
                # Delete the session (story completed)
                PlaySession.objects.filter(
                    session_key=session_key,
                    story_id=page_data['story_id']
                ).delete()
                
                ending_label = page_data.get('ending_label', 'The End')
                messages.success(request, f'🎉 You reached: {ending_label}!')
        
        return render(request, 'gameplay/play_story.html', {
            'story_id': page_data.get('story_id') if page_data else None,
            'page': page_data
        })
    except:
        messages.error(request, 'Cannot load page')
        return redirect('story_list')


# ========== STATISTICS VIEW ==========

def statistics(request):
    """Show gameplay statistics with percentages"""
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
    
    # Calculate ending distribution with labels
    ending_distribution = {}
    for story_id in story_plays.keys():
        story_endings = plays.filter(story_id=story_id)
        ending_counts = Counter(story_endings.values_list('ending_page_id', flat=True))
        total = sum(ending_counts.values())
        
        # Get ending labels
        endings_with_labels = {}
        for ending_id, count in ending_counts.items():
            try:
                response = requests.get(f'{FLASK_API}/pages/{ending_id}', timeout=5)
                if response.status_code == 200:
                    page_data = response.json()
                    label = page_data.get('ending_label', f'Ending #{ending_id}')
                    endings_with_labels[ending_id] = {
                        'label': label,
                        'count': count,
                        'percentage': round(count / total * 100, 1)
                    }
            except:
                endings_with_labels[ending_id] = {
                    'label': f'Ending #{ending_id}',
                    'count': count,
                    'percentage': round(count / total * 100, 1)
                }
        
        ending_distribution[story_id] = endings_with_labels
    
    return render(request, 'gameplay/statistics.html', {
        'story_plays': dict(story_plays),
        'story_details': story_details,
        'ending_distribution': ending_distribution,
        'total_plays': plays.count()
    })


# ========== CREATION VIEWS WITH DRAFT SUPPORT ==========

@login_required
def create_story(request):
    """Create new story (defaults to draft)"""
    if request.method == 'POST':
        data = {
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'status': 'draft',  # Level 13: default to draft
            'author_id': request.user.id
        }
        try:
            response = requests.post(f'{FLASK_API}/stories', json=data, headers={'X-API-KEY': settings.FLASK_API_KEY}, timeout=5)
            if response.status_code == 201:
                messages.success(request, '✅ Story created as draft!')
                story = response.json()
                return redirect('edit_story', story_id=story['id'])
            else:
                messages.error(request, 'Failed to create story')
        except:
            messages.error(request, 'Cannot connect to Flask API')
    
    return render(request, 'gameplay/create_story.html')


def edit_story(request, story_id):
    """Edit story with publish option"""
    try:
        # Get story
        response = requests.get(f'{FLASK_API}/stories/{story_id}', timeout=5)
        story = response.json() if response.status_code == 200 else None
        
        # Get pages
        response = requests.get(f'{FLASK_API}/stories/{story_id}/pages', timeout=5)
        pages = response.json() if response.status_code == 200 else []
        
        # Handle publish/unpublish
        if request.method == 'POST' and 'publish' in request.POST:
            new_status = 'published' if story['status'] == 'draft' else 'draft'
            response = requests.put(
                f'{FLASK_API}/stories/{story_id}',
                json={'status': new_status},
                headers={'X-API-KEY': settings.FLASK_API_KEY},
                timeout=5
            )
            if response.status_code == 200:
                messages.success(request, f'✅ Story {new_status}!')
                return redirect('edit_story', story_id=story_id)
        
        return render(request, 'gameplay/edit_story.html', {
            'story': story,
            'pages': pages
        })
    except:
        messages.error(request, 'Cannot load story')
        return redirect('story_list')


def create_page(request, story_id):
    """Add page with ending label support"""
    if request.method == 'POST':
        data = {
            'text': request.POST.get('text'),
            'is_ending': request.POST.get('is_ending') == 'on',
            'ending_label': request.POST.get('ending_label', '')  # Level 13
        }
        try:
            response = requests.post(
                f'{FLASK_API}/stories/{story_id}/pages',
                json=data,
                headers={'X-API-KEY': settings.FLASK_API_KEY},
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
                headers={'X-API-KEY': settings.FLASK_API_KEY},
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
    

# ========== AUTHENTICATION VIEWS (Level 16) ==========

def register(request):
    """User registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'reader')
        
        # Validation
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'gameplay/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'gameplay/register.html')
        
        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Set role (using groups or is_staff)
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'author':
            user.is_staff = False
        
        user.save()
        
        messages.success(request, f'✅ Account created! You can now login.')
        return redirect('login')
    
    return render(request, 'gameplay/register.html')


def login_view(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('story_list')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'gameplay/login.html')


def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('story_list')