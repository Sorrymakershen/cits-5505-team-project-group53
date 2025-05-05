from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db, csrf
from app.models.travel_plan import TravelPlan
from app.models.user import User
from datetime import datetime
import requests
import json
from math import radians, sin, cos, sqrt, atan2
from collections import defaultdict
from itertools import groupby
from operator import itemgetter

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
@csrf.exempt  # 禁用此路由的 CSRF 保护
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
@csrf.exempt  # 禁用此路由的 CSRF 保护
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

@statistics_bp.route('/get-monthly-expenses')
@login_required
def get_monthly_expenses():
    """API endpoint to get monthly expense data for bar chart"""
    try:
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        
        # Initialize data structure for monthly expenses
        monthly_expenses = defaultdict(float)
        
        for plan in travel_plans:
            # Calculate total cost for this plan from itinerary items
            for item in plan.itinerary_items:
                if item.cost:
                    # Get the month of the activity (if time is set) or plan start date
                    if hasattr(item, 'day') and item.day and plan.start_date:
                        # Calculate the actual date by adding days
                        from datetime import timedelta
                        day_offset = max(0, item.day - 1)  # day is 1-based
                        actual_date = plan.start_date + timedelta(days=day_offset)
                        month_key = actual_date.strftime('%Y-%m')
                    else:
                        # Fallback to plan start date
                        month_key = plan.start_date.strftime('%Y-%m')
                    
                    monthly_expenses[month_key] += item.cost
        
        # Convert to sorted list of (month, amount) tuples
        sorted_expenses = sorted(monthly_expenses.items())
        
        # Format for chart display
        months = [f"{m.split('-')[0][-2:]}-{m.split('-')[1]}" for m, _ in sorted_expenses]  # Format: YY-MM
        amounts = [amount for _, amount in sorted_expenses]
        
        return jsonify({
            'success': True,
            'labels': months,
            'data': amounts
        })
    
    except Exception as e:
        print(f"Error fetching monthly expenses: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching expense data'
        }), 500

@statistics_bp.route('/get-duration-distribution')
@login_required
def get_duration_distribution():
    """API endpoint to get trip duration distribution data"""
    try:
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        
        # Calculate duration for each trip
        durations = []
        for plan in travel_plans:
            if plan.start_date and plan.end_date:
                days = (plan.end_date - plan.start_date).days + 1
                durations.append(days)
        
        # Group durations into buckets
        buckets = {
            '1-3 days': 0,
            '4-7 days': 0,
            '1-2 weeks': 0,
            '2-4 weeks': 0,
            '1+ month': 0
        }
        
        for duration in durations:
            if duration <= 3:
                buckets['1-3 days'] += 1
            elif duration <= 7:
                buckets['4-7 days'] += 1
            elif duration <= 14:
                buckets['1-2 weeks'] += 1
            elif duration <= 28:
                buckets['2-4 weeks'] += 1
            else:
                buckets['1+ month'] += 1
        
        # Convert to format needed for charts
        labels = list(buckets.keys())
        data = list(buckets.values())
        
        return jsonify({
            'success': True,
            'labels': labels,
            'data': data
        })
    
    except Exception as e:
        print(f"Error fetching duration distribution: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching duration data'
        }), 500

@statistics_bp.route('/get-destination-frequency')
@login_required
def get_destination_frequency():
    """API endpoint to get destination visit frequency data"""
    try:
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        
        # Count visits to each destination
        destination_counts = defaultdict(int)
        
        for plan in travel_plans:
            destination = plan.destination.split(',')[0].strip()  # Use first part (city) of destination
            destination_counts[destination] += 1
        
        # Sort by frequency and take top 10
        sorted_destinations = sorted(destination_counts.items(), key=itemgetter(1), reverse=True)[:10]
        
        # Convert to format needed for charts
        labels = [dest for dest, _ in sorted_destinations]
        data = [count for _, count in sorted_destinations]
        
        # Generate colors for each bar
        colors = [
            'rgba(54, 162, 235, 0.7)',   # Blue
            'rgba(255, 99, 132, 0.7)',   # Red
            'rgba(255, 206, 86, 0.7)',   # Yellow
            'rgba(75, 192, 192, 0.7)',   # Green
            'rgba(153, 102, 255, 0.7)',  # Purple
            'rgba(255, 159, 64, 0.7)',   # Orange
            'rgba(201, 203, 207, 0.7)',  # Grey
            'rgba(54, 162, 235, 0.5)',   # Light Blue
            'rgba(255, 99, 132, 0.5)',   # Light Red
            'rgba(255, 206, 86, 0.5)'    # Light Yellow
        ]
        
        return jsonify({
            'success': True,
            'labels': labels,
            'data': data,
            'colors': colors[:len(labels)]
        })
    
    except Exception as e:
        print(f"Error fetching destination frequency: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching destination data'
        }), 500

