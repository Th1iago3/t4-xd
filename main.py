from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response, session
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime, timedelta
import threading
import logging
import time
import json
import os
from functools import wraps
from urllib.parse import quote_plus
import uuid
import hashlib
import re
import socket

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # TODO: Set to True in production with HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('user_logs.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(stream_handler)

# Database and file paths
DB_PATH = 'users.db'
USERS_FILE = 'users.json'
LOCK = threading.Lock()

# Socket server settings
SOCKET_PORT = 5001  # Separate port for socket server
SOCKET_HOST = '0.0.0.0'  # Listen on all interfaces

# Initialize users.json if it doesn't exist
def init_users_file():
    """Initialize users.json with a default admin user if it doesn't exist."""
    if not os.path.exists(USERS_FILE):
        default_user = {
            "username": "@t4x",
            "password": hashlib.sha256("@@@t4x".encode()).hexdigest(),
            "role": "admin",
            "is_admin": True,
            "api_key": str(uuid.uuid4()),
            "request_limit": 100
        }
        with open(USERS_FILE, 'w') as f:
            json.dump({"users": [default_user]}, f, indent=2)
        logger.info("users.json initialized with default user")

# Database Initialization
def init_db():
    """Initialize SQLite database with tables for users, searches, and API status."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT NOT NULL,
                    user_agent TEXT,
                    first_visit TEXT NOT NULL,
                    last_visit TEXT NOT NULL,
                    visit_count INTEGER DEFAULT 1,
                    UNIQUE(ip, user_agent)
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    results_count INTEGER DEFAULT 0,
                    response_time REAL DEFAULT 0.0
                )
            ''')
            c.execute('''
                CREATE TABLE IF NOT EXISTS api_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_time REAL DEFAULT 0.0
                )
            ''')
            c.execute('CREATE INDEX IF NOT EXISTS idx_searches_query ON searches(query)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_searches_timestamp ON searches(timestamp)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_users_ip ON users(ip)')
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s" % str(e))
        raise

# Jinja2 Filter for Masking API Key
@app.template_filter('mask_api_key')
def mask_api_key(api_key):
    """Mask API key, showing only the last 4 characters (e.g., ****1234)."""
    if not api_key or len(api_key) <= 4:
        return api_key
    return '****' + api_key[-4:]

# User Management
def validate_user(username, password):
    """Validate user credentials against users.json."""
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            logger.debug(f"Attempting to validate user: {username}, hashed password: {hashed_password[:8]}...")
            for user in data.get('users', []):
                if user['username'] == username and user['password'] == hashed_password:
                    user['masked_api_key'] = mask_api_key(user['api_key'])
                    logger.info(f"User {username} validated successfully")
                    return user
            logger.warning(f"Validation failed for user: {username}")
            return None
    except Exception as e:
        logger.error("Failed to validate user: %s" % str(e))
        return None

def get_user_by_username(username):
    """Retrieve user data by username from users.json."""
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            for user in data.get('users', []):
                if user['username'] == username:
                    user['masked_api_key'] = mask_api_key(user['api_key'])
                    return user
        return None
    except Exception as e:
        logger.error("Failed to get user by username: %s" % str(e))
        return None

def get_user_by_key(api_key):
    """Retrieve user data by API key from users.json."""
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            for user in data.get('users', []):
                if user['api_key'] == api_key:
                    user['masked_api_key'] = mask_api_key(user['api_key'])
                    return user
        return None
    except Exception as e:
        logger.error("Failed to get user by API key: %s" % str(e))
        return None

def get_all_users():
    """Retrieve all users from users.json."""
    try:
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            users = data.get('users', [])
            for user in users:
                user['masked_api_key'] = mask_api_key(user['api_key'])
            return users
    except Exception as e:
        logger.error("Failed to get all users: %s" % str(e))
        return []

def add_user(username, password, is_admin=False, request_limit=20):
    """Add a new user to users.json."""
    try:
        with LOCK:
            with open(USERS_FILE, 'r+') as f:
                data = json.load(f)
                if any(user['username'] == username for user in data['users']):
                    return False, "Usuário já existe"
                new_user = {
                    "username": username,
                    "password": hashlib.sha256(password.encode()).hexdigest(),
                    "role": "admin" if is_admin else "user",
                    "is_admin": is_admin,
                    "api_key": str(uuid.uuid4()),
                    "request_limit": request_limit
                }
                data['users'].append(new_user)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
                logger.info("New user registered: %s" % username)
                return True, "Usuário registrado com sucesso"
    except Exception as e:
        logger.error("Failed to add user: %s" % str(e))
        return False, "Erro ao registrar usuário"

def update_user_api_key(username, request_limit):
    """Update API key and request limit for a user."""
    try:
        with LOCK:
            with open(USERS_FILE, 'r+') as f:
                data = json.load(f)
                for user in data['users']:
                    if user['username'] == username:
                        user['api_key'] = str(uuid.uuid4())
                        user['request_limit'] = request_limit
                        f.seek(0)
                        json.dump(data, f, indent=2)
                        f.truncate()
                        logger.info("API key updated for user: %s" % username)
                        return True, user['api_key']
                return False, "Usuário não encontrado"
    except Exception as e:
        logger.error("Failed to update API key: %s" % str(e))
        return False, "Erro ao atualizar chave"

def update_user_profile(username, new_username=None, new_password=None, current_password=None):
    """Update user profile after validating current password."""
    try:
        with LOCK:
            with open(USERS_FILE, 'r+') as f:
                data = json.load(f)
                for user in data['users']:
                    if user['username'] == username:
                        if current_password and user['password'] != hashlib.sha256(current_password.encode()).hexdigest():
                            return False, "Senha atual incorreta"
                        if new_username and new_username != username:
                            if any(u['username'] == new_username for u in data['users']):
                                return False, "Novo nome de usuário já existe"
                            user['username'] = new_username
                        if new_password:
                            user['password'] = hashlib.sha256(new_password.encode()).hexdigest()
                        f.seek(0)
                        json.dump(data, f, indent=2)
                        f.truncate()
                        logger.info("Profile updated for user: %s" % username)
                        return True, "Perfil atualizado com sucesso"
                return False, "Usuário não encontrado"
    except Exception as e:
        logger.error("Failed to update profile: %s" % str(e))
        return False, "Erro ao atualizar perfil"

# Authentication Decorator
def auth_required(f):
    """Decorator to require authentication for routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            logger.warning("No user session found")
            return redirect(url_for('login'))
        user = get_user_by_username(session['username'])
        if not user:
            logger.warning("Invalid user session for username: %s" % session.get('username'))
            session.pop('username', None)
            return redirect(url_for('login'))
        request.user = user
        return f(*args, **kwargs)
    return decorated

