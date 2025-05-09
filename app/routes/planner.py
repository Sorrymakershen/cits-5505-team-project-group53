from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.travel_plan import TravelPlan, ItineraryItem, PlanShare
from app.models.user import User
from datetime import datetime, timedelta
import random  # For generating random recommendations
import requests  # add requests module for API calls
import json  # add json module for parsing JSON data
import hashlib  # For generating cache keys
import time  # For cache expiration management

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

# Configuration for Gemini API
GEMINI_API_KEY = "AIzaSyAwbiZHLVnwXMhVXOS8heweUSXSyU4FTYE"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Memory cache system for API responses
api_response_cache = {}
CACHE_EXPIRY = 3600  # Cache expiry time in seconds (1 hour)

def get_cache_key(endpoint, params):
    """Generate a cache key based on endpoint and parameters."""
    # Convert parameters to a sorted string to ensure consistent key generation
    param_str = json.dumps(params, sort_keys=True)
    # Generate a fixed-length key using MD5 hash
    return f"{endpoint}:{hashlib.md5(param_str.encode()).hexdigest()}"

def get_cached_response(endpoint, params):
    """Retrieve a cached API response if available and not expired."""
    cache_key = get_cache_key(endpoint, params)
    cached_item = api_response_cache.get(cache_key)
    
    if cached_item:
        timestamp, data = cached_item
        # Check if cache is still valid
        if time.time() - timestamp < CACHE_EXPIRY:
            print(f"Cache hit for: {endpoint}")
            return data
    
    print(f"Cache miss for: {endpoint}")
    return None

def set_cached_response(endpoint, params, response):
    """Cache an API response with current timestamp."""
    cache_key = get_cache_key(endpoint, params)
    api_response_cache[cache_key] = (time.time(), response)
    print(f"Cached response for: {endpoint}")

@planner_bp.route('/')
@login_required
def index():
    """Travel planner main page listing user's travel plans"""
    owned_plans = TravelPlan.query.filter_by(user_id=current_user.id).order_by(TravelPlan.start_date).all()
    
    # Get plans shared with the user and accepted
    accepted_shares = PlanShare.query.filter_by(shared_user_id=current_user.id, status='accepted').all()
    shared_plans = [share.travel_plan for share in accepted_shares]
    
    # Get pending invitations for the current user
    pending_invitations = PlanShare.query.filter_by(shared_user_id=current_user.id, status='pending').all()
    
    return render_template('planner/index.html', 
                           plans=owned_plans, 
                           shared_plans=shared_plans,
                           pending_invitations=pending_invitations)

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
        
        # Get location coordinates
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        
        # 转Change the coordinates to floating-point numbers (if provided)
        dest_lat = float(lat) if lat and lat.strip() else None
        dest_lng = float(lng) if lng and lng.strip() else None
        
        # Create new travel plan
        plan = TravelPlan(
            title=title,
            destination=destination,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
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
    can_view = False
    can_edit_shared = False # To pass to template for UI, if needed

    if plan.user_id == current_user.id:
        can_view = True
        # Owner can always edit, but for consistency with shared logic:
        # plan_share_details = PlanShare(can_edit=True) # Not a real DB object, just for logic
    else:
        share_info = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_user_id=current_user.id,
            status='accepted'
        ).first()
        
        if share_info:
            can_view = True
            can_edit_shared = share_info.can_edit
        elif plan.is_public: # Allow viewing if public, even if not explicitly shared or owned
            can_view = True

    if not can_view:
        flash('You do not have access to this travel plan.', 'danger')
        return redirect(url_for('planner.index'))
    
    # Calculate total cost from all itinerary items
    total_cost = 0
    
    # Group itinerary items by day
    itinerary_by_day = {}
    
    # Prepare itinerary items for JSON serialization
    itinerary_items_json = []
    for item in plan.itinerary_items:
        if item.cost:
            total_cost += item.cost
        
        # Group by day for template rendering
        if item.day not in itinerary_by_day:
            itinerary_by_day[item.day] = []
        itinerary_by_day[item.day].append(item)
        
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
    
    # Convert dictionary to sorted list of tuples for Jinja
    itinerary_by_day = sorted(itinerary_by_day.items())
    
    # Optional: Calculate expense categories
    categories = {}
    for item in plan.itinerary_items:
        if item.cost:
            activity_type = item.activity.split(' ')[0] if item.activity else 'Other'
            if activity_type not in categories:
                categories[activity_type] = 0
            categories[activity_type] += float(item.cost)
            
    return render_template(
        'planner/view.html', 
        plan=plan, 
        total_cost=total_cost, 
        itinerary_items_json=itinerary_items_json,
        itinerary_by_day=itinerary_by_day,
        categories=categories,
        # Pass edit permission for shared users if needed in template
        # current_user_can_edit = (plan.user_id == current_user.id) or (share_info and share_info.can_edit if 'share_info' in locals() else False)
        user_can_edit_this_plan=(plan.user_id == current_user.id or can_edit_shared)
    )

