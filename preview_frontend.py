"""
Preview server for Frontend PHP pages — full admin CRUD simulation.
No PHP/MySQL required. Stores data in-memory for testing.
"""
import re
from datetime import datetime
from flask import Flask, send_from_directory, Response, request, jsonify, session
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'preview-secret-key-dev-only'
FRONTEND = Path(__file__).parent / 'Frontend'

# ── In-memory data stores ────────────────────────────────────
_next_id = {'emp': 2, 'client': 3, 'cid': 3, 'proj': 1}
_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

DB = {
    'employees': [
        {'id':1,'employee_code':'EMP-001','name':'John Doe','email':'john@example.com','status':'active','created_at':_now}
    ],
    'client_ids': [
        {'id':1,'client_id_code':'CLIENT-001','client_id_name':'ABC Corporation','status':'active','created_at':_now},
        {'id':2,'client_id_code':'CLIENT-002','client_id_name':'XYZ Industries','status':'active','created_at':_now}
    ],
    'clients': [
        {'id':1,'client_name':'Mr. ABC','email':'abc@example.com','client_id':1,'client_id_code':'CLIENT-001','client_id_name':'ABC Corporation','status':'active','created_at':_now},
        {'id':2,'client_name':'Ms. XYZ','email':'xyz@example.com','client_id':2,'client_id_code':'CLIENT-002','client_id_name':'XYZ Industries','status':'active','created_at':_now}
    ],
    'projects': []
}

TEST_USERS = {
    'admin':    {'email':'admin@example.com','password':'admin123','name':'Admin User','redirect':'/admin/dashboard.php'},
    'employee': {'email':'john@example.com','password':'employee123','name':'John Doe','redirect':'/employee/dashboard.php'},
    'client':   {'email':'abc@example.com','password':'client123','name':'Mr. ABC','redirect':'/client/dashboard.php'}
}

def strip_php(content):
    name = session.get('name', 'Test User')
    email = session.get('email', 'test@logicapt.com')
    content = re.sub(r'<\?php.*?\?>', '', content, flags=re.DOTALL)
    content = re.sub(r'<\?php[^>]*$', '', content, flags=re.MULTILINE)
    content = content.replace("<?php echo htmlspecialchars($_SESSION['name']); ?>", name)
    content = content.replace("<?php echo htmlspecialchars($_SESSION['email']); ?>", email)
    content = content.replace('<?php echo $project_id; ?>', '1')
    content = content.replace("<?php echo bin2hex(random_bytes(16)); ?>", 'preview_csrf')
    return content

def _get_field(key):
    return request.form.get(key) or (request.json or {}).get(key, '')

# ── Auth APIs ────────────────────────────────────────────────
@app.route('/api/auth/admin-login.php', methods=['POST'])
def admin_login(): return _handle_login('admin')
@app.route('/api/auth/employee-login.php', methods=['POST'])
def employee_login(): return _handle_login('employee')
@app.route('/api/auth/client-login.php', methods=['POST'])
def client_login(): return _handle_login('client')

def _handle_login(role):
    email, password = _get_field('email'), _get_field('password')
    u = TEST_USERS[role]
    if email == u['email'] and password == u['password']:
        session.update({'user_id':1, 'name':u['name'], 'email':u['email'], 'user_type':role})
        return jsonify({'success':True, 'message':'Login successful', 'redirect':u['redirect']})
    return jsonify({'success':False, 'message':'Invalid email or password'}), 401

@app.route('/api/auth/test-mode-check.php')
def test_mode_check(): return jsonify({'testModeAvailable': True})

@app.route('/api/auth/test-mode-login.php', methods=['POST'])
def test_mode_login():
    role = request.args.get('type', 'admin')
    u = TEST_USERS.get(role, TEST_USERS['admin'])
    session.update({'user_id':1, 'name':u['name']+' (Test)', 'email':u['email'], 'user_type':role})
    return jsonify({'success':True, 'user':{'id':1,'email':u['email'],'name':session['name'],'type':role,'testMode':True}})

