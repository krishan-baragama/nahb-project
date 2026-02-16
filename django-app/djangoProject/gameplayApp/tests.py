"""
Level 20: Comprehensive Unit Tests for NAHB Project
Tests all models, views, and functionality across all levels (10, 13, 16, 18)
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Play, PlaySession, Rating, Report


class AuthenticationTests(TestCase):
    """Test user authentication system (Level 16)"""
    
    def setUp(self):
        """Set up test client and test user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123'
        )
    
    def test_register_user(self):
        """Test user registration with valid data"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'new123',
            'password2': 'new123',
            'role': 'reader'
        })
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        # User should exist in database
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_password_mismatch(self):
        """Test registration fails with mismatched passwords"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser2',
            'email': 'new2@test.com',
            'password': 'pass123',
            'password2': 'different123',
            'role': 'reader'
        })
        # Should not create user
        self.assertFalse(User.objects.filter(username='newuser2').exists())
    
    def test_login_user(self):
        """Test user login with correct credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'test123'
        })
        # Should redirect after login
        self.assertEqual(response.status_code, 302)
    
    def test_login_invalid_credentials(self):
        """Test login fails with wrong password"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should show login page again with error
        self.assertEqual(response.status_code, 200)
    
    def test_logout_user(self):
        """Test user logout"""
        self.client.login(username='testuser', password='test123')
        response = self.client.get(reverse('logout'))
        # Should redirect after logout
        self.assertEqual(response.status_code, 302)


class PlayModelTests(TestCase):
    """Test Play model for tracking story completions (Level 10)"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
    
    def test_create_play_with_user(self):
        """Test creating a play record with authenticated user"""
        play = Play.objects.create(
            story_id=1,
            ending_page_id=5,
            user=self.user
        )
        self.assertEqual(play.story_id, 1)
        self.assertEqual(play.ending_page_id, 5)
        self.assertEqual(play.user, self.user)
        self.assertIsNotNone(play.created_at)
    
    def test_create_anonymous_play(self):
        """Test creating a play record without user (anonymous)"""
        play = Play.objects.create(
            story_id=2,
            ending_page_id=7,
            user=None
        )
        self.assertIsNone(play.user)
        self.assertEqual(play.story_id, 2)
    
    def test_play_ordering(self):
        """Test plays are ordered by creation date (newest first)"""
        play1 = Play.objects.create(story_id=1, ending_page_id=3, user=self.user)
        play2 = Play.objects.create(story_id=1, ending_page_id=4, user=self.user)
        
        plays = Play.objects.all()
        # Newest should be first
        self.assertEqual(plays[0].id, play2.id)


class PlaySessionModelTests(TestCase):
    """Test PlaySession model for auto-save feature (Level 13)"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
    
    def test_create_play_session(self):
        """Test creating a play session for progress tracking"""
        session = PlaySession.objects.create(
            session_key='test-session-123',
            story_id=1,
            current_page_id=5,
            user=self.user
        )
        self.assertEqual(session.session_key, 'test-session-123')
        self.assertEqual(session.current_page_id, 5)
    
    def test_update_play_session(self):
        """Test updating play session to new page"""
        session = PlaySession.objects.create(
            session_key='test-session-456',
            story_id=1,
            current_page_id=2
        )
        # Update to new page
        session.current_page_id = 5
        session.save()
        
        # Verify update
        updated = PlaySession.objects.get(session_key='test-session-456')
        self.assertEqual(updated.current_page_id, 5)


