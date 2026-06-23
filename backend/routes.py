import json, os, requests
from flask import Blueprint, redirect, request, session, jsonify, current_app
from models import db, User, Progress

api = Blueprint('api', __name__)

# ---------- GitHub OAuth ----------
@api.route('/auth/github')
def github_login():
    client_id = current_app.config['GITHUB_CLIENT_ID']
    redirect_uri = request.host_url.rstrip('/') + '/api/auth/github/callback'
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
