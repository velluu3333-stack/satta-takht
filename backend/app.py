# ============================================================
# Satta Takht — Flask Backend (by Saurav)
# Auto scraper + Dynamic City Manager + 4 Khaiwal Boards + Admin Panel + REST API
# ============================================================

from flask import Flask, jsonify, request, render_template, redirect, url_for, session, send_from_directory
from flask_cors import CORS
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import date, datetime
import threading
import time
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Frontend static folder path (detect whether in parent or local folder)
_candidate_frontend_1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
_candidate_frontend_2 = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend'))
FRONTEND_DIR = _candidate_frontend_1 if os.path.isdir(_candidate_frontend_1) else _candidate_frontend_2

app = Flask(__name__, static_folder=None)
app.secret_key = 'satta-takht-saurav-secret-2024'
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'results.db')

# ---- Admin credentials ----
ADMIN_USER = 'saurav'
ADMIN_PASS = 'takht@2024'

SCRAPE_SOURCE = 'https://satta-king-fast.com/'

# ============================================================
# DATABASE SETUP
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Results table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_date TEXT NOT NULL,
            city_key TEXT NOT NULL,
            result_number TEXT DEFAULT '',
            updated_at TEXT,
            UNIQUE(result_date, city_key)
        )
    ''')
    # Dynamic cities table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city_key TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            scrape_id TEXT NOT NULL,
            result_time TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 99,
            created_at TEXT
        )
    ''')
    # 4 Khaiwal Boards table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS khaiwals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            tagline TEXT DEFAULT '',
            timings TEXT DEFAULT '',
            rate_jodi TEXT DEFAULT '',
            rate_haruf TEXT DEFAULT '',
            whatsapp TEXT DEFAULT '',
            calling TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            badge TEXT DEFAULT '',
            telegram TEXT DEFAULT '',
            board_theme TEXT DEFAULT 'theme-blue'
        )
    ''')
    # Auto migrate if existing columns are missing
    try:
        conn.execute("ALTER TABLE khaiwals ADD COLUMN telegram TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE khaiwals ADD COLUMN board_theme TEXT DEFAULT 'theme-blue'")
    except Exception:
        pass

    # Site settings (Chatbot, Support, Themes, Leak Jodi)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS site_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    default_settings_list = [
        ('telegram_link', 'https://t.me/'),
        ('whatsapp_number', '919999999999'),
        ('chatbot_telegram', 'https://t.me/'),
        ('chatbot_whatsapp', '919999999999'),
        ('support_telegram', 'https://t.me/'),
        ('support_whatsapp', '919999999999'),
        ('app_download_link', ''),
        ('site_theme', 'theme-classic-dark'),
        ('leak_jodi_active', '1'),
        ('leak_jodi_title', '👑 VIP LEAK JODI & SINGLE HARUF BLAST 👑'),
        ('leak_jodi_tagline', '100% सॉलिड लीक गेम • सिंगल जोड़ी फिक्स • 100% लॉस कवर गारंटी'),
        ('leak_jodi_games', 'गली | दिसावर | फरीदाबाद | गाजियाबाद | दिल्ली बाजार'),
        ('leak_jodi_whatsapp', '919999999999'),
        ('leak_jodi_telegram', 'https://t.me/'),
        ('leak_jodi_note', 'खाईवाल का परचा लगवाने या सिंगल लीक गेम पाने के लिए तुरंत मैसेज करें')
    ]
    for k, v in default_settings_list:
        conn.execute("INSERT OR IGNORE INTO site_settings (key, value) VALUES (?, ?)", (k, v))

    # Seed Default Cities (Comprehensive list from satta-king-fast.com)
    existing_cities = conn.execute('SELECT COUNT(*) as c FROM cities').fetchone()['c']
    if existing_cities == 0:
        defaults = [
            ('desawar',        'DESAWAR',         'DS', '05:00 AM', 1, 1),
            ('delhi_bazar',    'DELHI BAZAR',     'DB', '03:00 PM', 1, 2),
            ('shree_ganesh',   'SHREE GANESH',    'SG', '04:30 PM', 1, 3),
            ('faridabad',      'FARIDABAD',       'FB', '06:00 PM', 1, 4),
            ('ghaziabad',      'GHAZIABAD',       'GB', '09:55 PM', 1, 5),
            ('gali',           'GALI',            'GL', '11:25 PM', 1, 6),
            ('up_king',        'U.P KING',        'UI', '02:00 PM', 1, 7),
            ('new_punjab',     'NEW PUNJAB',      'NP', '11:10 AM', 1, 8),
            ('royal_bazar',    'ROYAL BAZAR',     'RO', '01:15 PM', 1, 9),
            ('super_king',     'SUPER KING',      'SU', '01:45 PM', 1, 10),
            ('mumbai_bazaar',  'MUMBAI BAZAAR',   'MU', '02:00 PM', 1, 11),
            ('kalka_bazar',    'KALKA BAZAR',     'KB', '02:30 PM', 1, 12),
            ('delhi_city',     'DELHI CITY',      'DC', '02:30 PM', 1, 13),
            ('taj',            'TAJ',             'TJ', '03:15 PM', 1, 14),
        ]
        conn.executemany('''
            INSERT OR IGNORE INTO cities
            (city_key, display_name, scrape_id, result_time, is_active, sort_order, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [(k, d, s, t, a, o, datetime.now().isoformat()) for k, d, s, t, a, o in defaults])

    # Seed Default 4 Khaiwal Boards
    existing_khaiwals = conn.execute('SELECT COUNT(*) as c FROM khaiwals').fetchone()['c']
    if existing_khaiwals == 0:
        khaiwals_default = [
            (1, '👑 महाकाल भाई खाईवाल', 'ईमानदार खाईवाल • 100% पेमेंट की गारंटी', 
             'दिल्ली बाजार 03:00 PM | श्री गणेश 04:30 PM | फरीदाबाद 06:00 PM | गाजियाबाद 09:30 PM | गली 11:25 PM | दिसावर 05:00 AM',
             '10 के 950 (100 के 9500)', '100 के 950 (1000 के 9500)', '919999999999', '919999999999', 1, '🔥 NO. 1 TRUSTED'),
            
            (2, '⚡ राजा भाई ऑनलाइन खाईवाल', 'फास्ट सर्विस • 5 मिनट में तुरंत निकासी', 
             'दिल्ली बाजार 02:50 PM | श्री गणेश 04:20 PM | फरीदाबाद 05:55 PM | गाजियाबाद 09:25 PM | गली 11:20 PM | दिसावर 04:50 AM',
             '10 के 950', '100 के 950', '919888888888', '919888888888', 1, '⚡ SUPERFAST PAY'),

            (3, '💎 बादशाह भाई खाईवाल', 'सबसे पुराना और भरोसेमंद नाम', 
             'सभी बड़े और छोटे गेम उपलब्ध | 24x7 बुकिंग चालू',
             '10 के 950', '100 के 950', '919777777777', '919777777777', 1, '💎 ROYAL GUARANTEE'),

            (4, '🎯 सिकंदर खाईवाल दरबार', 'हाथों-हाथ पेमेंट • नो फ्रॉड', 
             'फरीदाबाद | गाजियाबाद | गली | दिसावर स्पेशलिस्ट',
             '10 के 950', '100 के 950', '919666666666', '919666666666', 1, '🎯 TOP RATED')
        ]
        conn.executemany('''
            INSERT OR REPLACE INTO khaiwals
            (id, name, tagline, timings, rate_jodi, rate_haruf, whatsapp, calling, is_active, badge)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', khaiwals_default)

    conn.commit()
    conn.close()
    logging.info("Database initialized successfully.")

def get_active_cities():
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM cities WHERE is_active=1 ORDER BY sort_order, id'
    ).fetchall()
    conn.close()
    return rows

def get_all_cities():
    conn = get_db()
    rows = conn.execute('SELECT * FROM cities ORDER BY sort_order, id').fetchall()
    conn.close()
    return rows

def get_active_khaiwals():
    conn = get_db()
    rows = conn.execute('SELECT * FROM khaiwals WHERE is_active=1 ORDER BY id').fetchall()
    conn.close()
    return rows

def get_all_khaiwals():
    conn = get_db()
    rows = conn.execute('SELECT * FROM khaiwals ORDER BY id').fetchall()
    conn.close()
    return rows

# ============================================================
# SCRAPER
# ============================================================

def scrape_results():
    logging.info("Starting scrape from satta-king-fast.com ...")
    today = date.today().strftime('%d-%m-%Y')
    cities = get_active_cities()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/120.0.0.0 Safari/537.36'
        }
        resp = requests.get(SCRAPE_SOURCE, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        conn = get_db()

        for city in cities:
            city_key   = city['city_key']
            scrape_id  = city['scrape_id']
            try:
                row_el = soup.find('tr', id=scrape_id)
                if not row_el:
                    continue
                today_td = row_el.find('td', class_='today-number')
                if not today_td:
                    continue
                h3 = today_td.find('h3')
                number = h3.get_text(strip=True) if h3 else ''
                if number.upper() in ('XX', '', '-'):
                    continue
                conn.execute('''
                    INSERT INTO results (result_date, city_key, result_number, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(result_date, city_key) DO UPDATE SET
                        result_number = excluded.result_number,
                        updated_at = excluded.updated_at
                ''', (today, city_key, number, datetime.now().isoformat()))
                logging.info(f"  {city_key}: {number} ✓")
            except Exception as e:
                logging.error(f"  Error {city_key}: {e}")

        conn.commit()
        conn.close()
        logging.info("Scrape complete.")
    except Exception as e:
        logging.error(f"Scrape failed: {e}")

def scraper_loop():
    while True:
        scrape_results()
        time.sleep(5 * 60)

@app.route('/api/cron/scrape', methods=['GET', 'POST'])
def api_cron_scrape():
    """Triggered by scheduled cron jobs or webhooks."""
    token = request.args.get('token', '') or request.form.get('token', '')
    if token != 'takht@2024':
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 403
    threading.Thread(target=scrape_results, daemon=True).start()
    return jsonify({'status': 'ok', 'message': 'Scraping triggered', 'time': datetime.now().isoformat()})

# ============================================================
# PUBLIC API
# ============================================================

@app.route('/api/cities', methods=['GET'])
def api_cities():
    """Returns active cities list for frontend."""
    cities = get_active_cities()
    return jsonify([dict(c) for c in cities])

@app.route('/api/results/today', methods=['GET'])
def api_today():
    today = date.today().strftime('%d-%m-%Y')
    conn = get_db()
    rows = conn.execute(
        'SELECT city_key, result_number FROM results WHERE result_date = ?', (today,)
    ).fetchall()
    conn.close()
    return jsonify({r['city_key']: r['result_number'] for r in rows})

@app.route('/api/results/chart', methods=['GET'])
def api_chart():
    conn = get_db()
    rows = conn.execute('''
        SELECT result_date, city_key, result_number
        FROM results ORDER BY result_date DESC LIMIT 500
    ''').fetchall()
    conn.close()
    date_map = {}
    for row in rows:
        d = row['result_date']
        if d not in date_map:
            date_map[d] = {'date': d}
        date_map[d][row['city_key']] = row['result_number']
    sorted_dates = sorted(date_map.values(), key=lambda x: x['date'], reverse=True)
    return jsonify(sorted_dates[:30])

@app.route('/api/khaiwals', methods=['GET'])
def api_khaiwals():
    """Returns active Khaiwal boards."""
    boards = get_active_khaiwals()
    return jsonify([dict(b) for b in boards])

@app.route('/api/settings', methods=['GET'])
def api_settings():
    """Returns global site settings (Telegram and WhatsApp)."""
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM site_settings').fetchall()
    conn.close()
    settings = {r['key']: r['value'] for r in rows}
    return jsonify(settings)

# ============================================================
# ADMIN — LOGIN & LOGOUT
# ============================================================

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin_panel'))
    error = None
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USER and \
           request.form.get('password') == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        error = 'Invalid credentials!'
    return render_template('login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# ============================================================
# ADMIN — RESULT ENTRY
# ============================================================

@app.route('/admin/panel', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    message = None
    if request.method == 'POST':
        action_type = request.form.get('action_type', 'result')
        if action_type == 'settings':
            tg = request.form.get('telegram_link', '').strip()
            wa = request.form.get('whatsapp_number', '').strip()
            conn = get_db()
            if tg: conn.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES ('telegram_link', ?)", (tg,))
            if wa: conn.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES ('whatsapp_number', ?)", (wa,))
            conn.commit()
            conn.close()
            message = "✅ Telegram & WhatsApp Chatbot links updated successfully!"
        else:
            result_date = request.form.get('result_date', '').strip()
            city_key    = request.form.get('city', '').strip()
            number      = request.form.get('number', '').strip()
            if result_date and city_key and number:
                try:
                    dt = datetime.strptime(result_date, '%Y-%m-%d')
                    result_date_fmt = dt.strftime('%d-%m-%Y')
                except Exception:
                    result_date_fmt = result_date
                conn = get_db()
                conn.execute('''
                    INSERT INTO results (result_date, city_key, result_number, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(result_date, city_key) DO UPDATE SET
                        result_number = excluded.result_number,
                        updated_at = excluded.updated_at
                ''', (result_date_fmt, city_key, number, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                message = f"✅ {city_key.upper()} → {number} saved for {result_date_fmt}"
            else:
                message = "❌ Please fill all fields."

    conn = get_db()
    recent = conn.execute('''
        SELECT r.result_date, r.city_key, c.display_name, r.result_number, r.updated_at
        FROM results r
        LEFT JOIN cities c ON r.city_key = c.city_key
        ORDER BY r.updated_at DESC LIMIT 50
    ''').fetchall()
    
    settings_rows = conn.execute('SELECT key, value FROM site_settings').fetchall()
    settings = {r['key']: r['value'] for r in settings_rows}
    conn.close()

    today = date.today().strftime('%Y-%m-%d')
    cities = get_active_cities()
    return render_template('admin.html', message=message, recent=recent,
                           today=today, cities=cities, settings=settings)

@app.route('/admin/scrape-now', methods=['POST'])
def admin_scrape_now():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    threading.Thread(target=scrape_results, daemon=True).start()
    return redirect(url_for('admin_panel') + '?msg=Scraping+started!')

# ============================================================
# ADMIN — CITY MANAGER
# ============================================================

@app.route('/admin/cities', methods=['GET'])
def admin_cities():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    cities = get_all_cities()
    msg = request.args.get('msg', '')
    return render_template('cities.html', cities=cities, msg=msg)

@app.route('/admin/cities/add', methods=['POST'])
def admin_city_add():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    display_name = request.form.get('display_name', '').strip().upper()
    scrape_id    = request.form.get('scrape_id', '').strip().upper()
    result_time  = request.form.get('result_time', '').strip()
    sort_order   = request.form.get('sort_order', 99)

    if not display_name or not scrape_id:
        return redirect(url_for('admin_cities') + '?msg=❌+Name+and+Scrape+ID+required')

    city_key = display_name.lower().replace(' ', '_').replace('-', '_').replace('.', '')

    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO cities (city_key, display_name, scrape_id, result_time, is_active, sort_order, created_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
        ''', (city_key, display_name, scrape_id, result_time, int(sort_order), datetime.now().isoformat()))
        conn.commit()
        msg = f"✅+City+{display_name}+added!"
    except sqlite3.IntegrityError:
        msg = f"❌+City+key+{city_key}+already+exists"
    conn.close()
    return redirect(url_for('admin_cities') + f'?msg={msg}')

@app.route('/admin/cities/toggle/<int:city_id>', methods=['POST'])
def admin_city_toggle(city_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    city = conn.execute('SELECT is_active FROM cities WHERE id=?', (city_id,)).fetchone()
    if city:
        new_state = 0 if city['is_active'] else 1
        conn.execute('UPDATE cities SET is_active=? WHERE id=?', (new_state, city_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_cities') + '?msg=✅+City+status+updated')

@app.route('/admin/cities/delete/<int:city_id>', methods=['POST'])
def admin_city_delete(city_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    conn.execute('DELETE FROM cities WHERE id=?', (city_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_cities') + '?msg=🗑️+City+deleted')

@app.route('/admin/cities/edit/<int:city_id>', methods=['POST'])
def admin_city_edit(city_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    display_name = request.form.get('display_name', '').strip().upper()
    scrape_id    = request.form.get('scrape_id', '').strip().upper()
    result_time  = request.form.get('result_time', '').strip()
    sort_order   = request.form.get('sort_order', 99)
    conn = get_db()
    conn.execute('''
        UPDATE cities SET display_name=?, scrape_id=?, result_time=?, sort_order=?
        WHERE id=?
    ''', (display_name, scrape_id, result_time, int(sort_order), city_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_cities') + '?msg=✅+City+updated')

# ============================================================
# ADMIN — KHAIWAL BOARDS MANAGER
# ============================================================

@app.route('/admin/khaiwals', methods=['GET', 'POST'])
def admin_khaiwals():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    msg = request.args.get('msg', '')
    if request.method == 'POST':
        kid        = request.form.get('id')
        name       = request.form.get('name', '').strip()
        badge      = request.form.get('badge', '').strip()
        tagline    = request.form.get('tagline', '').strip()
        timings    = request.form.get('timings', '').strip()
        rate_jodi  = request.form.get('rate_jodi', '').strip()
        rate_haruf = request.form.get('rate_haruf', '').strip()
        whatsapp   = request.form.get('whatsapp', '').strip()
        calling    = request.form.get('calling', '').strip()
        telegram   = request.form.get('telegram', '').strip()
        board_theme = request.form.get('board_theme', 'theme-blue').strip()
        is_active  = 1 if request.form.get('is_active') else 0

        conn = get_db()
        conn.execute('''
            UPDATE khaiwals SET
                name=?, badge=?, tagline=?, timings=?, rate_jodi=?, rate_haruf=?,
                whatsapp=?, calling=?, is_active=?, telegram=?, board_theme=?
            WHERE id=?
        ''', (name, badge, tagline, timings, rate_jodi, rate_haruf, whatsapp, calling, is_active, telegram, board_theme, kid))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_khaiwals') + f'?msg=✅+Board+{kid}+updated+successfully!')

    khaiwals = get_all_khaiwals()
    return render_template('khaiwals.html', khaiwals=khaiwals, msg=msg)

# ============================================================
# ADMIN — CHATBOT, THEMES & LEAK JODI SETTINGS
# ============================================================

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    msg = request.args.get('msg', '')
    conn = get_db()
    if request.method == 'POST':
        # 1. Chatbot & Fast Action links
        cb_tg = request.form.get('chatbot_telegram', '').strip()
        cb_wa = request.form.get('chatbot_whatsapp', '').strip()
        
        # 2. Support Helpline & Community links
        sp_tg = request.form.get('support_telegram', '').strip()
        sp_wa = request.form.get('support_whatsapp', '').strip()
        
        # 3. App download link
        apk = request.form.get('app_download_link', '').strip()

        # 4. Site-wide theme
        site_theme = request.form.get('site_theme', 'theme-classic-dark').strip()

        # 5. Leak Jodi Section
        leak_active = '1' if request.form.get('leak_jodi_active') else '0'
        leak_title = request.form.get('leak_jodi_title', '').strip()
        leak_tagline = request.form.get('leak_jodi_tagline', '').strip()
        leak_games = request.form.get('leak_jodi_games', '').strip()
        leak_wa = request.form.get('leak_jodi_whatsapp', '').strip()
        leak_tg = request.form.get('leak_jodi_telegram', '').strip()
        leak_note = request.form.get('leak_jodi_note', '').strip()

        settings_to_save = {
            'chatbot_telegram': cb_tg,
            'chatbot_whatsapp': cb_wa,
            'support_telegram': sp_tg,
            'support_whatsapp': sp_wa,
            'telegram_link': sp_tg or cb_tg,      # backwards compat
            'whatsapp_number': sp_wa or cb_wa,    # backwards compat
            'app_download_link': apk,
            'site_theme': site_theme,
            'leak_jodi_active': leak_active,
            'leak_jodi_title': leak_title,
            'leak_jodi_tagline': leak_tagline,
            'leak_jodi_games': leak_games,
            'leak_jodi_whatsapp': leak_wa,
            'leak_jodi_telegram': leak_tg,
            'leak_jodi_note': leak_note
        }
        for k, v in settings_to_save.items():
            conn.execute("INSERT OR REPLACE INTO site_settings (key, value) VALUES (?, ?)", (k, v))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_settings') + '?msg=✅+All+Settings+and+Themes+updated+successfully!')

    settings_rows = conn.execute('SELECT key, value FROM site_settings').fetchall()
    settings = {r['key']: r['value'] for r in settings_rows}
    conn.close()
    return render_template('settings.html', settings=settings, msg=msg)

# ============================================================
# FRONTEND SERVING
# ============================================================

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'css'), filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.path.join(FRONTEND_DIR, 'js'), filename)

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'by': 'Saurav', 'time': datetime.now().isoformat()})

# ============================================================
# START
# ============================================================

if __name__ == '__main__':
    init_db()
    t = threading.Thread(target=scraper_loop, daemon=True)
    t.start()
    logging.info("🚀 Satta Takht by Saurav — Backend started!")
    app.run(debug=True, host='0.0.0.0', port=5000)