# Logging Functions
def log_user(ip, user_agent):
    """Log user visit to the database."""
    try:
        with LOCK:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute("SELECT visit_count FROM users WHERE ip = ? AND user_agent = ?", (ip, user_agent))
                result = c.fetchone()
                if result:
                    c.execute("""
                        UPDATE users
                        SET last_visit = ?, visit_count = visit_count + 1
                        WHERE ip = ? AND user_agent = ?
                    """, (timestamp, ip, user_agent))
                else:
                    c.execute("""
                        INSERT INTO users (ip, user_agent, first_visit, last_visit, visit_count)
                        VALUES (?, ?, ?, ?, 1)
                    """, (ip, user_agent, timestamp, timestamp))
                conn.commit()
                logger.info("User logged - IP: %s..." % ip[:10])
    except Exception as e:
        logger.error("Error logging user: %s" % str(e))

def log_search(query, ip, results_count=0, response_time=0.0):
    """Log search query to the database."""
    if results_count == 0:
        return
    try:
        with LOCK:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute("""
                    INSERT INTO searches (query, ip, timestamp, results_count, response_time)
                    VALUES (?, ?, ?, ?, ?)
                """, (query, ip, timestamp, results_count, response_time))
                conn.commit()
                logger.info("Search logged - Query: %s, Results: %d" % (query, results_count))
    except Exception as e:
        logger.error("Error logging search: %s" % str(e))