@planner_bp.route('/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_plan(plan_id):
    """Edit an existing travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    user_can_edit = False

    if plan.user_id == current_user.id:
        user_can_edit = True
    else:
        share_info = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_user_id=current_user.id,
            status='accepted',
            can_edit=True
        ).first()
        if share_info:
            user_can_edit = True
            
    if not user_can_edit:
        flash('You do not have permission to edit this travel plan.', 'danger')
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
        
        # Get location coordinates
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        
        # 转Change the coordinates to floating-point numbers (if provided)
        if lat and lat.strip():
            plan.dest_lat = float(lat)
        if lng and lng.strip():
            plan.dest_lng = float(lng)
        
        db.session.commit()
        
        flash('Travel plan updated successfully!', 'success')
        return redirect(url_for('planner.view_plan', plan_id=plan.id))
        
    return render_template('planner/edit.html', plan=plan)

@planner_bp.route('/<int:plan_id>/itinerary', methods=['GET', 'POST'])
@login_required
def manage_itinerary(plan_id):
    """Manage itinerary items for a travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    user_can_edit = False

    if plan.user_id == current_user.id:
        user_can_edit = True
    else:
        share_info = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_user_id=current_user.id,
            status='accepted',
            can_edit=True
        ).first()
        if share_info:
            user_can_edit = True

    if not user_can_edit:
        flash('You do not have permission to edit this itinerary.', 'danger')
        return redirect(url_for('planner.view_plan', plan_id=plan_id))
    
    if request.method == 'POST':
        # send JSON data for AJAX requests
        if request.is_xhr or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # get data from request
                data = request.json
                
                # add day, time, activity, location
                day = int(data.get('day'))
                time = data.get('time')
                activity = data.get('activity')
                location = data.get('location')
                
                # handle empty strings for lat/lng/cost
                lat_str = data.get('lat')
                lat = float(lat_str) if lat_str and lat_str.strip() else None
                
                lng_str = data.get('lng')
                lng = float(lng_str) if lng_str and lng_str.strip() else None
                
                cost_str = data.get('cost')
                cost = float(cost_str) if cost_str and cost_str.strip() else 0
                
                notes = data.get('notes')
                
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
                
                # return a JSON response with the new item
                return jsonify({
                    'success': True,
                    'message': 'Itinerary item added successfully!',
                    'item': {
                        'id': item.id,
                        'day': item.day,
                        'time': item.time,
                        'activity': item.activity,
                        'location': item.location,
                        'lat': item.lat,
                        'lng': item.lng,
                        'cost': float(item.cost) if item.cost else 0,
                        'notes': item.notes
                    }
                })
                
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Error adding itinerary item: {str(e)}'
                }), 400
        
        # handle form submission
        else:
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
    """Share a travel plan with another user by email."""
    plan = TravelPlan.query.get_or_404(plan_id)

    # Ensure only the plan owner can share
    if plan.user_id != current_user.id:
        flash('You do not have permission to share this plan.', 'danger')
        return redirect(url_for('planner.view_plan', plan_id=plan_id))

    if request.method == 'POST':
        email = request.form.get('email')
        can_edit = 'can_edit' in request.form

        if not email:
            flash('Email address is required.', 'warning')
            return redirect(url_for('planner.share_plan', plan_id=plan_id))

        target_user = User.query.filter_by(email=email).first()

        if not target_user:
            flash(f'User with email "{email}" not found.', 'danger')
            return redirect(url_for('planner.share_plan', plan_id=plan_id))

        if target_user.id == current_user.id:
            flash('You cannot share a plan with yourself.', 'warning')
            return redirect(url_for('planner.share_plan', plan_id=plan_id))

        existing_share = PlanShare.query.filter_by(
            travel_plan_id=plan.id,
            shared_user_id=target_user.id
        ).first()

        if existing_share:
            if existing_share.status == 'pending':
                flash(f'A share invitation is already pending for {email}.', 'info')
            elif existing_share.status == 'accepted':
                flash(f'This plan is already shared with {email}. You can manage permissions if needed or revoke and re-share.', 'info')
            elif existing_share.status == 'rejected':
                # If previously rejected, update the existing share to pending and set new permissions
                existing_share.status = 'pending'
                existing_share.can_edit = can_edit
                existing_share.created_at = datetime.utcnow() # Optionally update timestamp
                db.session.commit()
                flash(f'Re-sent sharing invitation to {email}. They will need to accept it.', 'success')
            else: # Other statuses, treat as re-share opportunity or specific handling
                # For now, let's assume we can re-activate by setting to pending
                existing_share.status = 'pending'
                existing_share.can_edit = can_edit
                existing_share.created_at = datetime.utcnow()
                db.session.commit()
                flash(f'Sharing invitation for {email} has been re-activated.', 'success')
            return redirect(url_for('planner.share_plan', plan_id=plan_id))

        # Create new share if no existing_share record or if we decided to create new for rejected ones
        new_share = PlanShare(
            travel_plan_id=plan.id,
            shared_user_id=target_user.id,
            can_edit=can_edit,
            status='pending'  # Explicitly set status
        )
        db.session.add(new_share)
        db.session.commit()

        flash(f'Travel plan shared with {email}. They will need to accept the invitation.', 'success')
        return redirect(url_for('planner.share_plan', plan_id=plan_id))

    # For GET request, display shares
    # Ensure shares are queried using shared_user_id and relationship to User for email/username
    current_shares = PlanShare.query.filter_by(travel_plan_id=plan.id).all()
    
    # We need to pass user details (like email or username) to the template
    # The PlanShare model now has 'shared_user' relationship
    
    return render_template('planner/share.html', plan=plan, shares=current_shares)

@planner_bp.route('/share_response/<int:share_id>', methods=['POST'])
@login_required
def respond_to_share(share_id):
    share_invitation = PlanShare.query.get_or_404(share_id)

    # Security check: Ensure the current user is the one invited
    if share_invitation.shared_user_id != current_user.id:
        flash('You do not have permission to respond to this invitation.', 'danger')
        return redirect(url_for('planner.index'))

    # Ensure the invitation is still pending
    if share_invitation.status != 'pending':
        flash('This invitation is no longer active or has already been responded to.', 'info')
        # Redirect to plan view if accepted, otherwise to index
        if share_invitation.status == 'accepted':
            return redirect(url_for('planner.view_plan', plan_id=share_invitation.travel_plan_id))
        return redirect(url_for('planner.index'))

    action = request.form.get('action')

    if action == 'accept':
        share_invitation.status = 'accepted'
        db.session.commit()
        flash('Sharing invitation accepted!', 'success')
        # Redirect to the plan they just accepted
        return redirect(url_for('planner.view_plan', plan_id=share_invitation.travel_plan_id))
    elif action == 'reject':
        share_invitation.status = 'rejected'
        # Optionally, you might delete the PlanShare record upon rejection 
        # or keep it as 'rejected' for auditing/history.
        # For now, let's mark as rejected.
        # db.session.delete(share_invitation) # Alternative: delete it
        db.session.commit()
        flash('Sharing invitation rejected.', 'info')
    else:
        flash('Invalid action.', 'danger')

    return redirect(url_for('planner.index'))

