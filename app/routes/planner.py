from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.travel_plan import TravelPlan, ItineraryItem, PlanShare
from datetime import datetime
import random  # For generating random recommendations

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

@planner_bp.route('/')
@login_required
def index():
    """Travel planner main page listing user's travel plans"""
    # Get plans created by the user
    owned_plans = TravelPlan.query.filter_by(user_id=current_user.id).order_by(TravelPlan.start_date).all()
    
    # Get plans shared with the user
    shared_with_me = PlanShare.query.filter_by(shared_email=current_user.email).all()
    shared_plans = [share.travel_plan for share in shared_with_me]
    
    return render_template('planner/index.html', plans=owned_plans, shared_plans=shared_plans)

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
