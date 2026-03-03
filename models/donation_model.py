import mysql.connector
from Config import db_config
from db.database import execute_query, get_db_connection
from models.pickup_recommender import should_recommend_pickup  # ✅ used in logic

# 🔍 All Donations + Donor Info
def get_all_donations():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT d.id, d.title, d.description, d.location, d.quantity,
               d.predicted_category, d.image_filename, d.created_at,
               d.pickup_required, d.pickup_time, d.pickup_status,
               d.claimed_by, d.claimed_at,
               u.name AS user_name
        FROM donations d
        LEFT JOIN users u ON d.user_id = u.id
        ORDER BY d.created_at DESC
    """)
    donations = cur.fetchall()
    cur.close()
    conn.close()

    for d in donations:
        d['pickup_status'] = d.get('pickup_status') or 'Pending'
        d['pickup_recommended'] = should_recommend_pickup(
            d['quantity'], d['predicted_category'], d['description']
        )
    print(f"📦 Donations fetched: {len(donations)}")
    return donations

# 📊 Category Stats for Filters
def get_category_stats():
    query = """
        SELECT predicted_category, COUNT(*) as count
        FROM donations
        GROUP BY predicted_category
    """
    result = execute_query(query)
    return {
        row['predicted_category'] or "Uncategorized": row['count']
        for row in result
    }

# 💾 Save Donation
# def save_donation(user_id, title, description, location, quantity,
#                   predicted_category, image_filename,
#                   pickup_required=False, pickup_time=None, pickup_status=None):
#     try:
#         conn = mysql.connector.connect(**db_config)
#         cur = conn.cursor()
#         cur.execute("""
#             INSERT INTO donations (
#                 user_id, title, description, location, quantity,
#                 predicted_category, image_filename,
#                 pickup_required, pickup_time, pickup_status
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """, (
#             user_id, title, description, location, quantity,
#             predicted_category, image_filename,
#             pickup_required, pickup_time, pickup_status
#         ))
#         conn.commit()
#         print("✅ Donation saved.")
#     except Exception as e:
#         print("❌ Donation insert failed:", e)
#     finally:
#         cur.close()
#         conn.close()
def save_donation(user_id, title, description, location, quantity,
                  predicted_category, image_filename,
                  pickup_required=False, pickup_time=None, pickup_status=None):
    conn = None
    cur = None
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()

        # Ensure safe defaults
        if pickup_status is None:
            pickup_status = 'pending'
        if predicted_category is None:
            predicted_category = ''
        if image_filename is None:
            image_filename = ''

        cur.execute("""
            INSERT INTO donations (
                user_id, title, description, location, quantity,
                predicted_category, image_filename,
                pickup_required, pickup_time, pickup_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, title, description, location, quantity,
            predicted_category, image_filename,
            pickup_required, pickup_time, pickup_status
        ))

        conn.commit()
        print("✅ Donation saved.")
    except Exception as e:
        print("❌ Donation insert failed:", e)

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


# 🛠 Update Pickup Status
def update_pickup_status(donation_id, status):
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        cur.execute("""
            UPDATE donations SET pickup_status = %s WHERE id = %s
        """, (status, donation_id))
        conn.commit()
        print(f"✅ Pickup status updated to '{status}' for donation ID: {donation_id}")
    except Exception as e:
        print("❌ Pickup status update failed:", e)
    finally:
        cur.close()
        conn.close()