@planner_bp.route('/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    """Delete a travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user owns this plan
    if plan.user_id != current_user.id:
        flash('You do not have permission to delete this plan', 'danger')
        return redirect(url_for('planner.index'))
    
    # Delete the plan
    db.session.delete(plan)
    db.session.commit()
    
    flash('Travel plan deleted successfully', 'success')
    return redirect(url_for('planner.index'))

@planner_bp.route('/<int:plan_id>/toggle_public', methods=['POST'])
@login_required
def toggle_public(plan_id):
    """Toggle the public/private status of a travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user owns this plan
    if plan.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'You do not have permission to modify this plan'}), 403
    
    # Get data from request
    data = request.json
    is_public = data.get('is_public', False)
    
    # Update the plan's public status
    plan.is_public = is_public
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_public': plan.is_public,
        'message': f'Plan is now {"public" if is_public else "private"}'
    })

@planner_bp.route('/<int:plan_id>/remove_share/<int:share_id>', methods=['POST'])
@login_required
def remove_share(plan_id, share_id):
    """Remove a share from a travel plan"""
    # Get the plan and check if the current user owns it
    plan = TravelPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        flash('You do not have permission to modify this plan', 'danger')
        return redirect(url_for('planner.index'))
    
    # Get the share and delete it
    share = PlanShare.query.get_or_404(share_id)
    
    # Verify the share belongs to this plan
    if share.travel_plan_id != plan_id:
        flash('Invalid share removal request', 'danger')
        return redirect(url_for('planner.share_plan', plan_id=plan_id))
    
    email = share.shared_email
    db.session.delete(share)
    db.session.commit()
    
    flash(f'Sharing with {email} has been removed', 'success')
    return redirect(url_for('planner.share_plan', plan_id=plan_id))

@planner_bp.route('/recommend')
@login_required
def recommend_destinations():
    """Smart destination recommendation page"""
    return render_template('planner/recommend.html')

@planner_bp.route('/<int:plan_id>/ai_recommendations', methods=['POST'])
@login_required
def ai_recommendations(plan_id):
    """Get AI recommended activities based on travel plan"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user has permission to access this plan
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email
        ).first()
        
        if not shared and not plan.is_public:
            return jsonify({'success': False, 'message': 'You do not have permission to access this plan'}), 403
    
    # Get day data from request
    data = request.json
    day = data.get('day', 1)
    
    # Cache parameters for this recommendation
    cache_params = {
        'plan_id': plan_id,
        'day': day,
        'destination': plan.destination,
        'interests': plan.interests or '',
        'start_date': plan.start_date.strftime('%Y-%m-%d'),
        'end_date': plan.end_date.strftime('%Y-%m-%d'),
        'endpoint': 'ai_recommendations'
    }
    
    # Check cache first
    cached_response = get_cached_response('ai_recommendations', cache_params)
    if cached_response:
        print(f"Using cached AI recommendations for plan {plan_id}, day {day}")
        return jsonify(cached_response)
    
    # Prepare prompt in English
    prompt_text = f"""
    Recommend 5 different activities for Day {day} of the following travel plan:
    
    Destination: {plan.destination}
    Trip dates: {plan.start_date.strftime('%Y-%m-%d')} to {plan.end_date.strftime('%Y-%m-%d')}
    Interests: {plan.interests or 'Not specified'}
    
    Please return 5 recommended activities in JSON format as follows:
    [
        {{
            "activity": "Activity name",
            "location": "Location",
            "cost": Estimated cost (number only),
            "description": "Brief description",
            "time_spent": "Estimated time (e.g.: 2 hours)",
            "latitude": Approximate latitude (number only),
            "longitude": Approximate longitude (number only)
        }},
        ...
    ]
    """
    
    # Prepare Gemini API request data
    request_data = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    try:
        # Call Gemini API directly
        api_url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json=request_data
        )
        
        # Check response status
        response.raise_for_status()
        response_data = response.json()
        
        # Extract text from response
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            response_text = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Extract JSON part from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                recommendations = json.loads(json_str)
                
                # Ensure lat/lng are parsed correctly if present
                for rec in recommendations:
                    rec['lat'] = rec.pop('latitude', None) # Rename latitude to lat
                    rec['lng'] = rec.pop('longitude', None) # Rename longitude to lng
                    # Attempt to convert to float, default to None if invalid
                    try:
                        rec['lat'] = float(rec['lat']) if rec['lat'] is not None else None
                    except (ValueError, TypeError):
                        rec['lat'] = None
                    try:
                        rec['lng'] = float(rec['lng']) if rec['lng'] is not None else None
                    except (ValueError, TypeError):
                        rec['lng'] = None

                response_payload = {
                    'success': True, 
                    'recommendations': recommendations,
                    'day': day
                }
                
                # Cache the response
                set_cached_response('ai_recommendations', cache_params, response_payload)
                print(f"Cached AI recommendations for plan {plan_id}, day {day}")
                
                return jsonify(response_payload)
            else:
                # Failed to format response, return raw response
                return jsonify({
                    'success': False, 
                    'message': 'Failed to parse API response',
                    'raw_response': response_text
                }), 500
        else:
            return jsonify({
                'success': False, 
                'message': 'Invalid API response format',
                'raw_response': response_data
            }), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False, 
            'message': f'API request error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error getting recommendations: {str(e)}'
        }), 500

