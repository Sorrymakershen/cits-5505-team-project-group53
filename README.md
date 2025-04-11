### Travel Planning Platform

A smart travel planning tool designed to assist users in creating personalized travel itineraries based on individual preferences, with the added functionality of sharing plans with travel companions.

#### Features
- **Data Upload**: Users can upload their travel preferences, budget, and schedule, and the system will provide personalized recommendations based on this data.
- **Automated Analysis**: The system automatically generates a tailored itinerary and budget allocation.
- **Selective Sharing**: Users can selectively share their travel plans with travel companions or advisors.
- **Map Visualization**: Utilizes Leaflet.js to visually display travel destinations and attractions on a map.
- **Budget Management**: Intelligently allocates and visualizes the travel budget.

#### Technology Stack
- **Backend**: Flask framework
- **Database**: SQLite, managed via SQLAlchemy ORM
- **Frontend**: Bootstrap 5, responsive design
- **Maps**: Leaflet.js
- **Charts**: Chart.js

#### Installation Guide
1. Clone this repository to your local machine.
2. Create and activate a Python virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```
5. Run the application:
   ```
   python run.py
   ```
6. Open your browser and navigate to `http://127.0.0.1:5000`.

#### Project Structure
```
travel_planning_platform/
├── app/                    # Application package
│   ├── models/             # Database models
│   │   ├── user.py         # User model
│   │   └── travel_plan.py  # Travel plan model
│   ├── routes/             # Routes
│   │   ├── main_routes.py  # Main routes
│   │   ├── auth_routes.py  # Authentication routes
│   │   ├── plan_routes.py  # Travel plan routes
│   │   └── share_routes.py # Sharing functionality routes
│   ├── static/             # Static files
│   │   ├── css/            # CSS styles
│   │   ├── js/             # JavaScript scripts
│   │   └── images/         # Image resources
│   ├── templates/          # HTML templates
│   │   ├── auth/           # Authentication templates
│   │   ├── main/           # Homepage and dashboard templates
│   │   ├── plans/          # Travel plan templates
│   │   └── share/          # Sharing functionality templates
│   └── __init__.py         # Application initialization
├── run.py                  # Application entry point
└── requirements.txt        # Project dependencies
```

#### Usage Instructions
1. Register and log in to your account.
2. On the "Create New Plan" page, enter your travel details and preferences.
3. Click "Generate Itinerary and Budget Plan" to receive personalized recommendations.
4. Review and modify the generated itinerary and budget allocation as needed.
5. Use the "Share" feature to share your plan with travel companions.

#### Developers
23935599 XINYU SHEN

© 2025