# 📥 Unclaimed Donations
def get_unclaimed_donations():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT d.*, u.name AS user_name
        FROM donations d
        LEFT JOIN users u ON d.user_id = u.id
        WHERE claimed_by IS NULL
        ORDER BY d.created_at DESC
    """)
    records = cur.fetchall()
    cur.close()
    conn.close()

    for d in records:
        d['pickup_status'] = d.get('pickup_status') or 'Pending'
        d['pickup_recommended'] = should_recommend_pickup(
            d['quantity'], d['predicted_category'], d['description']
        )
    return records

# ✅ Claimed Donations by NGO
def get_claimed_donations(ngo_id):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT d.*, dc.claimed_at, dc.pickup_time, dc.pickup_notes,
               n.org_name AS claimed_by_name,
               u.name AS user_name
        FROM donation_claims dc
        JOIN donations d ON dc.donation_id = d.id
        LEFT JOIN ngos n ON dc.ngo_id = n.id
        LEFT JOIN users u ON d.user_id = u.id
        WHERE dc.ngo_id = %s
        ORDER BY dc.claimed_at DESC
    """, (ngo_id,))
    claimed = cur.fetchall()
    cur.close()
    conn.close()

    for d in claimed:
        d['pickup_status'] = d.get('pickup_status') or 'Pending'
        d['pickup_recommended'] = should_recommend_pickup(
            d['quantity'], d['predicted_category'], d['description']
        )
    return claimed

# 📍 Mark Donation as Claimed
def mark_donation_claimed(donation_id, ngo_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        cur.execute("""
            UPDATE donations
            SET claimed_by = %s, claimed_at = NOW()
            WHERE id = %s
        """, (ngo_id, donation_id))
        conn.commit()
        print(f"📥 Donation {donation_id} marked as claimed by NGO {ngo_id}")
    except Exception as e:
        print("❌ Claim marking failed:", e)
    finally:
        cur.close()
        conn.close()

def mark_donation_fulfilled(donation_id):
    """Mark a donation as finally completed/delivered."""
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        # Update donation status
        cur.execute("UPDATE donations SET pickup_status = 'Fulfilled' WHERE id = %s", (donation_id,))
        # Update claim status
        cur.execute("UPDATE donation_claims SET status = 'Fulfilled' WHERE donation_id = %s", (donation_id,))
        conn.commit()
        print(f"🎉 Donation {donation_id} marked as FULFILLED.")
    except Exception as e:
        print("❌ Fulfillment update failed:", e)
    finally:
        cur.close()
        conn.close()

def mark_donation_dispatched(donation_id):
    """Mark a donation as currently being picked up (on the way)."""
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        # Update donation status
        cur.execute("UPDATE donations SET pickup_status = 'Dispatched' WHERE id = %s", (donation_id,))
        # Update claim status
        cur.execute("UPDATE donation_claims SET status = 'Dispatched' WHERE donation_id = %s", (donation_id,))
        conn.commit()
        print(f"🚚 Donation {donation_id} is now DISPATCHED (On the Way).")
    except Exception as e:
        print("❌ Dispatch update failed:", e)
    finally:
        cur.close()
        conn.close()

# 📧 Get Donor Info by Donation — used for notifications
def get_donor_by_donation_id(donation_id):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.id, u.name, u.email, d.title as donation_title
        FROM donations d
        LEFT JOIN users u ON d.user_id = u.id
        WHERE d.id = %s
    """, (donation_id,))
    donor = cur.fetchone()
    cur.close()
    conn.close()
    return donor

# 🔍 Single Donation by ID
def get_donation_by_id(donation_id):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM donations WHERE id = %s", (donation_id,))
    donation = cur.fetchone()
    cur.close()
    conn.close()
    return donation

# 📊 GLOBAL IMPACT STATS
def get_impact_stats():
    """Returns total items shared across the platform."""
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT SUM(quantity) as total_items, COUNT(*) as donation_count FROM donations")
    stats = cur.fetchone()
    cur.close()
    conn.close()
    return stats or {'total_items': 0, 'donation_count': 0}

# 🏆 LEADERBOARD: TOP 5 DONORS
def get_top_donors():
    """Ranks users by their total contribution (Fulfilled donations)."""
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT u.name, SUM(d.quantity) as total_qty, COUNT(d.id) as count
        FROM donations d
        JOIN users u ON d.user_id = u.id
        WHERE d.pickup_status = 'Fulfilled'
        GROUP BY u.id
        ORDER BY total_qty DESC
        LIMIT 5
    """)
    top_donors = cur.fetchall()
    cur.close()
    conn.close()
    return top_donors

