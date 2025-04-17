from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models.travel_plan import TravelPlan, ItineraryItem, PlanShare
from datetime import datetime
import uuid

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

@planner_bp.route('/')
@login_required
def index():
    """Travel planner main page listing user's travel plans"""
    plans = TravelPlan.query.filter_by(user_id=current_user.id).order_by(TravelPlan.start_date).all()
    return render_template('planner/index.html', plans=plans)

@planner_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_plan():
    """Create a new travel plan"""
    # Pre-fill destination from request args (for recommendations integration)
    destination = request.args.get('destination', '')
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        destination = request.form.get('destination')
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        budget = float(request.form.get('budget') or 0)
        interests = request.form.get('interests')
        is_public = 'is_public' in request.form
        
        # Create new travel plan
        plan = TravelPlan(
            title=title,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            interests=interests,
            is_public=is_public,
            user_id=current_user.id
        )
        
        db.session.add(plan)
        db.session.commit()
        
        flash('Travel plan created successfully!', 'success')
        return redirect(url_for('planner.view_plan', plan_id=plan.id))
        
    return render_template('planner/create.html', destination=destination)

@planner_bp.route('/<int:plan_id>')
@login_required
def view_plan(plan_id):
    """View a specific travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user owns this plan or it's shared with them
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email
        ).first()
        
        if not shared and not plan.is_public:
            flash('You do not have access to this travel plan', 'danger')
            return redirect(url_for('planner.index'))
    
    # Calculate total cost from all itinerary items
    total_cost = 0
    
    # Prepare itinerary items for JSON serialization
    itinerary_items_json = []
    for item in plan.itinerary_items:
        if item.cost:
            total_cost += item.cost
        
        # Create a serializable dictionary for each item
        itinerary_items_json.append({
            'id': item.id,
            'day': item.day,
            'time': item.time,
            'activity': item.activity,
            'location': item.location,
            'lat': item.lat,
            'lng': item.lng,
            'cost': float(item.cost) if item.cost else 0,
            'notes': item.notes
        })
            
    return render_template('planner/view.html', plan=plan, total_cost=total_cost, itinerary_items_json=itinerary_items_json)

@planner_bp.route('/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    """Edit an existing travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user owns this plan or has edit permission
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email,
            can_edit=True
        ).first()
        
        if not shared:
            flash('You do not have permission to edit this travel plan', 'danger')
            return redirect(url_for('planner.view_plan', plan_id=plan_id))
    
    if request.method == 'POST':
        # Update plan details
        plan.title = request.form.get('title')
        plan.destination = request.form.get('destination')
        plan.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        plan.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        plan.budget = float(request.form.get('budget') or 0)
        plan.interests = request.form.get('interests')
        plan.is_public = 'is_public' in request.form
        
        db.session.commit()
        
        flash('Travel plan updated successfully!', 'success')
        return redirect(url_for('planner.view_plan', plan_id=plan.id))
        
    return render_template('planner/edit.html', plan=plan)

