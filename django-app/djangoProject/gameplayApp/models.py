"""
Level 10 Models - Play tracking only
"""
from django.db import models

class Play(models.Model):
    """
    Track completed game plays
    Level 10: Anonymous only (no user link)
    """
    story_id = models.IntegerField()
    ending_page_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
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
