from django import template
from gameplayApp.models import Rating

register = template.Library()

@register.filter
def get_avg_rating(story_id):
    """Get average rating for a story"""
    ratings = Rating.objects.filter(story_id=story_id)
    if ratings.exists():
        avg = sum(r.rating for r in ratings) / ratings.count()
        return round(avg, 1)
    return None

@register.filter
def get_rating_count(story_id):
    """Get total rating count for a story"""
    return Rating.objects.filter(story_id=story_id).count()