@planner_bp.route('/<int:plan_id>/add_recommendation', methods=['POST'])
@login_required
def add_recommendation(plan_id):
    """Add AI recommended activity to the itinerary"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user has permission to edit this plan
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email,
            can_edit=True
        ).first()
        
        if not shared:
            return jsonify({'success': False, 'message': 'You do not have permission to edit this plan'}), 403
    
    try:
        # Get activity data from request
        data = request.json
        print(f"DEBUG - Received recommendation data: {data}")
        
        day = int(data.get('day')) if data.get('day') else 1
        activity = data.get('activity')
        location = data.get('location')
        
        # handle empty strings for cost
        cost_raw = data.get('cost', 0)
        cost = float(cost_raw) if cost_raw and str(cost_raw).strip() else 0
        notes = data.get('description')
        
        # add lat/lng handling - ensure they are received correctly
        lat = None
        lng = None
        
        # try to extract lat/lng from the data
        if 'lat' in data and data['lat'] is not None and 'lng' in data and data['lng'] is not None:
            try:
                lat = float(data['lat'])
                lng = float(data['lng'])
                print(f"DEBUG - Parsed lat/lng: {lat}, {lng}") # Add log for parsed coords
            except (ValueError, TypeError) as e:
                # if conversion fails, set lat/lng to None
                print(f"DEBUG - Error parsing lat/lng: {e}. Data was: lat={data.get('lat')}, lng={data.get('lng')}")
                lat = None
                lng = None
        else:
             print(f"DEBUG - Lat/Lng not found or null in data: lat={data.get('lat')}, lng={data.get('lng')}")


        # create a new itinerary item
        item = ItineraryItem(
            day=day,
            activity=activity,
            location=location,
            cost=cost,
            notes=notes,
            lat=lat,
            lng=lng,
            travel_plan_id=plan_id
        )
        
        db.session.add(item)
        db.session.commit()
        
        print(f"DEBUG - Added item successfully: id={item.id}")
        
        # add the new item to the itinerary items JSON
        itinerary_items_json = []
        for item in plan.itinerary_items:
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
        
        # return a JSON response with the new item and all itinerary items
        return jsonify({
            'success': True,
            'message': 'Activity has been added to your itinerary',
            'item': {
                'id': item.id,
                'day': item.day,
                'time': item.time,
                'activity': item.activity,
                'location': item.location,
                'lat': item.lat,
                'lng': item.lng,
                'cost': float(item.cost) if item.cost else 0,
                'notes': item.notes
            },
            'itinerary_items_json': itinerary_items_json
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR - Failed to add recommendation: {str(e)}")
        print(f"ERROR - Traceback: {error_details}")
        return jsonify({
            'success': False, 
            'message': f'Error adding activity: {str(e)}'
        }), 500

@planner_bp.route('/<int:plan_id>/get_itinerary_data')
@login_required
def get_itinerary_data(plan_id):
    """Get updated itinerary data for AJAX updates"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user has permission to access this plan
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email
        ).first()
        
        if not shared and not plan.is_public:
            return jsonify({'success': False, 'message': 'You do not have permission to access this plan'}), 403
    
    # Calculate total cost from all itinerary items
    total_cost = 0
    
    # Generate day_dates array needed by the frontend
    day_dates = []
    for i in range((plan.end_date - plan.start_date).days + 1):
        current_date = (plan.start_date + timedelta(days=i)).strftime('%b %d, %Y')
        day_dates.append(current_date)
    
    # Group itinerary items by day
    itinerary_by_day = {}
    
    # Prepare itinerary items for JSON serialization
    itinerary_items_json = []
    for item in plan.itinerary_items:
        if item.cost:
            total_cost += item.cost
        
        # Group by day for template rendering
        if item.day not in itinerary_by_day:
            itinerary_by_day[item.day] = []
        itinerary_by_day[item.day].append({
            'id': item.id,
            'day': item.day,
            'time': item.time,
            'activity': item.activity,
            'location': item.location,
            'cost': float(item.cost) if item.cost else 0,
            'notes': item.notes
        })
        
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
    
    # Calculate expense categories
    categories = {}
    for item in plan.itinerary_items:
        if item.cost:
            activity_type = item.activity.split(' ')[0] if item.activity else 'Other'
            if activity_type not in categories:
                categories[activity_type] = 0
            categories[activity_type] += float(item.cost)
    
    # Convert dictionary to list of tuples for frontend compatibility
    itinerary_by_day_list = []
    for day, items in sorted(itinerary_by_day.items()):
        itinerary_by_day_list.append((day, items))
    
    return jsonify({
        'success': True,
        'total_cost': total_cost,
        'budget': plan.budget,
        'itinerary_items_json': itinerary_items_json,
        'itinerary_by_day': itinerary_by_day_list,
        'categories': categories,
        'day_dates': day_dates
    })