@statistics_bp.route('/get-travel-timeline')
@login_required
def get_travel_timeline():
    """API endpoint to get travel timeline data"""
    try:
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        
        # Format trips for timeline visualization
        trips = []
        for plan in travel_plans:
            if plan.start_date and plan.end_date:
                trip = {
                    'title': plan.title,
                    'destination': plan.destination,
                    'start_date': plan.start_date.strftime('%Y-%m-%d'),
                    'end_date': plan.end_date.strftime('%Y-%m-%d'),
                    'budget': plan.budget,
                    'description': plan.interests
                }
                trips.append(trip)
        
        return jsonify({
            'success': True,
            'trips': trips
        })
    
    except Exception as e:
        print(f"Error fetching travel timeline: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching timeline data'
        }), 500

@statistics_bp.route('/get-destination-comparison')
@login_required
def get_destination_comparison():
    """API endpoint to get destination comparison data"""
    try:
        # Get destinations with enough data for comparison
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        
        # Group plans by destination (city)
        destination_plans = defaultdict(list)
        for plan in travel_plans:
            destination = plan.destination.split(',')[0].strip()
            destination_plans[destination].append(plan)
        
        # Process destinations with at least one plan
        destinations = []
        for name, plans in destination_plans.items():
            if plans:
                # Average daily cost
                total_cost = 0
                total_days = 0
                
                for plan in plans:
                    days = (plan.end_date - plan.start_date).days + 1
                    total_days += days
                    
                    # Sum costs from itinerary items
                    plan_cost = 0
                    for item in plan.itinerary_items:
                        if item.cost:
                            plan_cost += item.cost
                    
                    total_cost += plan_cost
                
                avg_daily_cost = total_cost / max(1, total_days)
                
                # Distance from home if available
                distance = 0
                if current_user.home_lat and current_user.home_lng:
                    # Use coordinates from first plan's destination or itinerary
                    first_plan = plans[0]
                    lat, lng = None, None
                    
                    if first_plan.dest_lat and first_plan.dest_lng:
                        lat, lng = first_plan.dest_lat, first_plan.dest_lng
                    elif len(first_plan.itinerary_items.all()) > 0:
                        first_item = first_plan.itinerary_items.first()
                        if first_item and first_item.lat and first_item.lng:
                            lat, lng = first_item.lat, first_item.lng
                    
                    if lat and lng:
                        distance = haversine_distance(
                            current_user.home_lat, current_user.home_lng,
                            lat, lng
                        )
                
                # Average duration
                avg_duration = total_days / len(plans)
                
                # Add to destinations list
                destinations.append({
                    'name': name,
                    'cost': avg_daily_cost,
                    'duration': avg_duration,
                    'distance': distance,
                    'rating': 4.5,  # Would come from user ratings in a real system
                    'visits': len(plans)
                })
        
        return jsonify({
            'success': True,
            'destinations': destinations
        })
    
    except Exception as e:
        print(f"Error fetching destination comparison: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching comparison data'
        }), 500

@statistics_bp.route('/get-trend-analysis')
@login_required
def get_trend_analysis():
    """API endpoint to get travel trend analysis data"""
    try:
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        
        # Group by year and month
        trips_by_year_month = defaultdict(int)
        costs_by_year_month = defaultdict(float)
        
        for plan in travel_plans:
            if plan.start_date:
                year_month = plan.start_date.strftime('%Y-%m')
                trips_by_year_month[year_month] += 1
                
                # Sum costs
                plan_cost = 0
                for item in plan.itinerary_items:
                    if item.cost:
                        plan_cost += item.cost
                
                costs_by_year_month[year_month] += plan_cost
        
        # Sort chronologically
        sorted_months = sorted(list(set(trips_by_year_month.keys()) | set(costs_by_year_month.keys())))
        
        # Format for the chart
        labels = [f"{m[-2:]}/{m[:4]}" for m in sorted_months]  # Format: MM/YYYY
        
        time_series = {
            'Trips': [trips_by_year_month.get(month, 0) for month in sorted_months],
            'Expenses ($)': [costs_by_year_month.get(month, 0) for month in sorted_months]
        }
        
        # Generate insights based on the data
        insights = []
        
        # Check for spending trends
        if len(sorted_months) >= 3:
            recent_costs = [costs_by_year_month.get(month, 0) for month in sorted_months[-3:]]
            avg_recent_cost = sum(recent_costs) / 3
            avg_overall_cost = sum(costs_by_year_month.values()) / len(costs_by_year_month)
            
            if avg_recent_cost > avg_overall_cost * 1.2:
                insights.append("Your travel spending has increased by more than 20% in recent months.")
            elif avg_recent_cost < avg_overall_cost * 0.8:
                insights.append("You've been spending less on travel recently compared to your historical average.")
        
        # Check for travel frequency patterns
        if len(sorted_months) >= 6:
            trips_last_6_months = sum(trips_by_year_month.get(month, 0) for month in sorted_months[-6:])
            if trips_last_6_months == 0:
                insights.append("You haven't traveled in the last 6 months. Perhaps it's time to plan your next adventure!")
            elif trips_last_6_months >= 3:
                insights.append(f"You're an active traveler with {trips_last_6_months} trips in the last 6 months!")
        
        return jsonify({
            'success': True,
            'labels': labels,
            'timeSeries': time_series,
            'insights': insights
        })
    
    except Exception as e:
        print(f"Error fetching trend analysis: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error fetching trend data'
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