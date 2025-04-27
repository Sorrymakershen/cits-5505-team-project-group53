from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.travel_plan import TravelPlan
from app.models.user import User
from datetime import datetime
import requests
import json
from math import radians, sin, cos, sqrt, atan2

statistics_bp = Blueprint('statistics', __name__, url_prefix='/statistics')

@statistics_bp.route('/')
@login_required
def index():
    """Travel statistics main page"""
    # Calculate various statistics
    travel_stats = calculate_travel_statistics(current_user)
    
    return render_template(
        'statistics/index.html', 
        stats=travel_stats, 
        home_address=current_user.home_address
    )

@statistics_bp.route('/set-home-location', methods=['POST'])
@login_required
def set_home_location():
    """Set user's home location"""
    if request.method == 'POST':
        address = request.form.get('address')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        
        if not address or not lat or not lng:
            flash('Please enter a valid city', 'danger')
            return redirect(url_for('statistics.index'))
        
        # Update user's home location
        current_user.home_address = address
        current_user.home_lat = float(lat)
        current_user.home_lng = float(lng)
        db.session.commit()
        
        flash('Home setting successfully!', 'success')
        return redirect(url_for('statistics.index'))

@statistics_bp.route('/validate-address', methods=['POST'])
@login_required
def validate_address():
    """API endpoint to validate an address using Nominatim"""
    data = request.json
    address = data.get('address')
    
    if not address:
        return jsonify({'success': False, 'message': 'No address provided'})
    
    try:
        # Call Nominatim API
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'q': address,
                'format': 'json',
                'limit': 1
            },
            headers={
                'User-Agent': 'TravelPlannerApp/1.0'
            }
        )
        
        if response.status_code != 200:
            return jsonify({'success': False, 'message': 'Error calling location service'})
            
        results = response.json()
        
        if not results:
            return jsonify({'success': False, 'message': 'Location not found'})
            
        # Return first result
        location = results[0]
        return jsonify({
            'success': True,
            'location': {
                'display_name': location.get('display_name'),
                'lat': float(location.get('lat')),
                'lng': float(location.get('lon'))
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@statistics_bp.route('/ai-recommendations')
@login_required
def get_ai_recommendations():
    """Get AI recommendations based on user's travel history"""
    # This would typically call an AI service
    # For demo purposes, we'll generate some recommendations based on past destinations
    
    travel_stats = calculate_travel_statistics(current_user)
    
    # Simple rule-based recommendations
    recommendations = []
    
    if travel_stats['visited_countries']:
        nearby_countries = get_nearby_countries(travel_stats['visited_countries'])
        if nearby_countries:
            recommendations.append({
                'title': 'Explore nearby countries',
                'description': f"Since you've visited {', '.join(travel_stats['visited_countries'][:2])}, "
                              f"you might enjoy {', '.join(nearby_countries[:3])}.",
                'type': 'destination'
            })
    
    if travel_stats['top_interests']:
        recommendations.append({
            'title': 'Based on your interests',
            'description': f"Your love for {', '.join(travel_stats['top_interests'])} suggests "
                          f"you might enjoy destinations known for these activities.",
            'type': 'interest'
        })
    
    if travel_stats['total_trips'] > 0:
        recommendations.append({
            'title': 'Travel frequency',
            'description': f"You've taken {travel_stats['total_trips']} trips. "
                          f"Consider planning your next adventure soon to maintain your travel rhythm!",
            'type': 'habit'
        })
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })

@statistics_bp.route('/get-destinations')
@login_required
def get_destinations():
    """API endpoint to get destination coordinates for the travel map"""
    try:
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        destinations = []
        
        for plan in travel_plans:
            destination_name = plan.destination
            
            # First try to use the destination coordinates from the travel plan if they exist
            if plan.dest_lat and plan.dest_lng:
                destinations.append({
                    'name': destination_name,
                    'lat': plan.dest_lat,
                    'lng': plan.dest_lng,
                    'plan_id': plan.id,
                    'title': plan.title
                })
            # Fallback to the first itinerary item's coordinates
            elif len(plan.itinerary_items.all()) > 0:
                first_item = plan.itinerary_items.first()
                if first_item and first_item.lat and first_item.lng:
                    destinations.append({
                        'name': destination_name,
                        'lat': first_item.lat,
                        'lng': first_item.lng,
                        'plan_id': plan.id,
                        'title': plan.title
                    })
        
        return jsonify({
            'success': True,
            'destinations': destinations
        })
        
    except Exception as e:
        print(f"Error fetching destinations: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching destination data'
        }), 500

