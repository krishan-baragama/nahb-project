"""
Flask Routes - All levels (10, 13, 16)
"""
from flask import request, jsonify, current_app
from functools import wraps
from app import db
from app.models import Story, Page, Choice


def require_api_key(f):
    """Decorator for protected endpoints (Level 16)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if api_key != current_app.config['API_KEY']:
            return jsonify({'error': 'Unauthorized - Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated


def init_routes(app):
    
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'message': 'NAHB API - Levels 10-16',
            'version': '1.0'
        })

    # ========== PUBLIC READING ENDPOINTS ==========
    
    @app.route('/stories', methods=['GET'])
    def get_stories():
        status = request.args.get('status', 'published')
        stories = Story.query.filter_by(status=status).all()
        return jsonify([s.to_dict() for s in stories])

    @app.route('/stories/<int:story_id>', methods=['GET'])
    def get_story(story_id):
        story = Story.query.get_or_404(story_id)
        return jsonify(story.to_dict())

    @app.route('/stories/<int:story_id>/start', methods=['GET'])
    def get_story_start(story_id):
        story = Story.query.get_or_404(story_id)
        if not story.start_page_id:
            return jsonify({'error': 'No starting page'}), 404
        start_page = Page.query.get(story.start_page_id)
        return jsonify(start_page.to_dict())

    @app.route('/stories/<int:story_id>/pages', methods=['GET'])
    def get_story_pages(story_id):
        Story.query.get_or_404(story_id)
        pages = Page.query.filter_by(story_id=story_id).all()
        return jsonify([p.to_dict() for p in pages])

    @app.route('/pages/<int:page_id>', methods=['GET'])
    def get_page(page_id):
        page = Page.query.get_or_404(page_id)
        return jsonify(page.to_dict())

    # ========== PROTECTED WRITING ENDPOINTS (Level 16) ==========

    @app.route('/stories', methods=['POST'])
    @require_api_key
    def create_story():
        data = request.json
        if not data.get('title'):
            return jsonify({'error': 'Title required'}), 400
        
        if not data.get('author_id'):
            return jsonify({'error': 'Author ID required'}), 400
        
        story = Story(
            title=data.get('title'),
            description=data.get('description', ''),
            status=data.get('status', 'draft'),
            author_id=data.get('author_id')  # Level 16
        )
        db.session.add(story)
        db.session.commit()
        return jsonify(story.to_dict()), 201

    @app.route('/stories/<int:story_id>', methods=['PUT'])
    @require_api_key
    def update_story(story_id):
        story = Story.query.get_or_404(story_id)
        data = request.json
        
        if 'title' in data:
            story.title = data['title']
        if 'description' in data:
            story.description = data['description']
        if 'status' in data:
            story.status = data['status']
        if 'start_page_id' in data:
            story.start_page_id = data['start_page_id']
        
        db.session.commit()
        return jsonify(story.to_dict())

    @app.route('/stories/<int:story_id>', methods=['DELETE'])
    @require_api_key
    def delete_story(story_id):
        story = Story.query.get_or_404(story_id)
        Page.query.filter_by(story_id=story_id).delete()
        db.session.delete(story)
        db.session.commit()
        return jsonify({'message': 'Deleted'}), 200

    @app.route('/stories/<int:story_id>/pages', methods=['POST'])
    @require_api_key
    def create_page(story_id):
        story = Story.query.get_or_404(story_id)
        data = request.json
        
        if not data.get('text'):
            return jsonify({'error': 'Text required'}), 400
        
        page = Page(
            story_id=story_id,
            text=data.get('text'),
            is_ending=data.get('is_ending', False),
            ending_label=data.get('ending_label')  # Level 13
        )
        db.session.add(page)
        db.session.commit()
        
        if not story.start_page_id:
            story.start_page_id = page.id
            db.session.commit()
        
        return jsonify(page.to_dict()), 201

    @app.route('/pages/<int:page_id>/choices', methods=['POST'])
    @require_api_key
    def create_choice(page_id):
        page = Page.query.get_or_404(page_id)
        data = request.json
        
        if not data.get('text') or not data.get('next_page_id'):
            return jsonify({'error': 'Text and next_page_id required'}), 400
        
        next_page = Page.query.get_or_404(data['next_page_id'])
        if next_page.story_id != page.story_id:
            return jsonify({'error': 'Pages must be in same story'}), 400
        
        if page.is_ending:
            return jsonify({'error': 'Cannot add choices to ending'}), 400
        
        choice = Choice(
            page_id=page_id,
            text=data.get('text'),
            next_page_id=data.get('next_page_id')
        )
        db.session.add(choice)
        db.session.commit()
        return jsonify(choice.to_dict()), 201

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500