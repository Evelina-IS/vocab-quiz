import json, os, requests
from flask import Blueprint, redirect, request, session, jsonify, current_app
from models import db, User, Progress

api = Blueprint('api', __name__)

# ---------- GitHub OAuth ----------
@api.route('/auth/github')
def github_login():
    client_id = current_app.config['GITHUB_CLIENT_ID']
    redirect_uri = 'https://' + request.host + '/api/auth/github/callback'
    return redirect(
        f'https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=read:user'
    )

@api.route('/auth/github/callback')
def github_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No code provided'}), 400

    # Exchange code for access token
    token_resp = requests.post(
        'https://github.com/login/oauth/access_token',
        json={
            'client_id': current_app.config['GITHUB_CLIENT_ID'],
            'client_secret': current_app.config['GITHUB_CLIENT_SECRET'],
            'code': code,
        },
        headers={'Accept': 'application/json'}
    )
    token_data = token_resp.json()
    access_token = token_data.get('access_token')
    if not access_token:
        return jsonify({'error': 'Failed to get access token'}), 400

    # Get user info
    user_resp = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    github_user = user_resp.json()
    gh_id = github_user['id']
    username = github_user['login']
    avatar_url = github_user.get('avatar_url', '')

    # Find or create user
    user = User.query.filter_by(github_id=gh_id).first()
    if not user:
        user = User(github_id=gh_id, username=username, avatar_url=avatar_url)
        db.session.add(user)
        db.session.commit()
    else:
        user.username = username
        user.avatar_url = avatar_url
        db.session.commit()

    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    session['avatar_url'] = user.avatar_url
    session.permanent = True

    # Redirect to frontend
    return redirect('/')

# ---------- Auth status ----------
@api.route('/auth/me')
def auth_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'logged_in': False}), 200
    user = User.query.get(user_id)
    if not user:
        return jsonify({'logged_in': False}), 200
    return jsonify({
        'logged_in': True,
        'username': user.username,
        'avatar_url': user.avatar_url,
        'github_id': user.github_id,
    })

@api.route('/auth/logout')
def logout():
    session.clear()
    return jsonify({'ok': True})

# ---------- Progress ----------
@api.route('/progress', methods=['GET'])
def get_progress():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    records = Progress.query.filter_by(user_id=user_id).all()
    data = {}
    for r in records:
        data[str(r.word_seq)] = {'status': r.status, 'count': r.count}
    return jsonify(data)

@api.route('/progress', methods=['POST'])
def save_progress():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    body = request.get_json()
    if not body or 'word_seq' not in body or 'status' not in body:
        return jsonify({'error': 'Invalid data'}), 400

    word_seq = body['word_seq']
    status = body['status']
    record = Progress.query.filter_by(user_id=user_id, word_seq=word_seq).first()
    if not record:
        record = Progress(user_id=user_id, word_seq=word_seq, status=status, count=1)
        db.session.add(record)
    else:
        record.status = status
        record.count = (record.count or 0) + 1
    db.session.commit()
    return jsonify({'ok': True})

