"""
Level 20: Unit Tests for NAHB Project
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Play, PlaySession, Rating, Report


class AuthenticationTests(TestCase):
    """Test user authentication (Level 16)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123'
        )
    
    def test_register_user(self):
        """Test user registration"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'new123',
            'password2': 'new123',
            'role': 'reader'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_login_user(self):
        """Test user login"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'test123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_logout_user(self):
        """Test user logout"""
        self.client.login(username='testuser', password='test123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)


class PlayModelTests(TestCase):
    """Test Play model (Level 10)"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
    
    def test_create_play(self):
        """Test creating a play record"""
        play = Play.objects.create(
            story_id=1,
            ending_page_id=5,
            user=self.user
        )
        self.assertEqual(play.story_id, 1)
        self.assertEqual(play.ending_page_id, 5)
        self.assertEqual(play.user, self.user)
    
    def test_anonymous_play(self):
        """Test anonymous play (no user)"""
        play = Play.objects.create(
            story_id=1,
            ending_page_id=5,
            user=None
        )
        self.assertIsNone(play.user)


class RatingModelTests(TestCase):
    """Test Rating model (Level 18)"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
    
    def test_create_rating(self):
        """Test creating a rating"""
        rating = Rating.objects.create(
            story_id=1,
            user=self.user,
            rating=5,
            comment='Great story!'
        )
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.comment, 'Great story!')
    
    def test_unique_rating_per_user(self):
        """Test one rating per user per story"""
        Rating.objects.create(story_id=1, user=self.user, rating=5)
        
        # Try to create duplicate (should fail)
        with self.assertRaises(Exception):
            Rating.objects.create(story_id=1, user=self.user, rating=4)


class ReportModelTests(TestCase):
    """Test Report model (Level 18)"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
    
    def test_create_report(self):
        """Test creating a report"""
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
            reason='Test'
        )
        report.status = 'reviewed'
        report.save()
        self.assertEqual(report.status, 'reviewed')


class ViewTests(TestCase):
    """Test views"""
    
    def setUp(self):
        self.client = Client()
    
    def test_story_list_view(self):
        """Test story list page loads"""
        response = self.client.get(reverse('story_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gameplay/story_list.html')
    
    def test_statistics_view(self):
        """Test statistics page loads"""
        response = self.client.get(reverse('statistics'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gameplay/statistics.html')
    
    def test_login_required_for_create(self):
        """Test login required for story creation"""
        response = self.client.get(reverse('create_story'))
        self.assertEqual(response.status_code, 302)  # Redirect to login