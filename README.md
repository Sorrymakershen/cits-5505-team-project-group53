# Travel Planning Platform

An intelligent travel planning tool that assists users in creating personalized travel itineraries based on their preferences and supports sharing with travel companions.

## Features

- **Data Upload**: Users can upload travel preferences, budget, and schedule, and the system will provide personalized recommendations based on this data.
- **Automated Analysis**: The system automatically generates personalized itineraries and budget allocations.
- **Selective Sharing**: Users can selectively share travel plans with companions or travel advisors.
- **Map Visualization**: Utilizes Leaflet.js to visually display travel destinations and attractions on a map.
- **Budget Management**: Intelligently allocates and visualizes travel budgets.

## Technology Stack

- **Backend**: Flask framework
- **Database**: SQLite, managed via SQLAlchemy ORM
- **Frontend**: Bootstrap 5, responsive design
- **Maps**: Leaflet.js
- **Charts**: Chart.js

## Installation Guide

1. Clone this repository to your local machine.
2. Create and activate a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use venv\scripts\activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Initialize the database:

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. Run the application:

```bash
python run.py
```

6. Access the application in your browser at `http://127.0.0.1:5000`.

## Project Structure

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
│   │   ├── auth/           # Authentication-related templates
│   │   ├── main/           # Homepage and dashboard templates
│   │   ├── plans/          # Travel plan templates
│   │   └── share/          # Sharing functionality templates
│   └── __init__.py         # Application initialization
├── run.py                  # Application entry point
└── requirements.txt        # Project dependencies
```

## Usage Instructions

1. Register and log in to your account.
2. Enter your travel information and preferences on the "Create New Plan" page.
3. Click "Generate Itinerary and Budget Plan" to receive personalized recommendations.
4. Review and modify the generated itinerary and budget allocation.
5. Use the "Share" feature to share your plan with travel companions.

## Developer

23935599 Xinyu Shen 

© 2025