@planner_bp.route('/<int:plan_id>/delete_itinerary_item', methods=['POST'])
@login_required
def standard_delete_itinerary_item(plan_id):
    """Delete an itinerary item"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user has permission to edit this plan
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email,
            can_edit=True
        ).first()
        
        if not shared:
            return jsonify({'success': False, 'message': 'You do not have permission to edit this plan'}), 403
    
    # Get data from request
    data = request.json
    item_id = data.get('item_id')
    
    if not item_id:
        return jsonify({'success': False, 'message': 'No item ID provided'}), 400
    
    # Get the item and verify it belongs to the plan
    item = ItineraryItem.query.get_or_404(item_id)
    
    if item.travel_plan_id != plan_id:
        return jsonify({'success': False, 'message': 'Item does not belong to this plan'}), 403
    
    # Delete the item
    db.session.delete(item)
    db.session.commit()
    print(f"DEBUG: Deleted item with ID: {item_id}") # Log deletion confirmation

    # After deleting, fetch the updated list of itinerary items
    updated_items = ItineraryItem.query.filter_by(travel_plan_id=plan_id).order_by(ItineraryItem.day, ItineraryItem.time).all()
    print(f"DEBUG: Fetched {len(updated_items)} remaining items for plan {plan_id}") # Log count of remaining items

    itinerary_items_json = []
    total_cost = 0
    try:
        for updated_item in updated_items:
            if updated_item.cost:
                total_cost += updated_item.cost
            itinerary_items_json.append({
                'id': updated_item.id,
                'day': updated_item.day,
                'time': updated_item.time,
                'activity': updated_item.activity,
                'location': updated_item.location,
                'lat': updated_item.lat,
                'lng': updated_item.lng,
                'cost': float(updated_item.cost) if updated_item.cost else 0,
                'notes': updated_item.notes
            })
        print(f"DEBUG: Successfully built itinerary_items_json with {len(itinerary_items_json)} items.") # Log successful build
    except Exception as e:
        print(f"ERROR: Failed to build itinerary_items_json: {e}") # Log any error during build
        itinerary_items_json = [] # Ensure it's an empty list on error

    # Log the data just before returning
    print(f"DEBUG: Returning JSON data: success=True, message='Activity removed successfully', itinerary_items_json={json.dumps(itinerary_items_json)}, total_cost={total_cost}")

    return jsonify({
        'success': True,
        'message': 'Activity removed successfully',
        'itinerary_items_json': itinerary_items_json,
        'total_cost': total_cost
    })

@planner_bp.route('/<int:plan_id>/update_item_time', methods=['POST'])
@login_required
def update_item_time(plan_id):
    """Update the time for an itinerary item"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # Check if user has permission to edit this plan
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email,
            can_edit=True
        ).first()
        
        if not shared:
            return jsonify({'success': False, 'message': 'You do not have permission to edit this plan'}), 403
    
    # Get data from request
    data = request.json
    item_id = data.get('item_id')
    time = data.get('time')
    
    # Add debug logs
    print(f"DEBUG - Updating time: item_id={item_id}, time={time}, type(time)={type(time)}")
    
    if not item_id:
        return jsonify({'success': False, 'message': 'No item ID provided'}), 400
    
    # Get the item and verify it belongs to the plan
    item = ItineraryItem.query.get_or_404(item_id)
    
    if item.travel_plan_id != plan_id:
        return jsonify({'success': False, 'message': 'Item does not belong to this plan'}), 403
    
    # Add debug log - display the current time value
    print(f"DEBUG - Before update: item.time={item.time}, type={type(item.time)}")
    
    # Update the time
    item.time = time
    try:
        db.session.commit()
        print(f"DEBUG - After successful update: item.time={item.time}")
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG - Database error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error saving to database: {str(e)}'}), 500
    
    # Optional: Format the time for display (e.g. 14:30 -> 2:30 PM)
    formatted_time = None
    if time and isinstance(time, str) and ':' in time:
        try:
            # Parse time string into hours and minutes
            hours, minutes = map(int, time.split(':'))
            period = "AM"
            
            # Validate hours and minutes
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                # Convert to 12-hour format
                if hours >= 12:
                    period = "PM"
                    if hours > 12:
                        hours -= 12
                elif hours == 0:
                    hours = 12
                    
                formatted_time = f"{hours}:{minutes:02d} {period}"
            else:
                formatted_time = time
        except Exception:
            # If any error occurs during formatting, just use the original time
            formatted_time = time
    else:
        formatted_time = time
    
    return jsonify({
        'success': True,
        'message': 'Time updated successfully',
        'formatted_time': formatted_time
    })

