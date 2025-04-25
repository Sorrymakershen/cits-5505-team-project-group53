from app import app, create_app

# ensure the app is created
application = create_app()

if __name__ == '__main__':
    # set host and port for the application
    application.run(debug=True, host='127.0.0.1', port=5000)
