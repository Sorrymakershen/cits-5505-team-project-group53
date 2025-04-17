from app import app, create_app

# 确保应用程序是完全配置的
application = create_app()

if __name__ == '__main__':
    application.run(debug=True)