@planner_bp.route('/get_recommendations', methods=['POST'])
@login_required
def get_recommendations():
    """API endpoint for getting destination recommendations based on preferences"""
    # Get preference data from request
    data = request.json
    
    # Extract preferences
    destination = data.get('destination', '')
    interests = data.get('interests', '')
    budget = data.get('budget', '')
    season = data.get('season', '')
    duration = data.get('duration', '')
    
    # In a real application, you would use these preferences to query a database
    # or call an external API to get personalized recommendations
    # For now, let's generate some example destinations based on interests
    
    # Sample destination data based on interests
    destinations_by_interest = {
        'beaches': [
            {"name": "Bali, Indonesia", "lat": -8.4095, "lng": 115.1889, "description": "Tropical paradise with stunning beaches and vibrant culture", "category": "Islands", "budget_level": "Moderate"},
            {"name": "Maldives", "lat": 3.2028, "lng": 73.2207, "description": "Luxurious overwater bungalows and crystal-clear waters", "category": "Islands", "budget_level": "Luxury"},
            {"name": "Cancun, Mexico", "lat": 21.1619, "lng": -86.8515, "description": "Beautiful beaches with plenty of nightlife and activities", "category": "Beach Resort", "budget_level": "Moderate"}
        ],
        'mountains': [
            {"name": "Swiss Alps, Switzerland", "lat": 46.8182, "lng": 8.2275, "description": "Picturesque mountains with world-class hiking and skiing", "category": "Mountains", "budget_level": "Luxury"},
            {"name": "Banff, Canada", "lat": 51.1784, "lng": -115.5708, "description": "Stunning mountain scenery with crystal-clear lakes", "category": "National Park", "budget_level": "Moderate"},
            {"name": "Himalayas, Nepal", "lat": 28.3949, "lng": 84.1240, "description": "Majestic mountain range with challenging treks and breathtaking views", "category": "Trekking", "budget_level": "Budget"}
        ],
        'cities': [
            {"name": "Tokyo, Japan", "lat": 35.6762, "lng": 139.6503, "description": "Vibrant metropolis with cutting-edge technology and ancient traditions", "category": "Urban", "budget_level": "Moderate"},
            {"name": "Paris, France", "lat": 48.8566, "lng": 2.3522, "description": "Iconic city of art, fashion, and gastronomy", "category": "Cultural", "budget_level": "Moderate"},
            {"name": "New York City, USA", "lat": 40.7128, "lng": -74.0060, "description": "The city that never sleeps with world-class attractions", "category": "Urban", "budget_level": "Luxury"}
        ],
        'culture': [
            {"name": "Kyoto, Japan", "lat": 35.0116, "lng": 135.7681, "description": "Ancient temples and traditional Japanese culture", "category": "Historical", "budget_level": "Moderate"},
            {"name": "Rome, Italy", "lat": 41.9028, "lng": 12.4964, "description": "Ancient ruins and Renaissance art in the Eternal City", "category": "Historical", "budget_level": "Moderate"},
            {"name": "Marrakech, Morocco", "lat": 31.6295, "lng": -7.9811, "description": "Vibrant markets and rich cultural heritage", "category": "Cultural", "budget_level": "Budget"}
        ],
        'food': [
            {"name": "Bangkok, Thailand", "lat": 13.7563, "lng": 100.5018, "description": "Street food paradise with vibrant flavors", "category": "Culinary", "budget_level": "Budget"},
            {"name": "Bologna, Italy", "lat": 44.4949, "lng": 11.3426, "description": "The gastronomic capital of Italy with authentic cuisine", "category": "Culinary", "budget_level": "Moderate"},
            {"name": "San Sebastian, Spain", "lat": 43.3183, "lng": -1.9812, "description": "Renowned for its pintxos and Michelin-starred restaurants", "category": "Culinary", "budget_level": "Luxury"}
        ],
        'adventure': [
            {"name": "Queenstown, New Zealand", "lat": -45.0312, "lng": 168.6626, "description": "Adventure capital with bungee jumping, skiing, and more", "category": "Adventure", "budget_level": "Moderate"},
            {"name": "Costa Rica", "lat": 9.7489, "lng": -83.7534, "description": "Ziplines, surfing, and rainforest adventures", "category": "Eco-Adventure", "budget_level": "Moderate"},
            {"name": "Moab, Utah, USA", "lat": 38.5733, "lng": -109.5498, "description": "Desert adventures including mountain biking and rock climbing", "category": "Outdoor", "budget_level": "Budget"}
        ],
        'nature': [
            {"name": "Serengeti, Tanzania", "lat": -2.3333, "lng": 34.8333, "description": "Witness the great migration and abundant wildlife", "category": "Safari", "budget_level": "Luxury"},
            {"name": "Amazon Rainforest, Brazil", "lat": -3.4653, "lng": -62.2159, "description": "Explore the world's largest rainforest and its biodiversity", "category": "Eco-Tourism", "budget_level": "Moderate"},
            {"name": "Yellowstone, USA", "lat": 44.4280, "lng": -110.5885, "description": "Geysers, hot springs, and wildlife in America's first national park", "category": "National Park", "budget_level": "Budget"}
        ],
        'relax': [
            {"name": "Santorini, Greece", "lat": 36.3932, "lng": 25.4615, "description": "Breathtaking sunsets and white-washed buildings", "category": "Island", "budget_level": "Luxury"},
            {"name": "Bora Bora, French Polynesia", "lat": -16.5004, "lng": -151.7415, "description": "Overwater bungalows in a tranquil paradise", "category": "Island", "budget_level": "Luxury"},
            {"name": "Tulum, Mexico", "lat": 20.2114, "lng": -87.4654, "description": "Yoga retreats and eco-resorts on pristine beaches", "category": "Wellness", "budget_level": "Moderate"}
        ]
    }
    
    # Add regional destination mapping
    regional_destinations = {
        "japan": ["Tokyo, Japan", "Kyoto, Japan", "Osaka, Japan", "Hokkaido, Japan", "Okinawa, Japan"],
        "france": ["Paris, France", "Nice, France", "Bordeaux, France", "Lyon, France", "Marseille, France"],
        "italy": ["Rome, Italy", "Venice, Italy", "Florence, Italy", "Bologna, Italy", "Amalfi Coast, Italy"],
        "spain": ["Barcelona, Spain", "Madrid, Spain", "Seville, Spain", "San Sebastian, Spain", "Valencia, Spain"],
        "mexico": ["Cancun, Mexico", "Mexico City, Mexico", "Tulum, Mexico", "Puerto Vallarta, Mexico", "Oaxaca, Mexico"],
        "thailand": ["Bangkok, Thailand", "Phuket, Thailand", "Chiang Mai, Thailand", "Koh Samui, Thailand", "Krabi, Thailand"],
        "usa": ["New York City, USA", "San Francisco, USA", "Yellowstone, USA", "Moab, Utah, USA", "Hawaii, USA"],
        "canada": ["Banff, Canada", "Vancouver, Canada", "Toronto, Canada", "Quebec City, Canada", "Montreal, Canada"],
        "australia": ["Sydney, Australia", "Melbourne, Australia", "Great Barrier Reef, Australia", "Gold Coast, Australia", "Perth, Australia"],
        "china": ["Beijing, China", "Shanghai, China", "Xi'an, China", "Guilin, China", "Hong Kong"],
        "uk": ["London, UK", "Edinburgh, UK", "Bath, UK", "Lake District, UK", "Oxford, UK"],
        "england": ["London, UK", "Bath, UK", "Oxford, UK", "Cambridge, UK", "Cornwall, UK"],
        "greece": ["Santorini, Greece", "Athens, Greece", "Mykonos, Greece", "Crete, Greece", "Rhodes, Greece"],
        "brazil": ["Rio de Janeiro, Brazil", "Amazon Rainforest, Brazil", "São Paulo, Brazil", "Salvador, Brazil", "Iguazu Falls, Brazil"],
        "india": ["Delhi, India", "Agra, India", "Jaipur, India", "Mumbai, India", "Goa, India"],
        "indonesia": ["Bali, Indonesia", "Jakarta, Indonesia", "Yogyakarta, Indonesia", "Lombok, Indonesia", "Borneo, Indonesia"],
        "egypt": ["Cairo, Egypt", "Luxor, Egypt", "Nile River, Egypt", "Alexandria, Egypt", "Sharm El Sheikh, Egypt"],
        "morocco": ["Marrakech, Morocco", "Casablanca, Morocco", "Fez, Morocco", "Chefchaouen, Morocco", "Sahara Desert, Morocco"],
        "europe": ["Paris, France", "Rome, Italy", "Santorini, Greece", "Barcelona, Spain", "Switzerland Alps"]
    }
    
    # Default to a mix of destinations if no interest specified
    recommendations = []
    
    # First, check if we have a specific destination input
    has_specific_input = False
    user_destination = None
    user_destination_coords = None
    
    # Hard-coded geocoding for common destinations
    geocoded_places = {
        "tokyo": {"lat": 35.6762, "lng": 139.6503},
        "paris": {"lat": 48.8566, "lng": 2.3522},
        "london": {"lat": 51.5074, "lng": -0.1278},
        "new york": {"lat": 40.7128, "lng": -74.0060},
        "nyc": {"lat": 40.7128, "lng": -74.0060},
        "rome": {"lat": 41.9028, "lng": 12.4964},
        "bali": {"lat": -8.4095, "lng": 115.1889},
        "kyoto": {"lat": 35.0116, "lng": 135.7681},
        "barcelona": {"lat": 41.3851, "lng": 2.1734},
        "sydney": {"lat": -33.8688, "lng": 151.2093},
        "bangkok": {"lat": 13.7563, "lng": 100.5018},
        "hong kong": {"lat": 22.3193, "lng": 114.1694},
        "beijing": {"lat": 39.9042, "lng": 116.4074},
        "delhi": {"lat": 28.7041, "lng": 77.1025},
        "dubai": {"lat": 25.2048, "lng": 55.2708},
        "cape town": {"lat": -33.9249, "lng": 18.4241},
        "rio": {"lat": -22.9068, "lng": -43.1729},
        "mexico city": {"lat": 19.4326, "lng": -99.1332},
        "cairo": {"lat": 30.0444, "lng": 31.2357},
        "marrakech": {"lat": 31.6295, "lng": -7.9811},
        "italy": {"lat": 41.8719, "lng": 12.5674},
        "japan": {"lat": 36.2048, "lng": 138.2529},
        "france": {"lat": 46.6034, "lng": 1.8883},
        "spain": {"lat": 40.4637, "lng": -3.7492},
        "china": {"lat": 35.8617, "lng": 104.1954},
        "canada": {"lat": 56.1304, "lng": -106.3468},
        "brazil": {"lat": -14.2350, "lng": -51.9253},
        "australia": {"lat": -25.2744, "lng": 133.7751},
        "india": {"lat": 20.5937, "lng": 78.9629},
        "mexico": {"lat": 23.6345, "lng": -102.5528},
        "germany": {"lat": 51.1657, "lng": 10.4515},
        "thailand": {"lat": 15.8700, "lng": 100.9925},
        "uk": {"lat": 55.3781, "lng": -3.4360},
        "england": {"lat": 52.3555, "lng": -1.1743},
        "united kingdom": {"lat": 55.3781, "lng": -3.4360},
        "united states": {"lat": 37.0902, "lng": -95.7129},
        "usa": {"lat": 37.0902, "lng": -95.7129},
        "us": {"lat": 37.0902, "lng": -95.7129},
        "america": {"lat": 37.0902, "lng": -95.7129},
        "europe": {"lat": 54.5260, "lng": 15.2551}
    }
    
    if destination and len(destination) >= 2:
        destination_lower = destination.lower()
        
        # Try to find exact destination in our geocoded_places
        if destination_lower in geocoded_places:
            coords = geocoded_places[destination_lower]
            user_destination = destination
            user_destination_coords = coords
            has_specific_input = True
            
        # Fallback to checking if it's a country or region
        elif destination_lower in regional_destinations:
            regional_options = regional_destinations[destination_lower]
            # Add regional options to recommendations
            for place_name in regional_options:
                for interest, places in destinations_by_interest.items():
                    for place in places:
                        if place["name"] == place_name:
                            recommendations.append(place)
                            break
            
            # Make sure at least one recommendation is included by checking all known places
            if len(recommendations) == 0:
                for interest, places in destinations_by_interest.items():
                    for place in places:
                        if destination_lower in place["name"].lower():
                            recommendations.append(place)
            
            # Still use coordinates for the region/country
            if destination_lower in geocoded_places:
                user_destination = destination
                user_destination_coords = geocoded_places[destination_lower]
                has_specific_input = True
    
    # If no specific recommendations for destination yet, or we're doing a general search
    if len(recommendations) == 0:
        if interests in destinations_by_interest:
            recommendations = destinations_by_interest[interests].copy()
        else:
            # Mix from all categories
            for interest_destinations in destinations_by_interest.values():
                recommendations.extend(random.sample(interest_destinations, 1))
    
    # Filter by budget if specified
    if budget:
        budget_mapping = {
            'budget': 'Budget',
            'moderate': 'Moderate',
            'luxury': 'Luxury'
        }
        if budget in budget_mapping:
            budget_level = budget_mapping[budget]
            # Only filter if we'd have results left
            filtered = [r for r in recommendations if r['budget_level'] == budget_level]
            if filtered:
                recommendations = filtered
    
    # If destination was specified but no exact match, prioritize destinations containing the query
    if destination and len(destination) > 2 and not has_specific_input:
        destination_lower = destination.lower()
        # Move matching destinations to the front
        matching_destinations = []
        other_destinations = []
        
        for rec in recommendations:
            if destination_lower in rec['name'].lower() or destination_lower in rec['description'].lower():
                matching_destinations.append(rec)
            else:
                other_destinations.append(rec)
        
        recommendations = matching_destinations + other_destinations
    
    # Limit to 5 recommendations max
    recommendations = recommendations[:5]
    
    # Add a bit of randomness so results aren't always the same
    random.shuffle(recommendations)
    
    # Return user's destination input along with recommendations
    return jsonify({
        'success': True,
        'recommendations': recommendations,
        'user_destination': {
            'name': user_destination,
            'coords': user_destination_coords
        } if has_specific_input else None
    })