def log_api_status(status, response_time=0.0):
    """Log API status to the database."""
    try:
        with LOCK:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                c.execute("""
                    INSERT INTO api_status (timestamp, status, response_time)
                    VALUES (?, ?, ?)
                """, (timestamp, status, response_time))
                conn.commit()
    except Exception as e:
        logger.error("Error logging API status: %s" % str(e))

# API Status Checking
def check_api_status():
    """Check the status of the external API."""
    logger.info("Mocking API status due to DNS issue")
    return {"status": "online", "response_time": 0.1}
    # Uncomment when DNS issue is resolved:
    # url = "https://atrocidades18.net/?s=test"
    # headers = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    #     'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    #     'Accept-Encoding': 'gzip, deflate',
    #     'Connection': 'keep-alive'
    # }
    # try:
    #     start_time = time.time()
    #     response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
    #     response_time = time.time() - start_time
    #     status = "online" if response.status_code == 200 and response_time < 3 else "slow" if response.status_code == 200 else "offline"
    #     log_api_status(status, response_time)
    #     return {"status": status, "response_time": round(response_time, 2)}
    # except requests.RequestException as e:
    #     logger.error("API status check failed: %s" % str(e))
    #     log_api_status("offline", 0.0)
    #     return {"status": "offline", "response_time": 0.0}

# Scraping Functions
def scrape_videos(query, page=1):
    """Scrape videos from the external website."""
    videos = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate'
    }
    try:
        start_time = time.time()
        with requests.Session() as session:
            url = f"https://atrocidades18.net/?s={quote_plus(query)}" if page == 1 else f"https://atrocidades18.net/page/{page}/?s={quote_plus(query)}"
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            posts = soup.find_all('div', class_='writemag-compact-post-wrapper')
            for post in posts:
                video_data = {}
                thumbnail = post.find('img', class_='writemag-compact-post-thumbnail-img')
                video_data['thumbnail'] = thumbnail['src'] if thumbnail and thumbnail.get('src') else ''
                title_link = post.find('h2', class_='writemag-compact-post-title').find('a') if post.find('h2', class_='writemag-compact-post-title') else None
                video_data['title'] = title_link.text.strip() if title_link else 'Título não disponível'
                video_data['url'] = title_link['href'] if title_link else ''
                description = post.find('div', class_='writemag-compact-post-snippet').find('p') if post.find('div', class_='writemag-compact-post-snippet') else None
                video_data['description'] = description.text.strip() if description else 'Descrição não disponível'
                views = post.find('span', class_='themesdna-views')
                video_data['views'] = views.text.strip() if views else '0'
                date = post.find('span', class_='writemag-compact-post-header-date')
                video_data['date'] = date.text.strip().replace(' ', ' ') if date else 'Data não disponível'
                comments = post.find('span', class_='writemag-compact-post-header-comment')
                video_data['comments'] = comments.find('a').text.split()[0] if comments and comments.find('a') else '0'
                if video_data['url']:
                    try:
                        post_response = session.get(video_data['url'], headers=headers, timeout=10)
                        post_response.raise_for_status()
                        post_soup = BeautifulSoup(post_response.text, 'html.parser')
                        video_tag = post_soup.find('video')
                        video_data['video_url'] = video_tag.find('source')['src'] if video_tag and video_tag.find('source') and video_tag.find('source').get('src') else ''
                    except Exception as e:
                        logger.error("Error scraping video URL for %s: %s" % (video_data['url'], str(e)))
                        video_data['video_url'] = ''
                if video_data['title'] != 'Título não disponível' and video_data['url']:
                    video_data['page'] = page
                    videos.append(video_data)
        response_time = time.time() - start_time
        logger.info("Scraped %d videos for query: %s (page %d) in %.2fs" % (len(videos), query, page, response_time))
        return videos, page
    except Exception as e:
        logger.error("Error scraping videos: %s" % str(e))
        return [], page