@api.route('/progress/batch', methods=['POST'])
def batch_progress():
    """批量保存，每次默写完成后一次性提交"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    body = request.get_json()
    items = body.get('items', []) if body else []
    for item in items:
        word_seq = item.get('word_seq')
        status = item.get('status')
        if word_seq is None or not status:
            continue
        record = Progress.query.filter_by(user_id=user_id, word_seq=word_seq).first()
        if not record:
            record = Progress(user_id=user_id, word_seq=word_seq, status=status, count=1)
            db.session.add(record)
        else:
            record.status = status
            record.count = (record.count or 0) + 1
    db.session.commit()
    return jsonify({'ok': True})

@api.route('/progress/clear', methods=['POST'])
def clear_progress():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    Progress.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'ok': True})


@api.route('/admin/stats')
def admin_stats():
    """管理员统计 - 查看用户数据"""
    from models import User, Progress
    
    user_count = User.query.count()
    progress_count = Progress.query.count()
    users = User.query.all()
    
    user_list = []
    for u in users:
        correct = Progress.query.filter_by(user_id=u.id, status='correct').count()
        wrong = Progress.query.filter_by(user_id=u.id, status='wrong').count()
        user_list.append({
            'id': u.id,
            'github_id': u.github_id,
            'username': u.username,
            'created_at': str(u.created_at)[:19] if u.created_at else '',
            'correct': correct,
            'wrong': wrong,
            'total': correct + wrong,
        })
    
    return jsonify({
        'total_users': user_count,
        'total_progress_records': progress_count,
        'users': user_list,
    })


@api.route('/admin/progress')
def admin_progress():
    """导出所有用户的进度数据"""
    from models import User, Progress
    
    records = Progress.query.all()
    users = {u.id: u.username for u in User.query.all()}
    
    data = []
    for r in records:
        data.append({
            'id': r.id,
            'user_id': r.user_id,
            'username': users.get(r.user_id, 'unknown'),
            'word_seq': r.word_seq,
            'status': r.status,
            'count': r.count,
            'updated_at': str(r.updated_at)[:19] if r.updated_at else '',
        })
    
    return jsonify({
        'total_records': len(data),
        'records': data,
    })


@api.route('/admin')
def admin_page():
    """管理后台页面"""
    from models import User, Progress
    
    users = User.query.all()
    records = Progress.query.order_by(Progress.updated_at.desc()).limit(200).all()
    
    html = '<html><head><meta charset="utf-8"><title>管理后台</title>'
    html += '<style>body{font-family:sans-serif;padding:20px;max-width:1200px;margin:0 auto;}'
    html += 'table{border-collapse:collapse;width:100%;margin-top:10px;}'
    html += 'th,td{border:1px solid #ddd;padding:8px;text-align:left;}'
    html += 'th{background:#1a1a2e;color:#fff;}'
    html += 'tr:nth-child(even){background:#f9f9f9;}'
    html += '.correct{color:#27ae60;font-weight:bold;}'
    html += '.wrong{color:#e74c3c;font-weight:bold;}'
    html += 'h2{margin-top:30px;}</style></head><body>'
    
    html += f'<h1>📊 管理后台</h1>'
    html += f'<p>用户数: {len(users)} | 进度记录: {Progress.query.count()}</p>'
    
    # 用户表
    html += '<h2>👤 用户列表</h2>'
    html += '<table><tr><th>ID</th><th>GitHub ID</th><th>用户名</th><th>注册时间</th><th>正确</th><th>错误</th><th>总数</th></tr>'
    for u in users:
        correct = Progress.query.filter_by(user_id=u.id, status='correct').count()
        wrong = Progress.query.filter_by(user_id=u.id, status='wrong').count()
        html += f'<tr><td>{u.id}</td><td>{u.github_id}</td><td>{u.username}</td><td>{str(u.created_at)[:19]}</td>'
        html += f'<td class="correct">{correct}</td><td class="wrong">{wrong}</td><td>{correct+wrong}</td></tr>'
    html += '</table>'
    
    # 进度记录表
    html += '<h2>📝 进度记录（最近200条）</h2>'
    html += '<table><tr><th>ID</th><th>用户</th><th>单词序号</th><th>状态</th><th>次数</th><th>时间</th></tr>'
    
    # 加载单词表
    import json, os
    words_path = os.path.join(os.path.dirname(__file__), 'words.json')
    word_map = {}
    if os.path.exists(words_path):
        with open(words_path) as f:
            for w in json.load(f):
                word_map[w['seq']] = w['word']
    
    for r in records:
        user_name = User.query.get(r.user_id).username if User.query.get(r.user_id) else 'unknown'
        word_text = word_map.get(r.word_seq, str(r.word_seq))
        status_class = 'correct' if r.status == 'correct' else 'wrong'
        html += f'<tr><td>{r.id}</td><td>{user_name}</td><td>{word_text}</td>'
        html += f'<td class="{status_class}">{r.status}</td><td>{r.count}</td>'
        html += f'<td>{str(r.updated_at)[:19]}</td></tr>'
    html += '</table>'
    
    html += '</body></html>'
    return html