def calculate_travel_statistics(user):
    """Calculate various travel statistics for a user"""
    travel_plans = TravelPlan.query.filter_by(user_id=user.id).all()
    
    stats = {
        'total_trips': len(travel_plans),
        'total_days': 0,
        'total_distance': 0,
        'total_cost': 0,
        'cost_breakdown': {},
        'visited_cities': [],
        'visited_countries': [],
        'cities_this_year': [],
        'top_interests': [],
    }
    
    current_year = datetime.now().year
    all_interests = []
    
    for plan in travel_plans:
        # Calculate days
        days = (plan.end_date - plan.start_date).days + 1
        stats['total_days'] += days
        
        # Extract city and country from destination
        parts = plan.destination.split(',')
        if len(parts) > 0:
            city = parts[0].strip()
            stats['visited_cities'].append(city)
            
            if plan.start_date.year == current_year:
                stats['cities_this_year'].append(city)
            
            if len(parts) > 1:
                country = parts[-1].strip()
                if country not in stats['visited_countries']:
                    stats['visited_countries'].append(country)        # Calculate distance if home location is set
        if user.home_lat and user.home_lng and len(plan.itinerary_items.all()) > 0:
            # Use the first itinerary item's location as the destination coordinates
            first_item = plan.itinerary_items.first()
            if first_item and first_item.lat and first_item.lng:
                distance = haversine_distance(
                    user.home_lat, user.home_lng,
                    first_item.lat, first_item.lng
                )
                stats['total_distance'] += distance
        
        # Calculate total cost from itinerary items
        for item in plan.itinerary_items:
            if item.cost:
                stats['total_cost'] += item.cost
                
                # Categorize costs
                activity_type = item.activity.split(' ')[0] if item.activity else 'Other'
                if activity_type not in stats['cost_breakdown']:
                    stats['cost_breakdown'][activity_type] = 0
                stats['cost_breakdown'][activity_type] += item.cost
                
        # Collect interests
        if plan.interests:
            interests = [i.strip() for i in plan.interests.split(',')]
            all_interests.extend(interests)
    
    # Find most common interests
    if all_interests:
        interest_count = {}
        for interest in all_interests:
            if interest:
                interest_count[interest] = interest_count.get(interest, 0) + 1
                
        # Sort by count and get top 3
        stats['top_interests'] = [i[0] for i in sorted(
            interest_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]]
    
    return stats

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius = 6371  # Radius of earth in kilometers
    
    return radius * c

def get_nearby_countries(visited_countries):
    """Get nearby countries based on visited countries"""
    # Simplified country proximity map
    country_neighbors = {
        'USA': ['Canada', 'Mexico'],
        'Canada': ['USA'],
        'Mexico': ['USA', 'Guatemala', 'Belize'],
        'UK': ['France', 'Ireland', 'Netherlands'],
        'France': ['Spain', 'Italy', 'Germany', 'Switzerland', 'Belgium', 'UK'],
        'Germany': ['France', 'Netherlands', 'Belgium', 'Switzerland', 'Austria', 'Czech Republic'],
        'Japan': ['South Korea', 'Taiwan'],
        'China': ['Japan', 'South Korea', 'Vietnam', 'Thailand', 'India'],
        'Australia': ['New Zealand'],
        'Italy': ['France', 'Switzerland', 'Austria', 'Slovenia', 'Greece'],
        'Spain': ['Portugal', 'France', 'Morocco'],
    }
    
    nearby = []
    for country in visited_countries:
        clean_country = country.strip()
        for c, neighbors in country_neighbors.items():
            if clean_country in c:
                nearby.extend(neighbors)
    
    # Remove duplicates and already visited countries
    return [c for c in list(set(nearby)) if c not in visited_countries]