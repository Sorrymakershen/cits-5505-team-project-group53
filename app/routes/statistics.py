from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
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
from sqlalchemy import func, extract
import random

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
    try:
        if request.method == 'POST':
            # Log the form data for debugging
            current_app.logger.info(f"Form data received: {request.form}")
            
            address = request.form.get('address')
            lat = request.form.get('lat')
            lng = request.form.get('lng')
            
            if not address:
                flash('Please enter an address', 'danger')
                return redirect(url_for('statistics.index'))
                
            if not lat or not lng:
                flash('Please validate your address to get coordinates', 'danger')
                return redirect(url_for('statistics.index'))
            
            # Update user's home location
            current_user.home_address = address
            current_user.home_lat = float(lat)
            current_user.home_lng = float(lng)
            db.session.commit()
            
            flash('Home location set successfully!', 'success')
            return redirect(url_for('statistics.index'))
    except Exception as e:
        current_app.logger.error(f"Error setting home location: {str(e)}")
        flash(f'Error saving home location: {str(e)}', 'danger')
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

@statistics_bp.route('/api/statistics/monthly-expenses')
@login_required
def monthly_expenses_data():
    """API endpoint返回用户月度旅行支出数据"""
    try:
        # 获取用户的旅行计划，按月份分组
        current_year = datetime.now().year
        monthly_data = TravelPlan.query.filter(
            TravelPlan.user_id == current_user.id,
            extract('year', TravelPlan.start_date) == current_year
        ).with_entities(
            extract('month', TravelPlan.start_date).label('month'),
            func.sum(TravelPlan.budget).label('total_budget')
        ).group_by('month').order_by('month').all()
        
        # 生成所有月份数据（包括没有旅行的月份）
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        expenses_data = [0] * 12
        
        for item in monthly_data:
            month_idx = int(item.month) - 1  # 月份从1开始，索引从0开始
            expenses_data[month_idx] = float(item.total_budget or 0)
        
        return jsonify({
            'success': True,
            'labels': months,
            'data': expenses_data
        })
    
    except Exception as e:
        current_app.logger.error(f'获取月度支出数据时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error fetching monthly expenses data'
        }), 500

@statistics_bp.route('/api/statistics/duration-distribution')
@login_required
def duration_distribution_data():
    """API endpoint返回用户旅行时长分布数据"""
    try:
        # 获取用户的所有旅行计划
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        
        # 定义时长类别
        duration_categories = {
            'Short (1-3 days)': 0,
            'Medium (4-7 days)': 0,
            'Long (8-14 days)': 0,
            'Extended (15-30 days)': 0,
            'Long-term (30+ days)': 0
        }
        
        # 计算每个旅行的持续时间并归类
        for plan in travel_plans:
            if plan.start_date and plan.end_date:
                duration = (plan.end_date - plan.start_date).days + 1
                
                if duration <= 3:
                    duration_categories['Short (1-3 days)'] += 1
                elif duration <= 7:
                    duration_categories['Medium (4-7 days)'] += 1
                elif duration <= 14:
                    duration_categories['Long (8-14 days)'] += 1
                elif duration <= 30:
                    duration_categories['Extended (15-30 days)'] += 1
                else:
                    duration_categories['Long-term (30+ days)'] += 1
        
        # 过滤掉计数为0的类别
        filtered_categories = {k: v for k, v in duration_categories.items() if v > 0}
        
        # 如果没有数据，返回默认类别
        if not filtered_categories:
            return jsonify({
                'success': True,
                'labels': [],
                'data': []
            })
        
        return jsonify({
            'success': True,
            'labels': list(filtered_categories.keys()),
            'data': list(filtered_categories.values())
        })
    
    except Exception as e:
        current_app.logger.error(f'获取旅行时长分布数据时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error fetching duration distribution data'
        }), 500

@statistics_bp.route('/api/statistics/destination-frequency')
@login_required
def destination_frequency_data():
    """API endpoint返回用户目的地频率数据"""
    try:
        # 获取用户旅行的目的地频率
        destinations = TravelPlan.query.filter_by(user_id=current_user.id).with_entities(
            TravelPlan.destination,
            func.count(TravelPlan.id).label('count')
        ).group_by(TravelPlan.destination).order_by(func.count(TravelPlan.id).desc()).limit(10).all()
        
        if not destinations:
            return jsonify({
                'success': True,
                'labels': [],
                'data': [],
                'colors': []
            })
        
        # 准备数据
        labels = [d.destination for d in destinations]
        data = [d.count for d in destinations]
        
        # 生成随机颜色
        colors = []
        for _ in range(len(destinations)):
            r = random.randint(50, 200)
            g = random.randint(50, 200)
            b = random.randint(50, 200)
            colors.append(f'rgba({r}, {g}, {b}, 0.7)')
        
        return jsonify({
            'success': True,
            'labels': labels,
            'data': data,
            'colors': colors
        })
    
    except Exception as e:
        current_app.logger.error(f'获取目的地频率数据时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error fetching destination frequency data'
        }), 500

