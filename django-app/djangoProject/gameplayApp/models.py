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
    