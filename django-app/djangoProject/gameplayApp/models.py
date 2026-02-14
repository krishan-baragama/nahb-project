"""
Level 16 Models - Play tracking with user authentication
"""
from django.db import models
from django.contrib.auth.models import User

class Play(models.Model):
    """
    Track completed game plays
    Level 10: Anonymous only (no user link)
    Level 16: Link plays to authenticated users
    """
    story_id = models.IntegerField()
    ending_page_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Level 16
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Play {self.id} - Story {self.story_id} - Ending {self.ending_page_id}"

class PlaySession(models.Model):
    """
    Level 13: Track in-progress sessions for auto-save
    Allows users to resume where they left off
    """
    session_key = models.CharField(max_length=40, unique=True)
    story_id = models.IntegerField()
    current_page_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session {self.session_key} - Story {self.story_id} at Page {self.current_page_id}"
    

class Rating(models.Model):
    """Story ratings (Level 18)"""
    story_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['story_id', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rating}⭐ for Story {self.story_id} by {self.user.username}"


class Report(models.Model):
    """Story reports (Level 18)"""
    story_id = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('reviewed', 'Reviewed'),
            ('resolved', 'Resolved')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report for Story {self.story_id} - {self.status}"