def scrape_additional_pages(query, start_page=2, max_pages=4):
    """Scrape additional pages of videos."""
    videos = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate'
    }
    try:
        with requests.Session() as session:
            for p in range(start_page, max_pages + 1):
                start_time = time.time()
                url = f"https://atrocidades18.net/page/{p}/?s={quote_plus(query)}"
                response = session.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                posts = soup.find_all('div', class_='writemag-grid-post')
                page_videos = []
                for post in posts:
                    video_data = {}
                    thumbnail = post.find('img', class_='writemag-grid-post-thumbnail-img')
                    video_data['thumbnail'] = thumbnail['src'] if thumbnail and thumbnail.get('src') else ''
                    title_link = post.find('h2', class_='writemag-grid-post-title').find('a') if post.find('h2', class_='writemag-grid-post-title') else None
                    video_data['title'] = title_link.text.strip() if title_link else 'Título não disponível'
                    video_data['url'] = title_link['href'] if title_link else ''
                    description = post.find('div', class_='writemag-grid-post-snippet').find('p') if post.find('div', class_='writemag-grid-post-snippet') else None
                    video_data['description'] = description.text.strip() if description else 'Descrição não disponível'
                    views = post.find('span', class_='themesdna-view')
                    video_data['views'] = views.text.strip() if views else '0'
                    date = post.find('span', class_='writemag-grid-post-date')
                    video_data['date'] = date.text.strip().replace(' ', ' ') if date else 'Data não disponível'
                    comments = post.find('span', class_='grid-post-comment')
                    video_data['comments'] = comments.find('a').text.split()[0] if comments and comments.find('a') else '0'
                    if video_data['url']:
                        try:
                            post_response = session.get(video_data['url'], headers=headers, timeout=10)
                            post_response.raise_for_status()
                            post_soup = BeautifulSoup(post_response.text, 'html.parser')
                            video_tag = post_soup.find('video')
                            video_data['video_url'] = video_tag.find('source')['src'] if video_tag and video_tag.find('source') and video_tag.find('source').get('src') else ''
                        except Exception as e:
                            logger.error("Error scraping video URL for %s: %s" % (video_data['url'], str(e)))
                            video_data['video_url'] = ''
                    if video_data['title'] != 'Título não disponível' and video_data['url']:
                        video_data['page'] = p
                        page_videos.append(video_data)
                videos.extend(page_videos)
                response_time = time.time() - start_time
                logger.info("Scraped %d videos for query: %s (page %d) in %.2fs" % (len(page_videos), query, p, response_time))
        return videos, max_pages
    except Exception as e:
        logger.error("Error scraping additional pages: %s" % str(e))
        return videos, max_pages