@statistics_bp.route('/api/statistics/expense-chart')
@login_required
def expense_chart_data():
    """API endpoint返回用户旅行支出对比数据"""
    try:
        # 获取用户的所有旅行计划，按年份分组
        yearly_data = TravelPlan.query.filter_by(user_id=current_user.id).with_entities(
            extract('year', TravelPlan.start_date).label('year'),
            func.sum(TravelPlan.budget).label('total_budget')
        ).group_by('year').order_by('year').all()
        
        # 准备数据
        years = [int(item.year) for item in yearly_data]
        expenses = [float(item.total_budget) for item in yearly_data]
        
        # 计算每次旅行的平均支出
        avg_expenses = []
        for year in years:
            trips_count = TravelPlan.query.filter(
                TravelPlan.user_id == current_user.id,
                extract('year', TravelPlan.start_date) == year
            ).count()
            
            if trips_count > 0:
                yearly_expense = next((e for y, e in zip(years, expenses) if y == year), 0)
                avg_expenses.append(round(yearly_expense / trips_count, 2))
            else:
                avg_expenses.append(0)
        
        return jsonify({
            'success': True,
            'years': years,
            'expenses': expenses,
            'avg_expenses': avg_expenses
        })
    
    except Exception as e:
        current_app.logger.error(f'获取支出图表数据时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error fetching expense chart data'
        }), 500

@statistics_bp.route('/api/statistics/destination-comparison')
@login_required
def destination_comparison_data():
    """API endpoint返回用户目的地对比数据"""
    try:
        # 获取用户去过的所有目的地
        destinations_data = TravelPlan.query.filter_by(user_id=current_user.id).with_entities(
            TravelPlan.destination,
            func.count(TravelPlan.id).label('visits'),
            func.avg(TravelPlan.budget).label('avg_budget')
        ).group_by(TravelPlan.destination).all()
        
        if not destinations_data:
            return jsonify({
                'success': True,
                'destinations': []
            })
        
        # 计算每个目的地的数据
        destination_stats = []
        for dest in destinations_data:
            # 计算该目的地的平均停留天数
            trips = TravelPlan.query.filter_by(
                user_id=current_user.id,
                destination=dest.destination
            ).all()
            
            total_days = 0
            valid_trips = 0
            for trip in trips:
                if trip.start_date and trip.end_date:
                    duration = (trip.end_date - trip.start_date).days + 1
                    total_days += duration
                    valid_trips += 1
            
            avg_duration = total_days / valid_trips if valid_trips > 0 else 0
            
            # 计算每日平均花费
            daily_cost = dest.avg_budget / avg_duration if avg_duration > 0 else 0
            
            # 模拟距离数据（实际应用中可以使用地理编码API获取真实距离）
            distance = random.uniform(500, 10000)  # 假设距离为500-10000公里
            
            destination_stats.append({
                'name': dest.destination,
                'visits': dest.visits,
                'cost': daily_cost,
                'duration': avg_duration,
                'distance': distance
            })
        
        return jsonify({
            'success': True,
            'destinations': destination_stats
        })
    
    except Exception as e:
        current_app.logger.error(f'获取目的地对比数据时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error fetching destination comparison data'
        }), 500

@statistics_bp.route('/api/statistics/travel-timeline')
@login_required
def travel_timeline_data():
    """API endpoint返回用户旅行时间轴数据"""
    try:
        # 获取用户的旅行计划，按开始日期排序
        travel_plans = TravelPlan.query.filter_by(
            user_id=current_user.id
        ).order_by(TravelPlan.start_date.desc()).all()
        
        if not travel_plans:
            return jsonify({
                'success': True,
                'trips': []
            })
        
        # 准备时间轴数据
        timeline_data = []
        for plan in travel_plans:
            # 检查日期是否有效
            if not plan.start_date or not plan.end_date:
                continue
                
            # 格式化日期为ISO格式，以便前端解析
            timeline_data.append({
                'id': plan.id,
                'title': plan.title,
                'destination': plan.destination,
                'start_date': plan.start_date.isoformat(),
                'end_date': plan.end_date.isoformat(),
                'budget': float(plan.budget) if plan.budget else None,
                'description': plan.description
            })
        
        return jsonify({
            'success': True,
            'trips': timeline_data
        })
    
    except Exception as e:
        current_app.logger.error(f'获取旅行时间轴数据时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error fetching travel timeline data'
        }), 500

@statistics_bp.route('/api/expenses/by-trip')
@login_required
def expenses_by_trip():
    """API endpoint返回按旅行行程分类的费用数据"""
    try:
        # 获取用户的所有旅行计划
        travel_plans = TravelPlan.query.filter_by(user_id=current_user.id).all()
        
        # 准备数据结构
        trips_data = []
        aggregated_data = {
            'categories': [],
            'values': []
        }
        
        # 分类总计
        all_categories = {}
        
        for plan in travel_plans:
            # 每个行程的数据
            trip_data = {
                'id': plan.id,
                'title': plan.title,
                'expenses': {
                    'categories': [],
                    'values': []
                }
            }
            
            # 处理该行程的所有支出项目
            categories_dict = {}
            
            for item in plan.itinerary_items:
                if item.cost and item.cost > 0:
                    # 使用活动类型作为分类
                    category = item.activity.split(' ')[0] if item.activity else 'Other'
                    
                    # 累加到该行程的分类中
                    if category not in categories_dict:
                        categories_dict[category] = item.cost
                    else:
                        categories_dict[category] += item.cost
                    
                    # 同时累加到总体分类中
                    if category not in all_categories:
                        all_categories[category] = item.cost
                    else:
                        all_categories[category] += item.cost
            
            # 将字典转换为两个列表
            for category, value in categories_dict.items():
                trip_data['expenses']['categories'].append(category)
                trip_data['expenses']['values'].append(value)
            
            trips_data.append(trip_data)
        
        # 将总体分类数据转换为两个列表
        for category, value in all_categories.items():
            aggregated_data['categories'].append(category)
            aggregated_data['values'].append(value)
        
        # 返回每个行程的数据和汇总数据
        return jsonify({
            'success': True,
            'trips': trips_data,
            'aggregated': aggregated_data
        })
        
    except Exception as e:
        current_app.logger.error(f'获取按旅行分类的费用数据时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': 'Error fetching expense data by trip'
        }), 500