
=======
### Travel Planning Platform

A smart travel planning tool designed to assist users in creating personalised travel itineraries based on individual preferences, with the added functionality of sharing plans with travel companions.

#### Features
- **User Registration & Login**  
  Secure authentication and user management.
- **Travel Plan Management**  
  Create, edit, and delete travel plans with multiple destinations and detailed itineraries.
- **Memories Storage**  
  Upload travel photos and record memories, sorted by date.
- **Dashboard**  
  Overview of upcoming trips, recent memories, and unique destinations.
- **Interactive Maps**  
  Visualise travel plans and visited places using Leaflet.js.
- **Statistics & Charts**  
  Analyse travel history and trends with Chart.js.
- **Privacy & Terms Pages**  
  Inform users about the policy and terms of service.

#### Technology Stack
- **Backend**: [Flask](https://flask.palletsprojects.com/)  
  Python web framework for routing, authentication, and business logic.
- **Database**: [SQLite](https://www.sqlite.org/) + [SQLAlchemy ORM](https://www.sqlalchemy.org/)  
  SQLAlchemy ORM for database modelling and queries.
- **Frontend**: [Bootstrap 5](https://getbootstrap.com/)  
  Responsive design for all devices.
- **Maps**: [Leaflet.js](https://leafletjs.com/)  
  Interactive maps for displaying destinations and routes.
- **Charts**: [Chart.js](https://www.chartjs.org/)  
  Visualise travel statistics and trends.
- **Authentication**: [Flask-Login](https://flask-login.readthedocs.io/)  
  User registration, login, and session management.

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
4. Initialise the database:
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
travel-planning-platform/
├── app/                       # Application package
│   ├── __init__.py            # Application factory
│   ├── config.py              # Configuration settings
│   ├── extensions.py          # Flask extensions (db, login, etc.)
│   ├── models/                # Database models
│   │   ├── __init__.py        # Models initialization
│   │   ├── user.py            # User account model
│   │   ├── travel_plan.py     # Travel plans model
│   │   └── memory.py          # Travel memories model
│   ├── routes/                # Route blueprints
│   │   ├── __init__.py        # Routes initialization
│   │   ├── main.py            # Main routes (home, dashboard)
│   │   ├── auth.py            # Authentication routes
│   │   ├── travel_plans.py    # Travel plan management routes
│   │   └── memories.py        # Travel memories routes
│   ├── static/                # Static files
│   │   ├── css/               # Stylesheets
│   │   │   └── style.css      # Main stylesheet
│   │   ├── js/                # JavaScript files
│   │   │   └── main.js        # Main JavaScript file
│   │   ├── images/            # Image assets
│   │   └── favicon.ico        # Site favicon
│   ├── templates/             # HTML templates
│   │   ├── base.html          # Base template with common elements
│   │   ├── index.html         # Landing page
│   │   ├── dashboard.html     # User dashboard
│   │   ├── about.html         # About page
│   │   ├── privacy.html       # Privacy policy
│   │   ├── terms.html         # Terms of service
│   │   ├── auth/              # Authentication templates
│   │   │   ├── login.html     # Login page
│   │   │   ├── register.html  # Registration page
│   │   │   └── profile.html   # User profile page
│   │   ├── travel_plans/      # Travel plan templates
│   │   │   ├── create.html    # Create new plan
│   │   │   ├── edit.html      # Edit existing plan
│   │   │   ├── view.html      # View plan details
│   │   │   └── list.html      # List all plans
│   │   └── memories/          # Memory templates
│   │       ├── create.html    # Create new memory
│   │       ├── edit.html      # Edit existing memory
│   │       ├── view.html      # View memory details
│   │       └── list.html      # List all memories
│   └── utils/                 # Utility functions
│       ├── __init__.py
│       ├── email.py           # Email sending functionality
│       └── helpers.py         # Misc helper functions
├── migrations/                # Database migrations (Alembic)
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Test configuration
│   ├── test_models.py         # Model tests
│   ├── test_routes.py         # Route tests
│   └── test_utils.py          # Utility function tests
├── .env                       # Environment variables (git-ignored)
├── .env.example               # Example environment variables
├── .gitignore                 # Git ignore file
├── requirements.txt           # Project dependencies
├── run.py                     # Application entry point
└── README.md                  # Project documentation
```

##### Travel Planning Platform

## Overview
This travel planning platform helps users organise their trips and store their travel memories. 
The application allows users to create detailed travel plans with destinations, dates, and activities, as well as preserve memories from their journeys.

#### Usage Instructions

1. **Getting Started**
   - Register for a new account or log in if you already have one
   - Once logged in, you'll be directed to your personal dashboard

2. **Dashboard**
   - View your upcoming trips (limited to 6 most recent)
   - Browse your recent travel memories (limited to 6 most recent)
   - See statistics about your travels, including total unique destinations

3. **Planning a Trip**
   - Navigate to the "Travel Plans" section
   - Click "Create New Plan" to start planning a new trip
   - Fill in details like destination, dates, accommodation, and activities
   - Save your plan to access it later

4. **Recording Memories**
   - After your trip, go to the "Memories" section
   - Click "Create New Memory" to document your experiences
   - Upload photos and write descriptions about your travel highlights
   - Tag your memories with locations and categories

5. **Managing Your Content**
   - Edit or delete your travel plans as needed
   - Update your memories with new photos or information
   - Share selected content with friends or family (if sharing feature enabled)

6. **Account Settings**
   - Access your profile to update personal information
   - Manage privacy settings and notification preferences
   - Update your password or email address as needed

Visit the About, Privacy Policy, and Terms of Service pages for more information about the platform.
#### Developers
23935599 XINYU SHEN Sorrymakershen


© 2025