# Statistics Functions
def get_recent_searches(limit=10):
    """Retrieve recent searches from the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT query, timestamp, results_count, response_time
                FROM searches
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            searches = []
            for row in c.fetchall():
                searches.append({
                    'query': row[0],
                    'timestamp': row[1],
                    'results_count': row[2],
                    'response_time': round(row[3], 2) if row[3] else 0.0
                })
            return searches
    except Exception as e:
        logger.error("Error fetching recent searches: %s" % str(e))
        return []

def get_search_stats():
    """Retrieve search statistics from the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(DISTINCT query) FROM searches")
            total_unique_queries = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM searches")
            total_searches = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(DISTINCT ip) FROM users")
            unique_users = c.fetchone()[0] or 0
            c.execute("SELECT SUM(visit_count) FROM users")
            total_visits = c.fetchone()[0] or 0
            c.execute("""
                SELECT query, COUNT(*) as count
                FROM searches
                GROUP BY query
                ORDER BY count DESC
                LIMIT 1
            """)
            top_query_result = c.fetchone()
            top_query = top_query_result[0] if top_query_result else 'N/A'
            top_query_count = top_query_result[1] if top_query_result else 0
            c.execute("SELECT AVG(response_time) FROM searches WHERE response_time > 0")
            avg_response_time = c.fetchone()[0] or 0.0
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            c.execute("SELECT COUNT(*) FROM searches WHERE timestamp > ?", (yesterday,))
            recent_searches = c.fetchone()[0] or 0
            return {
                'total_unique_queries': total_unique_queries,
                'total_searches': total_searches,
                'unique_users': unique_users,
                'total_visits': total_visits,
                'top_query': top_query,
                'top_query_count': top_query_count,
                'avg_response_time': round(avg_response_time, 2),
                'recent_searches_24h': recent_searches
            }
    except Exception as e:
        logger.error("Error fetching search stats: %s" % str(e))
        return {
            'total_unique_queries': 0,
            'total_searches': 0,
            'unique_users': 0,
            'total_visits': 0,
            'top_query': 'N/A',
            'top_query_count': 0,
            'avg_response_time': 0.0,
            'recent_searches_24h': 0
        }

# Rate Limiting
def rate_limit(max_requests=20, per_seconds=60):
    """Decorator for rate limiting API requests."""
    calls = {}
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            now = time.time()
            ip = request.remote_addr
            calls[ip] = [call_time for call_time in calls.get(ip, []) if now - call_time < per_seconds]
            if len(calls.get(ip, [])) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            calls.setdefault(ip, []).append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

# Socket Server
def start_socket_server():
    """Run a TCP socket server to handle connections from network devices."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((SOCKET_HOST, SOCKET_PORT))
        server_socket.listen(5)
        logger.info(f"Socket server started on {SOCKET_HOST}:{SOCKET_PORT}")
        
        while True:
            client_socket, addr = server_socket.accept()
            logger.info(f"New socket connection from {addr}")
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
    except Exception as e:
        logger.error(f"Socket server error: {e}")
    finally:
        server_socket.close()

def handle_client(client_socket, addr):
    """Handle individual client connections."""
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            logger.info(f"Received from {addr}: {data}")
            response = f"Server: {data}"
            client_socket.send(response.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error handling client {addr}: {e}")
    finally:
        client_socket.close()
        logger.info(f"Connection closed for {addr}")

# Network Discovery
def get_local_ip():
    """Get the local IP address using socket."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        if local_ip.startswith('127.'):
            return '0.0.0.0'
        return local_ip
    except Exception as e:
        logger.error(f"Failed to get local IP: {e}")
        return '0.0.0.0'

# Routes
@app.route('/')
@auth_required
def index():
    """Render the index page with stats and recent searches."""
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    threading.Thread(target=log_user, args=(user_ip, user_agent), daemon=True).start()
    stats = get_search_stats()
    recent_searches = get_recent_searches()
    return render_template('base.html', user=request.user, stats=stats, recent_searches=recent_searches, api_status=check_api_status())