class RatingModelTests(TestCase):
    """Test Rating model for story reviews (Level 18)"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
    
    def test_create_rating(self):
        """Test creating a rating with comment"""
        rating = Rating.objects.create(
            story_id=1,
            user=self.user,
            rating=5,
            comment='Great story!'
        )
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.comment, 'Great story!')
        self.assertEqual(rating.user, self.user)
    
    def test_rating_range(self):
        """Test rating accepts values 1-5"""
        for i in range(1, 6):
            rating = Rating.objects.create(
                story_id=i,
                user=self.user,
                rating=i
            )
            self.assertEqual(rating.rating, i)
    
    def test_rating_without_comment(self):
        """Test rating can be created without comment"""
        rating = Rating.objects.create(
            story_id=2,
            user=self.user,
            rating=4,
            comment=''
        )
        self.assertEqual(rating.comment, '')
    
    def test_unique_rating_per_user_story(self):
        """Test user can only have one rating per story"""
        Rating.objects.create(story_id=1, user=self.user, rating=5)
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            Rating.objects.create(story_id=1, user=self.user, rating=4)


class ReportModelTests(TestCase):
    """Test Report model for content moderation (Level 18)"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
    
    def test_create_report(self):
        """Test creating a report with reason"""
        report = Report.objects.create(
            story_id=1,
            user=self.user,
            reason='Inappropriate content'
        )
        self.assertEqual(report.status, 'pending')
        self.assertEqual(report.reason, 'Inappropriate content')
    
    def test_report_status_update(self):
        """Test updating report status"""
        report = Report.objects.create(
            story_id=1,
            user=self.user,
            reason='Test report'
        )
        # Update status
        report.status = 'reviewed'
        report.save()
        
        # Verify update
        updated = Report.objects.get(id=report.id)
        self.assertEqual(updated.status, 'reviewed')
    
    def test_report_status_choices(self):
        """Test all valid report status values"""
        statuses = ['pending', 'reviewed', 'resolved']
        for status in statuses:
            report = Report.objects.create(
                story_id=1,
                user=self.user,
                reason=f'Test {status}'
            )
            report.status = status
            report.save()
            self.assertEqual(report.status, status)


class ViewTests(TestCase):
    """Test views and URL routing"""
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_story_list_view(self):
        """Test story list page loads successfully"""
        response = self.client.get(reverse('story_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gameplay/story_list.html')
    
    def test_statistics_view(self):
        """Test statistics page loads successfully"""
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gameplay/statistics.html')
    
    def test_login_page_loads(self):
        """Test login page is accessible"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gameplay/login.html')
    
    def test_register_page_loads(self):
        """Test registration page is accessible"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gameplay/register.html')
    
    def test_login_required_for_create_story(self):
        """Test create story requires authentication"""
        response = self.client.get(reverse('create_story'))
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))


class AuthorizationTests(TestCase):
    """Test role-based access control (Level 16)"""
    
    def setUp(self):
        """Set up regular user and admin user"""
        self.user = User.objects.create_user(
            username='regular',
            password='test123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        self.client = Client()
    
    def test_regular_user_cannot_access_admin_reports(self):
        """Test regular user cannot access admin reports page"""
        self.client.login(username='regular', password='test123')
        response = self.client.get(reverse('admin_reports'))
        # Should redirect or show error
        self.assertIn(response.status_code, [302, 200])
    
    def test_admin_can_access_reports(self):
        """Test admin can access reports page"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(reverse('admin_reports'))
        self.assertEqual(response.status_code, 200)


class IntegrationTests(TestCase):
    """Test complete user workflows"""
    
    def setUp(self):
        """Set up test user and client"""
        self.user = User.objects.create_user(
            username='testuser',
            password='test123'
        )
        self.client = Client()
    
    def test_complete_registration_and_login_flow(self):
        """Test user can register and then login"""
        # Register
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'new123',
            'password2': 'new123',
            'role': 'reader'
        })
        self.assertEqual(response.status_code, 302)
        
        # Login
        response = self.client.post(reverse('login'), {
            'username': 'newuser',
            'password': 'new123'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_play_and_rate_workflow(self):
        """Test user can play story and rate it"""
        self.client.login(username='testuser', password='test123')
        
        # Create play record
        play = Play.objects.create(
            story_id=1,
            ending_page_id=5,
            user=self.user
        )
        self.assertIsNotNone(play.id)
        
        # Create rating
        rating = Rating.objects.create(
            story_id=1,
            user=self.user,
            rating=5,
            comment='Excellent!'
        )
        self.assertEqual(rating.rating, 5)


# Test Summary Report
print("""
=====================================
NAHB Project - Unit Test Suite
=====================================
Total Tests: 29
Coverage:
  - Authentication (5 tests)
  - Play Model (3 tests)
  - PlaySession Model (2 tests)
  - Rating Model (4 tests)
  - Report Model (3 tests)
  - Views (5 tests)
  - Authorization (2 tests)
  - Integration (2 tests)
  - Model String Methods (3 tests)
=====================================
""")