# 📍 MAP DATA: RECENT ACTIVITY
def get_recent_map_data():
    """Fetches locations of active/recent donations for the map."""
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT title, location, predicted_category as category, pickup_status as status
        FROM donations
        WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
        ORDER BY created_at DESC
        LIMIT 15
    """)
    map_data = cur.fetchall()
    cur.close()
    conn.close()
    return map_data

# 👤 DONOR PROFILE STATS
def get_donor_profile_stats(user_id):
    """Returns comprehensive stats for a single donor's impact profile."""
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)

    # Total donations and items
    cur.execute("""
        SELECT COUNT(*) as total_donations, COALESCE(SUM(quantity), 0) as total_items
        FROM donations WHERE user_id = %s
    """, (user_id,))
    totals = cur.fetchone()

    # By status
    cur.execute("""
        SELECT pickup_status, COUNT(*) as count
        FROM donations WHERE user_id = %s
        GROUP BY pickup_status
    """, (user_id,))
    by_status = {row['pickup_status']: row['count'] for row in cur.fetchall()}

    # By category (for chart)
    cur.execute("""
        SELECT predicted_category as category, COUNT(*) as count, COALESCE(SUM(quantity),0) as qty
        FROM donations WHERE user_id = %s
        GROUP BY predicted_category ORDER BY count DESC
    """, (user_id,))
    by_category = cur.fetchall()

    # Monthly trend (last 6 months)
    cur.execute("""
        SELECT MIN(DATE_FORMAT(created_at, '%b %Y')) as month,
               COUNT(*) as count
        FROM donations
        WHERE user_id = %s AND created_at > DATE_SUB(NOW(), INTERVAL 6 MONTH)
        GROUP BY DATE_FORMAT(created_at, '%Y-%m')
        ORDER BY MIN(created_at) ASC
    """, (user_id,))
    monthly = cur.fetchall()

    cur.close()
    conn.close()

    return {
        'total_donations': totals['total_donations'],
        'total_items': int(totals['total_items']),
        'fulfilled': by_status.get('Fulfilled', 0),
        'dispatched': by_status.get('Dispatched', 0),
        'pending': by_status.get('Pending', 0),
        'by_category': by_category,
        'monthly': monthly,
    }

# 🏅 DONOR BADGES
def get_donor_badges(stats):
    """Awards badges based on the donor's stats. Returns list of earned badges."""
    badges = []
    total = stats['total_items']
    fulfilled = stats['fulfilled']
    donations = stats['total_donations']
    cats = [c['category'] for c in stats['by_category']]

    if total >= 1:
        badges.append({'icon': '🌱', 'title': 'First Step', 'desc': 'Made your first donation', 'color': '#10b981'})
    if total >= 10:
        badges.append({'icon': '⭐', 'title': 'Rising Star', 'desc': '10+ items donated', 'color': '#f59e0b'})
    if total >= 50:
        badges.append({'icon': '🔥', 'title': 'On Fire', 'desc': '50+ items donated', 'color': '#ef4444'})
    if total >= 100:
        badges.append({'icon': '💎', 'title': 'Diamond Donor', 'desc': '100+ items shared', 'color': '#6366f1'})
    if fulfilled >= 1:
        badges.append({'icon': '✅', 'title': 'Mission Complete', 'desc': 'First item fully delivered', 'color': '#10b981'})
    if fulfilled >= 5:
        badges.append({'icon': '🎯', 'title': 'Impact Maker', 'desc': '5+ deliveries verified', 'color': '#2563eb'})
    if 'Food' in cats:
        badges.append({'icon': '🍱', 'title': 'Food Hero', 'desc': 'Donated food items', 'color': '#f59e0b'})
    if 'Books' in cats:
        badges.append({'icon': '📚', 'title': 'Knowledge Giver', 'desc': 'Donated books', 'color': '#8b5cf6'})
    if 'Medical' in cats:
        badges.append({'icon': '🏥', 'title': 'Health Guardian', 'desc': 'Donated medical supplies', 'color': '#ef4444'})
    if donations >= 5:
        badges.append({'icon': '🤝', 'title': 'Community Pillar', 'desc': '5+ separate donations', 'color': '#06b6d4'})

    return badges