@planner_bp.route('/<int:plan_id>/itinerary/data', methods=['GET'])
@login_required
def get_itinerary_items_data(plan_id):
    """Get all itinerary items for a plan as JSON - for AJAX updates"""
    plan = TravelPlan.query.get_or_404(plan_id)
    
    # check if user has permission to access this plan
    if plan.user_id != current_user.id:
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id, 
            shared_email=current_user.email
        ).first()
        
        if not shared:
            return jsonify({
                'success': False,
                'message': 'You do not have permission to view this itinerary'
            }), 403
    
    # get all itinerary items for the plan
    items = ItineraryItem.query.filter_by(travel_plan_id=plan_id).order_by(
        ItineraryItem.day, ItineraryItem.time
    ).all()
    
    # create a list of dictionaries to hold the item data
    result = []
    for item in items:
        result.append({
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
    
    return jsonify({
        'success': True,
        'items': result
    })

@planner_bp.route('/api/location_recommendations', methods=['POST'])
@login_required
def location_recommendations():
    """Get AI recommendations for a location"""
    try:
        # Get location data from request
        data = request.json
        location = data.get('location')
        
        if not location:
            return jsonify({'success': False, 'message': 'Location is required'}), 400
        
        # Cache key parameters for this request
        cache_params = {
            'location': location,
            'endpoint': 'location_recommendations'
        }
        
        # Check cache first
        cached_response = get_cached_response('location_recommendations', cache_params)
        if cached_response:
            print(f"Using cached recommendation for: {location}")
            return jsonify(cached_response)
            
        # Prepare prompt in English for more consistent and higher quality responses
        prompt_text = f"""
        Provide interesting information about {location} that would be useful for a traveler.
        Include:
        1. A brief overview
        2. 3-5 interesting facts
        3. Top 5 must-visit attractions
        4. Best time to visit
        5. Local cuisine specialties

        Format your response using markdown for better readability.
        """
        
        # Prepare Gemini API request data
        request_data = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }]
        }
        
        # Call Gemini API directly
        api_url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json=request_data
        )
        
        # Check response status
        response.raise_for_status()
        response_data = response.json()
        
        # Extract text from response
        if 'candidates' in response_data and len(response_data['candidates']) > 0:
            response_text = response_data['candidates'][0]['content']['parts'][0]['text']
            
            # Remove common AI style introductions
            cleaned_text = response_text
            
            # Remove common patterns like "Okay, here's a brief overview of Shanghai..."
            import re
            ai_intro_patterns = [
                r'^Okay,\s+.*?(?=\n)',
                r'^Sure,\s+.*?(?=\n)',
                r'^Here\s+(?:is|are).*?(?=\n)',
                r'^I\'d\s+be\s+happy\s+to.*?(?=\n)',
                r'^Here\'s\s+(?:some|the).*?(?=\n)',
                r'^Let\s+me\s+provide\s+you.*?(?=\n)',
                r'^I\'ll\s+provide\s+you.*?(?=\n)',
                r'^Certainly[\s,!]+.*?(?=\n)'
            ]
            
            for pattern in ai_intro_patterns:
                cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
            
            # Remove leading whitespace after removing the intro
            cleaned_text = cleaned_text.lstrip()
            
            # Prepare response payload
            response_payload = {
                'success': True, 
                'recommendation': cleaned_text,
                'location': location
            }
            
            # Cache the response for future requests
            set_cached_response('location_recommendations', cache_params, response_payload)
            print(f"Cached recommendation for: {location}")
            
            return jsonify(response_payload)
        else:
            return jsonify({
                'success': False, 
                'message': 'Invalid API response format',
                'raw_response': response_data
            }), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False, 
            'message': f'API request error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error getting recommendations: {str(e)}'
        }), 500

