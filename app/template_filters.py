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
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                if hasattr(obj, '__dict__'):
                    return {key: value for key, value in obj.__dict__.items() 
                           if not key.startswith('_')}
                return super(CustomJSONEncoder, self).default(obj)
        
        return python_json.dumps(obj, cls=CustomJSONEncoder)
    
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
            
        return dict(day_timedelta=day_timedelta)