@app.route('/home')
@app.route('/home/apis/gore')
@auth_required
def home():
    """Redirect home routes to index."""
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if 'username' in session:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            error = "Todos os campos são obrigatórios."
        else:
            user = validate_user(username, password)
            if user:
                session['username'] = username
                session.permanent = True
                response = make_response(redirect(url_for('index')))
                response.set_cookie('api_key', user['api_key'], max_age=3600, httponly=True, secure=app.config['SESSION_COOKIE_SECURE'])
                logger.info("User logged in: %s" % username)
                return response
            error = "Credenciais inválidas. Tente novamente."
    return render_template('login.html', error=error, user=None, api_status=check_api_status())

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if 'username' in session:
        return redirect(url_for('index'))
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        if not username or not password or not confirm_password:
            error = "Todos os campos são obrigatórios."
        elif password != confirm_password:
            error = "As senhas não coincidem."
        elif len(username) < 3 or len(username) > 20:
            error = "O nome de usuário deve ter entre 3 e 20 caracteres."
        elif len(password) < 6:
            error = "A senha deve ter pelo menos 6 caracteres."
        elif not re.match(r'^[a-zA-Z0-9_@]+$', username):
            error = "O nome de usuário só pode conter letras, números, _ ou @."
        else:
            success, message = add_user(username, password)
            if success:
                return redirect(url_for('login'))
            error = message
    return render_template('register.html', error=error, success=success, user=None, api_status=check_api_status())

@app.route('/logout')
def logout():
    """Handle user logout."""
    username = session.get('username', 'unknown')
    session.pop('username', None)
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('api_key')
    logger.info("User logged out: %s" % username)
    return response

@app.route('/docs')
@auth_required
def docs():
    """Render the API documentation page."""
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    threading.Thread(target=log_user, args=(user_ip, user_agent), daemon=True).start()
    return render_template('docs.html', user=request.user, api_status=check_api_status())

@app.route('/stats', endpoint='stats')
@auth_required
def stats_page():
    """Render the statistics page."""
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    threading.Thread(target=log_user, args=(user_ip, user_agent), daemon=True).start()
    stats = get_search_stats()
    recent_searches = get_recent_searches(20)
    return render_template('stats.html', user=request.user, stats=stats, recent_searches=recent_searches, api_status=check_api_status())

@app.route('/admin', methods=['GET', 'POST'])
@auth_required
def admin():
    """Handle admin panel for managing users."""
    if not request.user.get('is_admin', False):
        logger.warning("Unauthorized access attempt to admin page by %s" % request.user['username'])
        return redirect(url_for('index'))
    error = None
    success = None
    users = get_all_users()
    if request.method == 'POST':
        selected_username = request.form.get('username', '').strip()
        request_limit = request.form.get('request_limit', '')
        if not selected_username or not request_limit:
            error = "Todos os campos são obrigatórios."
        elif not request_limit.isdigit() or int(request_limit) < 0:
            error = "O limite de requisições deve ser um número positivo."
        else:
            success, message = update_user_api_key(selected_username, int(request_limit))
            if not success:
                error = message
            else:
                success = f"Chave API gerada com sucesso para {selected_username}!"
    return render_template('admin.html', user=request.user, users=users, error=error, success=success, api_status=check_api_status())