@planner_bp.route('/<int:plan_id>/update_item_day_time', methods=['POST'])
@login_required
def update_item_day_time(plan_id):
    """Update the day and time of an itinerary item."""
    plan = TravelPlan.query.get_or_404(plan_id)
    if plan.user_id != current_user.id:
        # Add permission check for shared plans if necessary
        shared = PlanShare.query.filter_by(
            travel_plan_id=plan_id,
            shared_email=current_user.email
        ).first()
        if not shared and not plan.is_public:
            return jsonify({'success': False, 'message': 'Permission denied'}), 403

    data = request.get_json()
    item_id = data.get('item_id')
    new_day = data.get('day')
    new_time_str = data.get('time') # Expected format: HH:mm or empty string

    if not item_id or not new_day:
        return jsonify({'success': False, 'message': 'Missing item ID or day'}), 400

    item = ItineraryItem.query.filter_by(id=item_id, travel_plan_id=plan_id).first()

    if not item:
        return jsonify({'success': False, 'message': 'Itinerary item not found'}), 404

    try:
        item.day = int(new_day)

        # Handle time update
        if new_time_str:
            # Validate and potentially store as time object or formatted string
            try:
                # Store as string 'HH:MM AM/PM' for consistency with current display?
                # Or store as time object? Let's try formatting for display consistency.
                parsed_time = datetime.strptime(new_time_str, '%H:%M').time()
                item.time = parsed_time.strftime('%I:%M %p').lstrip('0') # Format like '9:30 AM'
            except ValueError:
                # Handle invalid time format if necessary, maybe just store raw string?
                # For now, let's assume valid HH:mm input from <input type="time">
                 parsed_time = datetime.strptime(new_time_str, '%H:%M').time()
                 item.time = parsed_time.strftime('%I:%M %p').lstrip('0') # Re-attempt formatting
                 # If strict validation needed, return error here
        else:
            item.time = None # Clear the time

        db.session.commit()

        # Optionally, return updated itinerary data similar to delete/add
        # This helps keep the frontend perfectly in sync immediately
        # (Reusing logic from get_itinerary_data might be good here)
        # For simplicity now, just return success. Frontend will call updateItinerary().
        return jsonify({'success': True, 'message': 'Item updated successfully'})

    except ValueError:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Invalid day or time format'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error updating item day/time: {e}") # Log the error server-side
        return jsonify({'success': False, 'message': 'An internal error occurred'}), 500
