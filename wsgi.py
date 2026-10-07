import os
import sys

# Ensure backend folder is on python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from wsgi import app

if __name__ == "__main__":
    app.run()
