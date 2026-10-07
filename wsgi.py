import os
import sys
import threading

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import app as backend_module

app = backend_module.app

# Initialize database
backend_module.init_db()

# Start background scraper
scraper_thread = threading.Thread(target=backend_module.scraper_loop, daemon=True)
scraper_thread.start()

if __name__ == "__main__":
    app.run()
