# app.py
import asyncio
import json
import logging
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
from datetime import datetime
import hashlib

from config import SECRET_KEY, DEBUG, PORT, ADMIN_USERNAME, ADMIN_PASSWORD
from database import *
from telegram_client import add_account_async, fetch_groups_async, send_post_to_groups_async

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = '/tmp/flask_session'  # مهم لـ Railway
Session(app)

# تهيئة قاعدة البيانات
init_db()

# ========== دوال مساعدة ==========
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return get_user(session['user_id'])
    return None

# ========== الصفحات ==========

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed = hash_password(password)
        
        user = get_user_by_username(username)
        if user and user['password'] == hashed:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('تم تسجيل الدخول بنجاح', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        
        if password != confirm:
            flash('كلمة المرور غير متطابقة', 'danger')
            return render_template('register.html')
        
        if get_user_by_username(username):
            flash('اسم المستخدم موجود مسبقاً', 'danger')
            return render_template('register.html')
        
        hashed = hash_password(password)
        create_user(username, hashed)
        flash('تم التسجيل بنجاح، يمكنك تسجيل الدخول الآن', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج', 'info')
    return redirect(url_for('index'))

# ========== لوحة التحكم ==========
@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    accounts = get_telegram_accounts(user['id'])
    posts = get_posts(user['id'])
    campaigns = get_campaigns(user['id'])
    schedules = get_schedules(user['id'])
    settings = get_publish_settings(user['id'])
    
    return render_template('dashboard.html', 
                         user=user,
                         accounts=accounts,
                         posts=posts,
                         campaigns=campaigns,
                         schedules=schedules,
                         settings=settings)

# ========== إدارة الحسابات ==========
@app.route('/accounts')
@login_required
def accounts():
    user = get_current_user()
    accs = get_telegram_accounts(user['id'])
    return render_template('accounts.html', accounts=accs)

@app.route('/add_account', methods=['POST'])
@login_required
def add_account():
    user = get_current_user()
    phone = request.form.get('phone')
    code = request.form.get('code')
    password = request.form.get('password')
    
    success, result = asyncio.run(add_account_async('', phone, code, password))
    
    if success:
        session_str = result
        add_telegram_account(user['id'], session_str, phone)
        flash('تم إضافة الحساب بنجاح', 'success')
    else:
        flash(f'خطأ: {result}', 'danger')
    
    return redirect(url_for('accounts'))

@app.route('/fetch_groups/<int:account_id>')
@login_required
def fetch_groups(account_id):
    user = get_current_user()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT session FROM telegram_accounts WHERE id = ? AND user_id = ?", (account_id, user['id']))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        flash('الحساب غير موجود', 'danger')
        return redirect(url_for('accounts'))
    
    groups = asyncio.run(fetch_groups_async(row['session'], user['id'], account_id))
    flash(f'تم جلب {len(groups)} مجموعة بنجاح', 'success')
    return redirect(url_for('accounts'))

@app.route('/set_active/<int:account_id>')
@login_required
def set_active(account_id):
    user = get_current_user()
    set_active_account(user['id'], account_id)
    flash('تم تفعيل الحساب', 'success')
    return redirect(url_for('accounts'))

@app.route('/delete_account/<int:account_id>')
@login_required
def delete_account_route(account_id):
    user = get_current_user()
    delete_account(user['id'], account_id)
    flash('تم حذف الحساب', 'success')
    return redirect(url_for('accounts'))

# ========== إدارة المنشورات ==========
@app.route('/posts')
@login_required
def posts():
    user = get_current_user()
    post_list = get_posts(user['id'])
    return render_template('posts.html', posts=post_list)

@app.route('/add_post', methods=['POST'])
@login_required
def add_post_route():
    user = get_current_user()
    content = request.form.get('content')
    if not content:
        flash('الرجاء إدخال نص المنشور', 'danger')
        return redirect(url_for('posts'))
    
    create_post(user['id'], content)
    flash('تم إضافة المنشور بنجاح', 'success')
    return redirect(url_for('posts'))

@app.route('/delete_post/<int:post_id>')
@login_required
def delete_post_route(post_id):
    user = get_current_user()
    delete_post(user['id'], post_id)
    flash('تم حذف المنشور', 'success')
    return redirect(url_for('posts'))

# ========== إدارة المجموعات ==========
@app.route('/groups')
@login_required
def groups():
    user = get_current_user()
    acc = get_active_account(user['id'])
    groups_list = []
    if acc:
        groups_list = get_cached_groups(user['id'], acc['id'])
    return render_template('groups.html', groups=groups_list, account=acc)

# ========== الجدولة ==========
@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    user = get_current_user()
    if request.method == 'POST':
        account_id = request.form.get('account_id')
        scheduled_time = request.form.get('scheduled_time')
        if account_id and scheduled_time:
            dt = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
            add_schedule(user['id'], int(account_id), dt)
            flash('تم جدولة النشر بنجاح', 'success')
        else:
            flash('الرجاء ملء جميع الحقول', 'danger')
        return redirect(url_for('schedule'))
    
    accounts = get_telegram_accounts(user['id'])
    schedules = get_schedules(user['id'])
    return render_template('schedule.html', accounts=accounts, schedules=schedules)

@app.route('/cancel_schedule/<int:schedule_id>')
@login_required
def cancel_schedule_route(schedule_id):
    cancel_schedule(schedule_id)
    flash('تم إلغاء الجدولة', 'success')
    return redirect(url_for('schedule'))

# ========== الحملات ==========
@app.route('/campaigns')
@login_required
def campaigns():
    user = get_current_user()
    camp_list = get_campaigns(user['id'])
    posts_list = get_posts(user['id'])
    accounts_list = get_telegram_accounts(user['id'])
    return render_template('campaigns.html', campaigns=camp_list, posts=posts_list, accounts=accounts_list)

@app.route('/add_campaign', methods=['POST'])
@login_required
def add_campaign():
    user = get_current_user()
    name = request.form.get('name')
    post_ids = request.form.getlist('post_ids')
    account_ids = request.form.getlist('account_ids')
    
    if not name or not post_ids or not account_ids:
        flash('الرجاء ملء جميع الحقول', 'danger')
        return redirect(url_for('campaigns'))
    
    post_ids = [int(x) for x in post_ids]
    account_ids = [int(x) for x in account_ids]
    create_campaign(user['id'], name, post_ids, account_ids)
    flash('تم إنشاء الحملة بنجاح', 'success')
    return redirect(url_for('campaigns'))

@app.route('/delete_campaign/<int:campaign_id>')
@login_required
def delete_campaign_route(campaign_id):
    delete_campaign(campaign_id)
    flash('تم حذف الحملة', 'success')
    return redirect(url_for('campaigns'))

# ========== تشغيل النشر ==========
@app.route('/run_campaign/<int:campaign_id>')
@login_required
def run_campaign(campaign_id):
    user = get_current_user()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaigns WHERE id = ? AND user_id = ?", (campaign_id, user['id']))
    campaign = cursor.fetchone()
    conn.close()
    
    if not campaign:
        flash('الحملة غير موجودة', 'danger')
        return redirect(url_for('campaigns'))
    
    post_ids = json.loads(campaign['post_ids'])
    account_ids = json.loads(campaign['account_ids'])
    
    # جلب المنشورات
    posts = []
    for pid in post_ids:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = ? AND user_id = ?", (pid, user['id']))
        post = cursor.fetchone()
        conn.close()
        if post:
            posts.append(post)
    
    if not posts:
        flash('لا توجد منشورات في الحملة', 'danger')
        return redirect(url_for('campaigns'))
    
    # جلب الحسابات
    accounts = []
    for aid in account_ids:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM telegram_accounts WHERE id = ? AND user_id = ?", (aid, user['id']))
        acc = cursor.fetchone()
        conn.close()
        if acc:
            accounts.append(acc)
    
    if not accounts:
        flash('لا توجد حسابات في الحملة', 'danger')
        return redirect(url_for('campaigns'))
    
    # تنفيذ النشر
    results = []
    for acc in accounts:
        for post in posts:
            groups = get_cached_groups(user['id'], acc['id'])
            group_ids = [g['group_id'] for g in groups]
            if group_ids:
                res = asyncio.run(send_post_to_groups_async(acc['session'], user['id'], acc['id'], post['id'], post['content'], group_ids))
                results.extend(res)
    
    flash(f'تم نشر المنشورات بنجاح ({len(results)} عملية)', 'success')
    return redirect(url_for('campaigns'))

# ========== الإعدادات ==========
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user = get_current_user()
    if request.method == 'POST':
        delay = request.form.get('delay', 5)
        try:
            delay = int(delay)
            set_publish_settings(user['id'], delay)
            flash('تم حفظ الإعدادات', 'success')
        except:
            flash('قيمة غير صحيحة', 'danger')
        return redirect(url_for('settings'))
    
    settings_value = get_publish_settings(user['id'])
    return render_template('settings.html', settings=settings_value)

# ========== تشغيل التطبيق ==========
if __name__ == '__main__':
    # استخدام PORT من متغيرات البيئة (مهم لـ Railway)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
