# ============================================================
# Satta Takht — Standalone Scraper Script (by Saurav)
# Can be run via Cron Job or manually: python cron_scrape.py
# ============================================================

from app import init_db, scrape_results
import logging

if __name__ == '__main__':
    logging.info("Starting standalone scheduled scrape...")
    init_db()
    scrape_results()
    logging.info("Scrape job completed successfully.")
