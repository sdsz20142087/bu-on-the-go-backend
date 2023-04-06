from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(port=8080, debug=True,host='0.0.0.0')