@planner_bp.route('/<int:plan_id>/itinerary', methods=['GET', 'POST'])
@login_required
def manage_itinerary(plan_id):
    """Manage itinerary items for a travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user owns this plan or has edit permission
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email,
            can_edit=True
        ).first()
        
        if not shared:
            flash('You do not have permission to edit this itinerary', 'danger')
            return redirect(url_for('planner.view_plan', plan_id=plan_id))
    
    if request.method == 'POST':
        # Add new itinerary item
        day = int(request.form.get('day'))
        time = request.form.get('time')
        activity = request.form.get('activity')
        location = request.form.get('location')
        
        # Convert empty strings to None for float fields
        lat = request.form.get('lat')
        lat = float(lat) if lat.strip() else None
        
        lng = request.form.get('lng') 
        lng = float(lng) if lng.strip() else None
        
        cost = float(request.form.get('cost') or 0)
        notes = request.form.get('notes')
        
        item = ItineraryItem(
            day=day,
            time=time,
            activity=activity,
            location=location,
            lat=lat,
            lng=lng,
            cost=cost,
            notes=notes,
            travel_plan_id=plan_id
        )
        
        db.session.add(item)
        db.session.commit()
        
        flash('Itinerary item added successfully!', 'success')
        
    # Get all itinerary items for this plan
    items = ItineraryItem.query.filter_by(travel_plan_id=plan_id).order_by(ItineraryItem.day, ItineraryItem.time).all()
    
    return render_template('planner/itinerary.html', plan=plan, items=items)

@planner_bp.route('/<int:plan_id>/share', methods=['GET', 'POST'])
@login_required
def share_plan(plan_id):
    """Share a travel plan with others"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Only the owner can share the plan
    if plan.user_id != current_user.id:
        flash('You do not have permission to share this plan', 'danger')
        return redirect(url_for('planner.view_plan', plan_id=plan_id))
        
    if request.method == 'POST':
        email = request.form.get('email')
        can_edit = 'can_edit' in request.form
        
        # Check if already shared with this email
        existing = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=email
        ).first()
        
        if existing:
            existing.can_edit = can_edit
            flash(f'Updated sharing permissions for {email}', 'info')
        else:
            # Create new share
            share = PlanShare(
                travel_plan_id=plan_id,
                shared_email=email,
                can_edit=can_edit
            )
            db.session.add(share)
            flash(f'Plan shared with {email}!', 'success')
            
        db.session.commit()
        
    # Get all current shares
    shares = PlanShare.query.filter_by(travel_plan_id=plan_id).all()
    
    return render_template('planner/share.html', plan=plan, shares=shares)

@planner_bp.route('/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """Delete a travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Only the owner can delete the plan
    if plan.user_id != current_user.id:
        flash('You do not have permission to delete this plan', 'danger')
        return redirect(url_for('planner.index'))
        
    db.session.delete(plan)
    db.session.commit()
    
    flash('Travel plan deleted successfully', 'success')
    return redirect(url_for('planner.index'))

@planner_bp.route('/<int:plan_id>/toggle-public', methods=['POST'])
@login_required
def toggle_public(plan_id):
    """Toggle the public status of a travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Only the owner can change public status
    if plan.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    # Get the requested status from the JSON data
    data = request.get_json()
    is_public = data.get('is_public', False)
    
    plan.is_public = is_public
    
    # Generate a share code if making public and no code exists
    if is_public and not plan.share_code:
        plan.share_code = str(uuid.uuid4())
    
    db.session.commit()
    
    return jsonify({'success': True})

@planner_bp.route('/shared/<string:share_code>')
def view_shared_plan(share_code):
    """View a shared travel plan using a share code"""
    # Find the plan with this share code
    plan = TravelPlan.query.filter_by(share_code=share_code).first_or_404()
    
    # Check if the plan is public or the current user has access
    if not plan.is_public and (not current_user.is_authenticated or 
                              (plan.user_id != current_user.id and 
                               not PlanShare.query.filter_by(
                                   travel_plan_id=plan.id,
                                   shared_email=current_user.email
                               ).first())):
        abort(404)  # Not found or no permission
    
    # Calculate total cost from all itinerary items
    total_cost = 0
    
    # Prepare itinerary items for JSON serialization
    itinerary_items_json = []
    for item in plan.itinerary_items:
        if item.cost:
            total_cost += item.cost
        
        # Create a serializable dictionary for each item
        itinerary_items_json.append({
            'id': item.id,
            'day': item.day,
            'time': item.time,
            'activity': item.activity,
            'location': item.location,
            'lat': item.lat,
            'lng': item.lng,
            'cost': float(item.cost) if item.cost else 0,
            'notes': item.notes
        })
    
    # Pass a flag to indicate this is a shared view (for UI customization)
    return render_template('planner/view.html', plan=plan, total_cost=total_cost, 
                          itinerary_items_json=itinerary_items_json, is_shared_view=True)