@app.route('/api/auth/logout.php', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success':True, 'message':'Logged out'})

# ── Admin Dashboard API ──────────────────────────────────────
@app.route('/api/admin/dashboard.php')
def admin_dashboard():
    return jsonify({'success':True,
        'employeeCount': len(DB['employees']),
        'clientCount': len(DB['clients']),
        'activeProjectCount': len([p for p in DB['projects'] if p['status']=='active']),
        'inactiveProjectCount': len([p for p in DB['projects'] if p['status']!='active'])
    })

# ── Employee CRUD ────────────────────────────────────────────
@app.route('/api/admin/employees.php')
def list_employees():
    return jsonify({'success':True, 'employees': DB['employees']})

@app.route('/api/admin/create-employee.php', methods=['POST'])
def create_employee():
    name, email = _get_field('name'), _get_field('email')
    pwd, pwd2 = _get_field('password'), _get_field('password_confirm')
    if not name or not email or not pwd: return jsonify({'success':False,'message':'All fields required'}), 400
    if pwd != pwd2: return jsonify({'success':False,'message':'Passwords do not match'}), 400
    if any(e['email']==email for e in DB['employees']): return jsonify({'success':False,'message':'Email already exists'}), 400
    eid = _next_id['emp']; _next_id['emp'] += 1
    emp = {'id':eid,'employee_code':f'EMP-{eid:03d}','name':name,'email':email,'status':'active','created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    DB['employees'].append(emp)
    return jsonify({'success':True,'message':'Employee created successfully','employee':emp}), 201

# ── Client ID CRUD ───────────────────────────────────────────
@app.route('/api/admin/client-ids.php')
def list_client_ids():
    return jsonify({'success':True, 'client_ids': DB['client_ids']})

@app.route('/api/admin/create-client-id.php', methods=['POST'])
def create_client_id():
    code, name = _get_field('client_id_code'), _get_field('client_id_name')
    if not code or not name: return jsonify({'success':False,'message':'Code and name are required'}), 400
    if any(c['client_id_code']==code for c in DB['client_ids']): return jsonify({'success':False,'message':'Client ID code already exists'}), 400
    cid = _next_id['cid']; _next_id['cid'] += 1
    rec = {'id':cid,'client_id_code':code,'client_id_name':name,'status':'active','created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    DB['client_ids'].append(rec)
    return jsonify({'success':True,'message':'Client ID created successfully','data':rec}), 201

# ── Client User CRUD ─────────────────────────────────────────
@app.route('/api/admin/clients.php')
def list_clients():
    return jsonify({'success':True, 'clients': DB['clients']})

@app.route('/api/admin/create-client.php', methods=['POST'])
def create_client():
    cname, email = _get_field('client_name'), _get_field('email')
    pwd, pwd2 = _get_field('password'), _get_field('password_confirm')
    cid = int(_get_field('client_id') or 0)
    if not cname or not email or not pwd or not cid: return jsonify({'success':False,'message':'All fields required'}), 400
    if pwd != pwd2: return jsonify({'success':False,'message':'Passwords do not match'}), 400
    if any(c['email']==email for c in DB['clients']): return jsonify({'success':False,'message':'Email already exists'}), 400
    ci = next((c for c in DB['client_ids'] if c['id']==cid), None)
    if not ci: return jsonify({'success':False,'message':'Invalid Client ID'}), 400
    nid = _next_id['client']; _next_id['client'] += 1
    rec = {'id':nid,'client_name':cname,'email':email,'client_id':cid,'client_id_code':ci['client_id_code'],'client_id_name':ci['client_id_name'],'status':'active','created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    DB['clients'].append(rec)
    return jsonify({'success':True,'message':'Client created successfully','data':rec}), 201


# ── Projects API ─────────────────────────────────────────────
@app.route('/api/admin/projects.php')
def list_projects():
    return jsonify({'success':True, 'projects': DB['projects']})

# ── Page routes ──────────────────────────────────────────────
@app.route('/')
def index():
    php_file = FRONTEND / 'index.php'
    if php_file.exists():
        return Response(strip_php(php_file.read_text(encoding='utf-8')), mimetype='text/html')
    return 'index.php not found', 404

@app.route('/public/assets/<path:filename>')
def public_assets(filename):
    return send_from_directory(FRONTEND / 'public' / 'assets', filename)

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(FRONTEND / 'public' / 'assets', filename)

@app.route('/<path:filepath>')
def serve_php(filepath):
    # Skip API routes (already handled above)
    if filepath.startswith('api/'):
        return jsonify({'success':False,'message':'API endpoint not found'}), 404
    for base in [FRONTEND, FRONTEND / 'public']:
        target = base / filepath
        if not target.exists() and not filepath.endswith('.php'):
            target = base / (filepath + '.php')
        if target.exists() and target.is_file():
            if target.suffix == '.php':
                return Response(strip_php(target.read_text(encoding='utf-8')), mimetype='text/html')
            return send_from_directory(target.parent, target.name)
    return f'File not found: {filepath}', 404

if __name__ == '__main__':
    print('\n' + '='*60)
    print('  FRONTEND PREVIEW SERVER (full admin CRUD)')
    print('  http://localhost:8080')
    print('='*60)
    print('\n  Credentials:')
    print('    Admin:    admin@example.com / admin123')
    print('    Employee: john@example.com  / employee123')
    print('    Client:   abc@example.com   / client123')
    print('\n  Admin Pages:')
    print('    /public/admin/login.php       Login')
    print('    /public/admin/dashboard.php   Dashboard')
    print('    /public/admin/employees.php   Manage Employees')
    print('    /public/admin/clients.php     Manage Clients')
    print('    /public/admin/client-ids.php  Client IDs')
    print('    /public/admin/projects.php    All Projects')
    print()
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)