# ============================================================
# Satta Takht — Production WSGI Entrypoint (by Saurav)
# ============================================================

from app import app, init_db, scraper_loop
import threading

# Initialize database on server start
init_db()

# Start background scraper loop
scraper_thread = threading.Thread(target=scraper_loop, daemon=True)
scraper_thread.start()

if __name__ == "__main__":
    app.run()