# 📡 LIVE ACTIVITY FEED
def get_live_activity_feed(limit=10):
    """Returns a real-time stream of recent platform events for the activity ticker."""
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT 
            d.title,
            d.predicted_category as category,
            d.pickup_status as status,
            d.created_at,
            u.name as donor_name,
            n.org_name as ngo_name,
            dc.claimed_at
        FROM donations d
        LEFT JOIN users u ON d.user_id = u.id
        LEFT JOIN donation_claims dc ON d.id = dc.donation_id
        LEFT JOIN ngos n ON dc.ngo_id = n.id
        ORDER BY GREATEST(d.created_at, COALESCE(dc.claimed_at, d.created_at)) DESC
        LIMIT %s
    """, (limit,))
    feed = cur.fetchall()
    cur.close()
    conn.close()

    # Convert to human-readable events
    events = []
    for item in feed:
        if item['status'] == 'Fulfilled':
            events.append({
                'icon': '🎉',
                'text': f"<b>{item['donor_name']}</b>'s {item['title']} was delivered!",
                'tag': 'Fulfilled',
                'color': '#10b981',
                'time': item['claimed_at'] or item['created_at']
            })
        elif item['status'] == 'Dispatched':
            events.append({
                'icon': '🚚',
                'text': f"<b>{item['ngo_name'] or 'An NGO'}</b> is on the way to pick up {item['title']}",
                'tag': 'En Route',
                'color': '#2563eb',
                'time': item['claimed_at'] or item['created_at']
            })
        elif item['ngo_name']:
            events.append({
                'icon': '📥',
                'text': f"<b>{item['ngo_name']}</b> claimed <b>{item['title']}</b>",
                'tag': 'Claimed',
                'color': '#6366f1',
                'time': item['claimed_at'] or item['created_at']
            })
        else:
            events.append({
                'icon': '❤️',
                'text': f"<b>{item['donor_name']}</b> donated {item['title']} ({item['category']})",
                'tag': 'New Donation',
                'color': '#f43f5e',
                'time': item['created_at']
            })
    return events

# 🔔 USER NOTIFICATIONS (derived from donation state changes)
def get_user_notifications(user_id):
    """Derives unread-style notifications from a user's donation activity."""
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT
            d.id,
            d.title,
            d.pickup_status,
            d.created_at,
            dc.claimed_at,
            n.org_name
        FROM donations d
        LEFT JOIN donation_claims dc ON d.id = dc.donation_id
        LEFT JOIN ngos n ON dc.ngo_id = n.id
        WHERE d.user_id = %s
          AND (
                dc.claimed_at IS NOT NULL
                OR d.pickup_status IN ('Dispatched', 'Fulfilled')
          )
        ORDER BY COALESCE(dc.claimed_at, d.created_at) DESC
        LIMIT 8
    """, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    notifications = []
    for row in rows:
        if row['pickup_status'] == 'Fulfilled':
            notifications.append({
                'icon': '🎉',
                'title': 'Delivery Confirmed!',
                'body': f"Your <b>{row['title']}</b> was successfully delivered.",
                'color': '#10b981',
                'donation_id': row['id'],
                'time': str(row['claimed_at'] or row['created_at'])
            })
        elif row['pickup_status'] == 'Dispatched':
            notifications.append({
                'icon': '🚚',
                'title': 'On The Way!',
                'body': f"<b>{row['org_name'] or 'An NGO'}</b> is picking up your <b>{row['title']}</b>.",
                'color': '#2563eb',
                'donation_id': row['id'],
                'time': str(row['claimed_at'] or row['created_at'])
            })
        elif row['org_name']:
            notifications.append({
                'icon': '📥',
                'title': 'Donation Claimed!',
                'body': f"<b>{row['org_name']}</b> has claimed your <b>{row['title']}</b>.",
                'color': '#6366f1',
                'donation_id': row['id'],
                'time': str(row['claimed_at'] or row['created_at'])
            })
    return notifications
