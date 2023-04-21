from app import create_app
from config import Config

if __name__ == '__main__':
    app = create_app()
    app.run(port=Config.PORT, debug=True, host='0.0.0.0')
