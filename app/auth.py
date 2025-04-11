from app import login_manager
from app.models.user import User

@login_manager.user_loader
def load_user(user_id):
    """
    This function is used by Flask-Login to load a user from the database 
    based on the user_id stored in the session.
    """
    return User.query.get(int(user_id))
