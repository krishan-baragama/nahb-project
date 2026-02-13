"""
Level 10 Routes - All endpoints for story management
"""
from flask import request, jsonify
from app import db
from app.models import Story, Page, Choice


def init_routes(app):
    
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'message': 'NAHB API - Level 10',
            'version': '1.0'
        })

    # ========== READING ENDPOINTS ==========
    
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

    # ========== WRITING ENDPOINTS ==========

    @app.route('/stories', methods=['POST'])
    def create_story():
        data = request.json
        if not data.get('title'):
            return jsonify({'error': 'Title required'}), 400
        
        story = Story(
            title=data.get('title'),
            description=data.get('description', ''),
            status=data.get('status', 'draft')
        )
        db.session.add(story)
        db.session.commit()
        return jsonify(story.to_dict()), 201

    @app.route('/stories/<int:story_id>', methods=['PUT'])
    def update_story(story_id):
        story = Story.query.get_or_404(story_id)
        data = request.json
        
        if 'title' in data:
            story.title = data['title']
        if 'description' in data:
            story.description = data['description']
        if 'start_page_id' in data:
            story.start_page_id = data['start_page_id']
        
        db.session.commit()
        return jsonify(story.to_dict())

    @app.route('/stories/<int:story_id>', methods=['DELETE'])
    def delete_story(story_id):
        story = Story.query.get_or_404(story_id)
        Page.query.filter_by(story_id=story_id).delete()
        db.session.delete(story)
        db.session.commit()
        return jsonify({'message': 'Deleted'}), 200

    @app.route('/stories/<int:story_id>/pages', methods=['POST'])
    def create_page(story_id):
        story = Story.query.get_or_404(story_id)
        data = request.json
        
        if not data.get('text'):
            return jsonify({'error': 'Text required'}), 400
        
        page = Page(
            story_id=story_id,
            text=data.get('text'),
            is_ending=data.get('is_ending', False),
            ending_label=data.get('ending_label')
        )
        db.session.add(page)
        db.session.commit()
        
        if not story.start_page_id:
            story.start_page_id = page.id
            db.session.commit()
        
        return jsonify(page.to_dict()), 201

    @app.route('/pages/<int:page_id>/choices', methods=['POST'])
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