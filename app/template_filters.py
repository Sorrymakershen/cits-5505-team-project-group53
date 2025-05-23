from datetime import datetime, timedelta
import json as python_json  # import standard library json module

def register_filters(app):
    """Register custom template filters for the Flask app."""
    
    @app.template_filter('datetime_format')
    def datetime_format(value, format='%B %d, %Y'):
        """Format a datetime object to a specified format."""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('tojson')
    def convert_to_json(obj):
        """Convert an SQLAlchemy object to a JSON-serializable dict."""
        # use standard library json instead of flask.json
        import decimal
        from app.models.travel_plan import ItineraryItem
        from app.models.memory import Memory
        
        class CustomJSONEncoder(python_json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, decimal.Decimal):
                    return float(obj)
                if isinstance(obj, ItineraryItem):
                    return {
                        'id': obj.id,
                        'day': obj.day,
                        'time': obj.time,
                        'activity': obj.activity,
                        'location': obj.location,
                        'lat': obj.lat,
                        'lng': obj.lng,
                        'cost': float(obj.cost) if obj.cost else 0,
                        'notes': obj.notes
                    }
                if isinstance(obj, Memory):
                    return {
                        'id': obj.id,
                        'title': obj.title,
                        'location': obj.location,
                        'lat': obj.lat,
                        'lng': obj.lng,
                        'visit_date': obj.visit_date.isoformat() if obj.visit_date else None,
                        'description': obj.description,
                        'emotional_rating': obj.emotional_rating,
                        'is_public': obj.is_public
                    }
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                if hasattr(obj, '__dict__'):
                    return {key: value for key, value in obj.__dict__.items() 
                           if not key.startswith('_')}
                return super(CustomJSONEncoder, self).default(obj)
        
        return python_json.dumps(obj, cls=CustomJSONEncoder)
    
    @app.template_filter('from_json')
    def convert_from_json(json_str):
        """Convert a JSON string back to a Python object."""
        if not json_str:
            return None
        return python_json.loads(json_str)
    
    @app.template_filter('date_humanize')
    def date_humanize(date_value):
        """Convert a date to a human-readable format like 'Today', 'Yesterday', etc."""
        if not date_value:
            return ""
        
        today = datetime.now().date()
        
        if isinstance(date_value, datetime):
            date_value = date_value.date()
            
        if date_value == today:
            return "Today"
        elif date_value == today - timedelta(days=1):
            return "Yesterday"
        elif date_value == today + timedelta(days=1):
            return "Tomorrow"
        elif today - timedelta(days=7) <= date_value < today:
            return f"{(today - date_value).days} days ago"
        elif today < date_value <= today + timedelta(days=7):
            return f"In {(date_value - today).days} days"
        else:
            return date_value.strftime("%B %d, %Y")
    
    @app.context_processor
    def utility_processor():
        """Add utility functions to the template context."""
        def day_timedelta(days, base_date=None):
            """
            calculate and return the date after adding days to base_date.
            """
            if base_date is None:
                # return a timedelta object that will be added to the base date in the template
                return timedelta(days=days)
            else:
                # if a base date is provided, return the calculated date
                return base_date + timedelta(days=days)
                
        def is_ajax_request():
            """Check if the current request is an AJAX request."""
            from flask import request
            return request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            
        return dict(
            day_timedelta=day_timedelta,
            is_ajax_request=is_ajax_request
        )