@app.route('/profile', methods=['GET', 'POST'])
@auth_required
def profile():
    """Handle user profile updates."""
    error = None
    success = None
    if request.method == 'POST':
        new_username = request.form.get('new_username', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        current_password = request.form.get('current_password', '').strip()
        if not current_password:
            error = "A senha atual é obrigatória."
        elif new_password and new_password != confirm_password:
            error = "As senhas não coincidem."
        elif new_password and len(new_password) < 6:
            error = "A nova senha deve ter pelo menos 6 caracteres."
        elif new_username and (len(new_username) < 3 or len(new_username) > 20):
            error = "O novo nome de usuário deve ter entre 3 e 20 caracteres."
        elif new_username and not re.match(r'^[a-zA-Z0-9_@]+$', new_username):
            error = "O novo nome de usuário só pode conter letras, números, _ ou @."
        else:
            success, message = update_user_profile(
                request.user['username'],
                new_username if new_username else None,
                new_password if new_password else None,
                current_password
            )
            if success:
                success = message
                if new_username:
                    session['username'] = new_username
                    user = get_user_by_username(new_username)
                    if user:
                        response = make_response(render_template('profile.html', user=user, success=success, error=None, api_status=check_api_status()))
                        response.set_cookie('api_key', user['api_key'], max_age=3600, httponly=True, secure=app.config['SESSION_COOKIE_SECURE'])
                        return response
            else:
                error = message
    return render_template('profile.html', user=request.user, error=error, success=success, api_status=check_api_status())

@app.route('/apis')
@auth_required
def apis():
    """Render the APIs page."""
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    threading.Thread(target=log_user, args=(user_ip, user_agent), daemon=True).start()
    return render_template('apis.html', user=request.user, api_status=check_api_status())

@app.route('/api')
@auth_required
def api():
    """Render the APIs page."""
    user_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    threading.Thread(target=log_user, args=(user_ip, user_agent), daemon=True).start()
    return render_template('apis.html', user=request.user, api_status=check_api_status())

@app.route('/api/gore', methods=['GET'])
@rate_limit(max_requests=20, per_seconds=60)
def api_gore():
    """Handle API requests for video scraping."""
    query = request.args.get('query', '').strip()
    token = request.args.get('token', '').strip()
    user_ip = request.remote_addr
    if not query:
        return jsonify({'error': 'Parâmetro "query" é obrigatório'}), 400
    if len(query) > 100:
        return jsonify({'error': 'O termo de busca deve ter no máximo 100 caracteres'}), 400
    if not token:
        return jsonify({'error': 'Token de API é obrigatório'}), 401
    user = get_user_by_key(token)
    if not user:
        return jsonify({'error': 'Token de API inválido'}), 401
    start_time = time.time()
    videos, page = scrape_videos(query)
    response_time = time.time() - start_time
    threading.Thread(target=log_search, args=(query, user_ip, len(videos), response_time), daemon=True).start()
    return jsonify({
        'query': query,
        'results': videos,
        'count': len(videos),
        'response_time': round(response_time, 2)
    })

@app.route('/api/gore/additional', methods=['GET'])
@rate_limit(max_requests=10, per_seconds=60)
def api_gore_additional():
    """Handle API requests for additional video pages."""
    query = request.args.get('query', '').strip()
    token = request.args.get('token', '').strip()
    user_ip = request.remote_addr
    if not query:
        return jsonify({'error': 'Parâmetro "query" é obrigatório'}), 400
    if len(query) > 100:
        return jsonify({'error': 'O termo de busca deve ter no máximo 100 caracteres'}), 400
    if not token:
        return jsonify({'error': 'Token de API é obrigatório'}), 401
    user = get_user_by_key(token)
    if not user:
        return jsonify({'error': 'Token de API inválido'}), 401
    start_time = time.time()
    videos, max_pages = scrape_additional_pages(query)
    response_time = time.time() - start_time
    threading.Thread(target=log_search, args=(query, user_ip, len(videos), response_time), daemon=True).start()
    return jsonify({
        'query': query,
        'results': videos,
        'count': len(videos),
        'response_time': round(response_time, 2),
        'max_pages': max_pages
    })

@app.route('/api/stats', methods=['GET'])
@rate_limit(max_requests=10, per_seconds=60)
def api_stats():
    """Return search statistics via API."""
    stats = get_search_stats()
    return jsonify(stats)

# Background Task
def background_api_check():
    """Periodically check API status in the background."""
    while True:
        try:
            check_api_status()
            logger.info("API status checked in background")
        except Exception as e:
            logger.error("Background API check failed: %s" % str(e))
        time.sleep(300)  # Check every 5 minutes

if __name__ == '__main__':
    init_users_file()
    init_db()
    
    # Start background tasks
    threading.Thread(target=background_api_check, daemon=True).start()
    threading.Thread(target=start_socket_server, daemon=True).start()
    
    # Get local IP for logging
    local_ip = get_local_ip()
    flask_port = 5000
    logger.info(f"Starting Flask server on http://{local_ip}:{flask_port}")
    
    try:
        # Run Flask app
        app.run(debug=False, host='0.0.0.0', port=flask_port, threaded=True)
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
