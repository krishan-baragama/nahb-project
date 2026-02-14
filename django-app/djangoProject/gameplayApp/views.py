"""
Level 13 Views - Enhanced UX with search, auto-save, draft support
"""
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .models import Play, PlaySession, Rating, Report
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
    """Display single story details with ratings"""
    try:
        response = requests.get(f'{FLASK_API}/stories/{story_id}', timeout=5)
        story = response.json() if response.status_code == 200 else None
    except:
        story = None
        messages.error(request, 'Cannot load story')
    
    # Get ratings for this story
    ratings = Rating.objects.filter(story_id=story_id)
    
    # Calculate average rating
    if ratings.exists():
        avg_rating = sum(r.rating for r in ratings) / ratings.count()
        avg_rating = round(avg_rating, 1)
    else:
        avg_rating = None
    
    # Get current user's rating
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(story_id=story_id, user=request.user)
        except Rating.DoesNotExist:
            pass
    
    return render(request, 'gameplay/story_detail.html', {
        'story': story,
        'ratings': ratings,
        'avg_rating': avg_rating,
        'rating_count': ratings.count(),
        'user_rating': user_rating
    })


# ========== PLAYING VIEWS WITH AUTO-SAVE ==========

def play_story(request, story_id):
    """Start or resume playing a story"""
    session_key = request.session.session_key or request.session.create()
    
    # Check if user wants to force restart
    force_restart = request.GET.get('restart', False)
    
    # Check for existing session (resume) - unless forcing restart
    if not force_restart:
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
    
    # Start from beginning (or restart)
    # Delete any existing session for this story first
    PlaySession.objects.filter(
        session_key=session_key,
        story_id=story_id
    ).delete()
    
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
    # Ensure we have a session key
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    
    try:
        # Fetch the page from Flask API
        response = requests.get(f'{FLASK_API}/pages/{page_id}', timeout=5)
        
        if response.status_code == 404:
            messages.error(request, 'Page not found')
            return redirect('story_list')
        elif response.status_code != 200:
            messages.error(request, f'Failed to load page (Error {response.status_code})')
            return redirect('story_list')
        
        page_data = response.json()
        
        if not page_data or 'story_id' not in page_data:
            messages.error(request, 'Invalid page data received')
            return redirect('story_list')
        
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
            'story_id': page_data['story_id'],
            'page': page_data
        })
        
    except requests.exceptions.ConnectionError:
        messages.error(request, 'Cannot connect to Flask API - is it running on port 5000?')
        return redirect('story_list')
    except requests.exceptions.Timeout:
        messages.error(request, 'Flask API timeout')
        return redirect('story_list')
    except requests.exceptions.RequestException as e:
        messages.error(request, f'API request error: {str(e)}')
        return redirect('story_list')
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"ERROR in get_page: {traceback.format_exc()}")
        messages.error(request, f'Error loading page: {str(e)}')
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

# ========== RATING & COMMENT VIEWS (Level 18) ==========

@login_required
def rate_story(request, story_id):
    """Add or update rating for a story"""
    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        if not rating_value or int(rating_value) not in range(1, 6):
            messages.error(request, 'Please select a rating from 1 to 5 stars')
            return redirect('story_detail', story_id=story_id)
        
        # Update or create rating
        rating, created = Rating.objects.update_or_create(
            story_id=story_id,
            user=request.user,
            defaults={
                'rating': int(rating_value),
                'comment': comment
            }
        )
        
        if created:
            messages.success(request, '✅ Rating submitted!')
        else:
            messages.success(request, '✅ Rating updated!')
        
        return redirect('story_detail', story_id=story_id)
    
    return redirect('story_detail', story_id=story_id)


@login_required
def report_story(request, story_id):
    """Report a story"""
    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        if not reason:
            messages.error(request, 'Please provide a reason for reporting')
            return redirect('story_detail', story_id=story_id)
        
        # Check if user already reported this story
        if Report.objects.filter(story_id=story_id, user=request.user).exists():
            messages.warning(request, 'You have already reported this story')
            return redirect('story_detail', story_id=story_id)
        
        Report.objects.create(
            story_id=story_id,
            user=request.user,
            reason=reason
        )
        
        messages.success(request, '✅ Report submitted. Admins will review it.')
        return redirect('story_detail', story_id=story_id)
    
    return redirect('story_detail', story_id=story_id)


@login_required
def admin_reports(request):
    """Admin view for managing reports"""
    if not request.user.is_staff:
        messages.error(request, 'Admin access required')
        return redirect('story_list')
    
    # Handle status updates
    if request.method == 'POST':
        report_id = request.POST.get('report_id')
        new_status = request.POST.get('status')
        
        if report_id and new_status:
            try:
                report = Report.objects.get(id=report_id)
                report.status = new_status
                report.save()
                messages.success(request, f'Report #{report_id} updated to {new_status}')
            except Report.DoesNotExist:
                messages.error(request, 'Report not found')
    
    # Get all reports
    reports = Report.objects.all()
    
    # Get story details for each report
    story_details = {}
    for report in reports:
        try:
            response = requests.get(f'{FLASK_API}/stories/{report.story_id}', timeout=5)
            if response.status_code == 200:
                story_details[report.story_id] = response.json()
        except:
            pass
    
    return render(request, 'gameplay/admin_reports.html', {
        'reports': reports,
        'story_details': story_details
    })


@login_required
def admin_suspend_story(request, story_id):
    """Admin: Suspend a story"""
    if not request.user.is_staff:
        messages.error(request, 'Admin access required')
        return redirect('story_list')
    
    try:
        response = requests.put(
            f'{FLASK_API}/stories/{story_id}',
            json={'status': 'suspended'},
            headers={'X-API-KEY': settings.FLASK_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            messages.success(request, '✅ Story suspended')
        else:
            messages.error(request, 'Failed to suspend story')
    except:
        messages.error(request, 'Cannot connect to Flask API')
    
    return redirect('admin_reports')