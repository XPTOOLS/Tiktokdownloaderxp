from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from loguru import logger
import os
from bson import ObjectId
import json

# Import configuration from config.py
from config import db, ADMIN_USERNAME, ADMIN_PASSWORD_HASH
from config import COLLECTION_STATS, COLLECTION_NOTIFICATIONS, COLLECTION_ACTIVITY, COLLECTION_USERS

app = Flask(__name__)
CORS(app)

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

app.json_encoder = JSONEncoder

# Serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    logger.debug(f"📁 Serving static file: {filename}")
    return send_from_directory('static', filename)

# Serve HTML files from templates folder
@app.route('/')
def serve_user():
    logger.info("🌐 Serving user.html for root path")
    return send_from_directory('templates', 'user.html')

@app.route('/user.html')
def serve_user_html():
    logger.info("🌐 Serving user.html")
    return send_from_directory('templates', 'user.html')

@app.route('/admin')
def serve_admin():
    logger.info("🔧 Serving admin.html")
    return send_from_directory('templates', 'admin.html')

@app.route('/login')
def serve_login():
    logger.info("🔐 Serving login.html")
    return send_from_directory('templates', 'login.html')

# API Routes (keep all existing API endpoints exactly as they are)
@app.route('/api/track-visit', methods=['POST'])
def track_visit():
    try:
        data = request.get_json()
        page = data.get('page', 'user')
        logger.info(f"📊 Tracking visit to page: {page}")
        
        visit_data = {
            'page': page,
            'timestamp': datetime.now(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        result = db[COLLECTION_STATS].insert_one(visit_data)
        logger.success(f"✅ Visit tracked successfully with ID: {result.inserted_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"❌ Error tracking visit: {e}")
        return jsonify({'error': 'Failed to track visit'}), 500

@app.route('/api/track-download', methods=['POST'])
def track_download():
    try:
        data = request.get_json()
        url = data.get('url', 'Unknown')[:100]  # Limit URL length for logging
        logger.info(f"📥 Tracking download attempt for URL: {url}")
        
        download_data = {
            'url': data.get('url'),
            'timestamp': datetime.now(),
            'ip_address': request.remote_addr,
            'status': 'attempted'
        }
        
        result = db[COLLECTION_STATS].insert_one(download_data)
        logger.success(f"✅ Download attempt tracked with ID: {result.inserted_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"❌ Error tracking download: {e}")
        return jsonify({'error': 'Failed to track download'}), 500

@app.route('/api/track-successful-download', methods=['POST'])
def track_successful_download():
    try:
        data = request.get_json()
        logger.info("🎉 Tracking successful download")
        
        download_data = {
            'type': 'successful_download',
            'timestamp': datetime.now(),
            'ip_address': request.remote_addr,
            'status': 'success'
        }
        
        result = db[COLLECTION_STATS].insert_one(download_data)
        logger.success(f"✅ Successful download tracked with ID: {result.inserted_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"❌ Error tracking successful download: {e}")
        return jsonify({'error': 'Failed to track successful download'}), 500

@app.route('/api/notifications')
def get_notifications():
    try:
        logger.debug("🔔 Fetching active notifications")
        # Get the latest active notification
        notification = db[COLLECTION_NOTIFICATIONS].find_one(
            {'active': True},
            sort=[('timestamp', -1)]
        )
        
        if notification:
            message_preview = notification['message'][:50] + '...' if len(notification['message']) > 50 else notification['message']
            logger.info(f"📢 Sending active notification: {message_preview}")
            return jsonify([{
                'message': notification['message'],
                'actionText': notification.get('actionText'),
                'actionUrl': notification.get('actionUrl'),
                'timestamp': notification['timestamp']
            }])
        else:
            logger.debug("📭 No active notifications found")
            return jsonify([])
    except Exception as e:
        logger.error(f"❌ Error fetching notifications: {e}")
        return jsonify([])

@app.route('/api/admin/stats')
def admin_stats():
    try:
        logger.info("📈 Generating admin statistics")
        
        # Total visits
        total_visits = db[COLLECTION_STATS].count_documents({'page': 'user'})
        logger.debug(f"📊 Total visits: {total_visits}")
        
        # Today's visits
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_visits = db[COLLECTION_STATS].count_documents({
            'page': 'user',
            'timestamp': {'$gte': today_start}
        })
        logger.debug(f"📊 Today's visits: {today_visits}")
        
        # Total download attempts
        total_downloads = db[COLLECTION_STATS].count_documents({'url': {'$exists': True}})
        logger.debug(f"📊 Total downloads: {total_downloads}")
        
        # Successful downloads
        successful_downloads = db[COLLECTION_STATS].count_documents({'type': 'successful_download'})
        logger.debug(f"📊 Successful downloads: {successful_downloads}")
        
        # Visits data for chart (last 7 days)
        visits_data = []
        labels = []
        logger.debug("📅 Generating chart data for last 7 days")
        
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            daily_visits = db[COLLECTION_STATS].count_documents({
                'page': 'user',
                'timestamp': {'$gte': date_start, '$lte': date_end}
            })
            
            visits_data.append(daily_visits)
            labels.append(date.strftime('%m/%d'))
            logger.debug(f"📅 {date.strftime('%m/%d')}: {daily_visits} visits")
        
        stats = {
            'totalVisits': total_visits,
            'todayVisits': today_visits,
            'totalDownloads': total_downloads,
            'successfulDownloads': successful_downloads,
            'visitsData': {
                'labels': labels,
                'data': visits_data
            }
        }
        
        logger.success("✅ Admin stats generated successfully")
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ Error getting admin stats: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500

@app.route('/api/admin/activity')
def admin_activity():
    try:
        logger.debug("📋 Fetching recent admin activities")
        activities_cursor = db[COLLECTION_ACTIVITY].find(
            {},
            sort=[('timestamp', -1)],
            limit=20
        )
        
        # Convert cursor to list and handle ObjectId serialization
        activities = []
        for activity in activities_cursor:
            # Convert ObjectId to string
            activity['_id'] = str(activity['_id'])
            activities.append(activity)
        
        logger.info(f"📋 Retrieved {len(activities)} recent activities")
        return jsonify(activities)
    except Exception as e:
        logger.error(f"❌ Error getting activities: {e}")
        return jsonify([])

@app.route('/api/admin/notification', methods=['POST'])
def send_notification():
    try:
        data = request.get_json()
        message = data.get('message', '')
        message_preview = message[:100] + '...' if len(message) > 100 else message
        logger.info(f"📢 Preparing to send notification: {message_preview}")
        
        # Deactivate all previous notifications
        update_result = db[COLLECTION_NOTIFICATIONS].update_many(
            {'active': True},
            {'$set': {'active': False}}
        )
        logger.debug(f"📭 Deactivated {update_result.modified_count} previous notifications")
        
        # Create new notification
        notification_data = {
            'message': data['message'],
            'actionText': data.get('actionText'),
            'actionUrl': data.get('actionUrl'),
            'timestamp': datetime.now(),
            'active': True,
            'sent_by': 'admin'
        }
        
        result = db[COLLECTION_NOTIFICATIONS].insert_one(notification_data)
        logger.success(f"✅ Notification sent successfully with ID: {result.inserted_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"❌ Error sending notification: {e}")
        return jsonify({'error': 'Failed to send notification'}), 500

@app.route('/api/admin/track-activity', methods=['POST'])
def track_admin_activity():
    try:
        data = request.get_json()
        action = data.get('action', 'Unknown')
        details = data.get('details', 'No details')
        logger.info(f"👤 Tracking admin activity: {action} - {details}")
        
        activity_data = {
            'action': data['action'],
            'details': data.get('details'),
            'timestamp': datetime.now(),
            'ip_address': request.remote_addr
        }
        
        result = db[COLLECTION_ACTIVITY].insert_one(activity_data)
        logger.debug(f"✅ Admin activity tracked with ID: {result.inserted_id}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"❌ Error tracking admin activity: {e}")
        return jsonify({'error': 'Failed to track activity'}), 500

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        logger.info(f"🔐 Login attempt for username: {username}")
        
        # Simple authentication
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
            logger.success(f"✅ Successful login for user: {username}")
            
            # Track login activity
            db[COLLECTION_ACTIVITY].insert_one({
                'action': 'Admin Login',
                'details': f'Successful login for {username}',
                'timestamp': datetime.now(),
                'ip_address': request.remote_addr
            })
            
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'token': 'admin_token'  # In production, use JWT tokens
            }), 200
        else:
            logger.warning(f"❌ Failed login attempt for user: {username}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials'
            }), 401
            
    except Exception as e:
        logger.error(f"❌ Error during login: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/admin/verify', methods=['POST'])
def verify_admin():
    try:
        data = request.get_json()
        token = data.get('token')
        
        logger.debug("🔍 Verifying admin token")
        
        # Simple token verification (in production, use proper JWT verification)
        if token == 'admin_token':
            logger.debug("✅ Admin token verified successfully")
            return jsonify({'status': 'success'}), 200
        else:
            logger.warning("❌ Invalid admin token")
            return jsonify({'status': 'error'}), 401
            
    except Exception as e:
        logger.error(f"❌ Error verifying admin: {e}")
        return jsonify({'error': 'Verification failed'}), 500

# Health check endpoint
@app.route('/api/health')
def health_check():
    logger.debug("🏥 Health check requested")
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if db else 'disconnected'
    })

if __name__ == '__main__':
    logger.info("🚀 Starting TikTok Downloader Server...")
    logger.info("📁 Serving static files from current directory")
    logger.info("🌐 User page available at: http://localhost:5000/")
    logger.info("🔧 Admin panel available at: http://localhost:5000/admin")
    logger.info("🔐 Login page available at: http://localhost:5000/login")
    logger.info(f"🔑 Default admin username: {ADMIN_USERNAME}")
    logger.info("📊 MongoDB collections initialized")
    app.run(debug=True, host='0.0.0.0', port=5000)