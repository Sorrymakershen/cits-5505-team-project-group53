from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
import os
from datetime import datetime
from app.models.memory import Memory, Photo, MemoryTag

memories_bp = Blueprint('memories', __name__, url_prefix='/memories')

@memories_bp.route('/')
@login_required
def index():
    """Memories main page showing user's travel memories"""
    from datetime import datetime, timedelta
    
    memories = Memory.query.filter_by(user_id=current_user.id).order_by(Memory.visit_date.desc()).all()
    
    # Add current time for marking recent memories
    now = datetime.now()
    
    return render_template('memories/index.html', 
                          memories=memories, 
                          now=now,
                          timedelta=timedelta)

@memories_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_memory():
    """Create a new travel memory"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        location = request.form.get('location')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        visit_date_str = request.form.get('visit_date')
        visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d') if visit_date_str else None
        description = request.form.get('description')
        emotional_rating = int(request.form.get('emotional_rating', 3))
        is_public = 'is_public' in request.form
        tags = request.form.get('tags', '').split(',')
          # Convert empty string values to None for float fields
        lat = float(lat) if lat.strip() else None
        lng = float(lng) if lng.strip() else None
        
        # Create new memory
        memory = Memory(
            title=title,
            location=location,
            lat=lat,
            lng=lng,
            visit_date=visit_date,
            description=description,
            emotional_rating=emotional_rating,
            is_public=is_public,
            user_id=current_user.id
        )
        
        db.session.add(memory)
        db.session.flush()  # Get the memory ID for relationships
        
        # Add tags
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                tag = MemoryTag(name=tag_name, memory_id=memory.id)
                db.session.add(tag)
        
        # Handle photo uploads
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo_file in photos:
                if photo_file and photo_file.filename:
                    filename = secure_filename(photo_file.filename)
                    # Ensure unique filename
                    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    
                    # Save file to uploads directory
                    upload_folder = os.path.join(current_app.static_folder, 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    photo_file.save(os.path.join(upload_folder, unique_filename))
                    
                    # Create photo record
                    photo = Photo(
                        filename=unique_filename,
                        caption=request.form.get('caption', ''),
                        memory_id=memory.id
                    )
                    db.session.add(photo)
        
        db.session.commit()
        flash('Memory created successfully!', 'success')
        return redirect(url_for('memories.view_memory', memory_id=memory.id))
        
    return render_template('memories/create.html')

@memories_bp.route('/<int:memory_id>')
@login_required
def view_memory(memory_id):
    """View a specific memory"""
    memory = Memory.query.get_or_404(memory_id)
    
    # Check if user owns this memory or it's public
    if memory.user_id != current_user.id and not memory.is_public:
        flash('You do not have access to view this memory', 'danger')
        return redirect(url_for('memories.index'))
        
    return render_template('memories/view.html', memory=memory)

@memories_bp.route('/<int:memory_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_memory(memory_id):
    """Edit an existing memory"""
    memory = Memory.query.get_or_404(memory_id)
    
    # Only the owner can edit the memory
    if memory.user_id != current_user.id:
        flash('You do not have permission to edit this memory', 'danger')
        return redirect(url_for('memories.index'))
    
    if request.method == 'POST':
        # Update memory details
        memory.title = request.form.get('title')
        memory.location = request.form.get('location')
        memory.lat = request.form.get('lat')
        memory.lng = request.form.get('lng')
        
        visit_date_str = request.form.get('visit_date')
        memory.visit_date = datetime.strptime(visit_date_str, '%Y-%m-%d') if visit_date_str else None
        
        memory.description = request.form.get('description')
        memory.emotional_rating = int(request.form.get('emotional_rating', 3))
        memory.is_public = 'is_public' in request.form
        
        # Update tags
        # First remove existing tags
        MemoryTag.query.filter_by(memory_id=memory.id).delete()
        
        # Then add new tags
        tags = request.form.get('tags', '').split(',')
        for tag_name in tags:
            tag_name = tag_name.strip()
            if tag_name:
                tag = MemoryTag(name=tag_name, memory_id=memory.id)
                db.session.add(tag)
        
        # Handle photo uploads
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo_file in photos:
                if photo_file and photo_file.filename:
                    filename = secure_filename(photo_file.filename)
                    # Ensure unique filename
                    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                    
                    # Save file to uploads directory
                    upload_folder = os.path.join(current_app.static_folder, 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    photo_file.save(os.path.join(upload_folder, unique_filename))
                    
                    # Create photo record
                    photo = Photo(
                        filename=unique_filename,
                        caption=request.form.get('caption', ''),
                        memory_id=memory.id
                    )
                    db.session.add(photo)
        
        db.session.commit()
        flash('Memory updated successfully!', 'success')
        return redirect(url_for('memories.view_memory', memory_id=memory.id))
        
    # Get existing tags as comma-separated string
    tags = [tag.name for tag in memory.tags]
    tags_string = ', '.join(tags)
    
    return render_template('memories/edit.html', memory=memory, tags_string=tags_string)

@memories_bp.route('/<int:memory_id>/delete', methods=['POST'])
@login_required
def delete_memory(memory_id):
    """Delete a memory"""
    memory = Memory.query.get_or_404(memory_id)
    
    # Only the owner can delete the memory
    if memory.user_id != current_user.id:
        flash('You do not have permission to delete this memory', 'danger')
        return redirect(url_for('memories.index'))
        
    # Delete associated photos from filesystem
    for photo in memory.photos:
        try:
            os.remove(os.path.join(current_app.static_folder, 'uploads', photo.filename))
        except:
            pass  # File might not exist
            
    db.session.delete(memory)
    db.session.commit()
    
    flash('Memory deleted successfully', 'success')
    return redirect(url_for('memories.index'))

@memories_bp.route('/timeline')
@login_required
def timeline():
    """View memories in a timeline format"""
    memories = Memory.query.filter_by(user_id=current_user.id).order_by(Memory.visit_date).all()
    return render_template('memories/timeline.html', memories=memories)

@memories_bp.route('/map')
@login_required
def map_view():
    """View memories on a map"""
    from datetime import datetime, timedelta
    import json
    
    # Get all memories with location data for the current user
    memories = Memory.query.filter_by(user_id=current_user.id).all()
    
    # Prepare memories with location data for the map
    map_data = []
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    for memory in memories:
        if memory.lat is not None and memory.lng is not None:
            # Prepare tags as list of strings
            tags = [tag.name for tag in memory.tags]
            
            # Get the first photo or None
            image_path = None
            if memory.photos and len(memory.photos) > 0:
                image_path = url_for('static', filename=f'uploads/{memory.photos[0].filename}')
            
            # Format the visit date
            visit_date_formatted = memory.visit_date.strftime('%B %d, %Y') if memory.visit_date else None
            
            # Check if memory is recent (within last 30 days)
            is_recent = memory.visit_date and memory.visit_date >= thirty_days_ago
            
            # Create map data object
            map_data.append({
                'id': memory.id,
                'title': memory.title,
                'location': memory.location,
                'lat': float(memory.lat),
                'lng': float(memory.lng),
                'description': memory.description[:150] + '...' if memory.description and len(memory.description) > 150 else memory.description,
                'visit_date': visit_date_formatted,
                'image_path': image_path,
                'tags': tags,
                'isRecent': is_recent
            })
    
    # Convert to JSON for template
    memories_json = json.dumps(map_data)
    
    return render_template('memories/map.html', memories=memories, memories_json=memories_json)
