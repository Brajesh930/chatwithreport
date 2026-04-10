from flask import Flask, request, jsonify, send_from_directory, session, Response
from pathlib import Path
from datetime import datetime
import os
import sys
import re
import bcrypt

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from helpers.config import Config
from helpers.logger import Logger
from helpers.file_helper import FileHelper
from helpers.database import init_db, db_execute
from helpers.auth import authenticate, get_current_user
from services.file_upload_service import FileUploadService
from services.file_parser_service import FileParserService
from services.ai_service import AIService

# Init DB on startup
init_db()

# Initialize Flask app
app = Flask(__name__, static_folder='public', static_url_path='')

# Load configuration
Config.load()

# Initialize services
upload_service = FileUploadService()
parser_service = FileParserService()
ai_service = AIService()

# Keep track of current document
current_document = {
    'original_filename': None,
    'parsed_filename': None,
    'parsed_path': None,
    'file_info': None
}

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve main application"""
    return send_from_directory('public', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('public', filename)

@app.route('/api/upload', methods=['POST'])
def upload():
    """Handle file upload — always field name 'file', supports one or many"""
    Logger.info('Upload request received')

    # getlist returns ALL files sent with field name 'file' (works for 1 or many)
    all_files = [f for f in request.files.getlist('file') if f.filename != '']

    if not all_files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    # ── MULTIPLE FILES ──────────────────────────────────────────────────────────
    if len(all_files) > 1:
        combined_parts = []
        uploaded_names = []

        for file_obj in all_files:
            upload_result = upload_service.process(file_obj)
            if not upload_result['success']:
                return jsonify({'success': False, 'message': upload_result.get('error', 'Upload failed')}), 400

            try:
                parse_result = parser_service.parse(
                    upload_result['upload_path'],
                    upload_result['original_filename']
                )
            except Exception as e:
                Logger.error('File parsing failed', {'error': str(e)})
                return jsonify({'success': False, 'message': f"Failed to parse {file_obj.filename}: {str(e)}"}), 400

            if not parse_result['success']:
                return jsonify({'success': False, 'message': parse_result.get('error', 'Parse failed')}), 400

            with open(parse_result['parsed_path'], 'r', encoding='utf-8') as f:
                combined_parts.append(f.read())

            uploaded_names.append(upload_result['original_filename'])

        # Combine all parsed texts with a clear separator
        separator = '\n\n' + '=' * 80 + '\n\n'
        full_content = separator.join(combined_parts)

        combined_filename = f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}_parsed.txt"
        combined_path = parser_service.parsed_dir / combined_filename

        with open(combined_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        combined_original_name = f"{len(uploaded_names)} files: {', '.join(uploaded_names)}"
        current_document['original_filename'] = combined_original_name
        current_document['parsed_filename'] = combined_filename
        current_document['parsed_path'] = str(combined_path)
        current_document['file_info'] = {
            'original_filename': combined_original_name,
            'parser_used': 'Multi-file Parser'
        }

        Logger.info('Multiple files uploaded and combined', {'count': len(uploaded_names)})
        return jsonify({
            'success': True,
            'message': f'{len(uploaded_names)} files uploaded and combined successfully',
            'data': {
                'uploadedCount': len(uploaded_names),
                'originalFilenames': uploaded_names,
                'combinedParsedFilename': combined_filename
            }
        })

    # ── SINGLE FILE ─────────────────────────────────────────────────────────────
    file_obj = all_files[0]
    upload_result = upload_service.process(file_obj)
    if not upload_result['success']:
        return jsonify(upload_result), 400

    try:
        parse_result = parser_service.parse(
            upload_result['upload_path'],
            upload_result['original_filename']
        )
    except Exception as e:
        Logger.error('File parsing failed', {'error': str(e)})
        parse_result = {'success': False, 'error': f'Failed to parse file: {str(e)}'}

    if not parse_result['success']:
        return jsonify(parse_result), 400

    current_document['original_filename'] = parse_result['original_filename']
    current_document['parsed_filename'] = parse_result['parsed_filename']
    current_document['parsed_path'] = parse_result['parsed_path']
    current_document['file_info'] = {
        'original_filename': parse_result['original_filename'],
        'parser_used': parse_result['parser_used']
    }

    Logger.info('File upload and parse completed successfully')
    return jsonify({
        'success': True,
        'message': 'File uploaded and parsed successfully',
        'original_filename': parse_result['original_filename'],
        'parsed_filename': parse_result['parsed_filename'],
        'parser_used': parse_result['parser_used']
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat question"""
    data = request.get_json()
    
    if not data or 'question' not in data:
        return jsonify({'success': False, 'error': 'No question provided'}), 400

    question = data['question'].strip()
    
    if not question:
        return jsonify({'success': False, 'error': 'Question cannot be empty'}), 400

    # Check if document is loaded
    if not current_document['parsed_path']:
        return jsonify({'success': False, 'error': 'No document loaded. Please upload a file first.'}), 400

    try:
        # Read the complete document content every time
        with open(current_document['parsed_path'], 'r', encoding='utf-8') as f:
            document_content = f.read()

        # Build prompt with complete document content
        prompt = f"""Based on the following document, please answer the question:

DOCUMENT:
{document_content}

QUESTION: {question}

ANSWER:"""

        Logger.info('Processing chat question', {'question_length': len(question)})

        # Get AI response
        response = ai_service.ask_question(prompt)

        if not response['success']:
            return jsonify(response), 400

        return jsonify({
            'success': True,
            'answer': response['answer']
        })

    except Exception as e:
        Logger.error('Chat processing failed', {'error': str(e)})
        return jsonify({
            'success': False,
            'error': f'Failed to process question: {str(e)}'
        }), 400

@app.route('/api/file-info', methods=['GET'])
def file_info_endpoint():
    """Get current file information"""
    if not current_document['original_filename']:
        return jsonify({
            'success': False,
            'message': 'No file loaded',
            'data': {}
        })

    try:
        parsed_path = Path(current_document['parsed_path'])
        file_size = parsed_path.stat().st_size if parsed_path.exists() else 0
        
        file_info = {'uploaded': None, 'parsed': None}
        
        # Add uploaded file info
        file_info['uploaded'] = {
            'filename': current_document['original_filename'],
            'size': FileHelper.format_file_size(file_size),
            'extension': current_document['original_filename'].split('.')[-1].lower(),
            'uploadTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add parsed file info with content
        if parsed_path.exists():
            with open(parsed_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_info['parsed'] = {
                'filename': current_document['parsed_filename'],
                'size': FileHelper.format_file_size(file_size),
                'uploadTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'content': content
            }
        
        return jsonify({
            'success': True,
            'message': 'File info retrieved',
            'data': file_info
        })
    except Exception as e:
        Logger.error('Failed to get file info', {'error': str(e)})
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve file information',
            'data': {}
        }), 400

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the application"""
    global current_document
    current_document = {
        'original_filename': None,
        'parsed_filename': None,
        'parsed_path': None,
        'file_info': None
    }
    Logger.info('Application reset')
    return jsonify({'success': True, 'message': 'Application reset successfully'})

# =====================================================================
#  FRONTEND ADMIN PREVIEW — serves PHP pages as HTML with mock APIs
# =====================================================================
app.secret_key = 'logicapt-preview-dev-key'
FRONTEND = Path(__file__).parent / 'Frontend'

_next_id = {'emp': 2, 'client': 3, 'cid': 3, 'proj': 1}
_now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
MOCK_DB = {
    'employees': [{'id':1,'employee_code':'EMP-001','name':'John Doe','email':'john@example.com','status':'active','created_at':_now_str}],
    'client_ids': [
        {'id':1,'client_id_code':'CLIENT-001','client_id_name':'ABC Corporation','status':'active','created_at':_now_str},
        {'id':2,'client_id_code':'CLIENT-002','client_id_name':'XYZ Industries','status':'active','created_at':_now_str}
    ],
    'clients': [
        {'id':1,'client_name':'Mr. ABC','email':'abc@example.com','client_id':1,'client_id_code':'CLIENT-001','client_id_name':'ABC Corporation','status':'active','created_at':_now_str},
        {'id':2,'client_name':'Ms. XYZ','email':'xyz@example.com','client_id':2,'client_id_code':'CLIENT-002','client_id_name':'XYZ Industries','status':'active','created_at':_now_str}
    ],
    'projects': []
}
MOCK_USERS = {
    'admin':    {'email':'admin@example.com','password':'admin123','name':'Admin User','redirect':'/admin/dashboard.php'},
    'employee': {'email':'john@example.com','password':'employee123','name':'John Doe','redirect':'/employee/dashboard.php'},
    'client':   {'email':'abc@example.com','password':'client123','name':'Mr. ABC','redirect':'/client/dashboard.php'}
}

def _strip_php(content):
    name = session.get('name', 'Test User')
    email = session.get('email', 'test@logicapt.com')
    content = re.sub(r'<\?php.*?\?>', '', content, flags=re.DOTALL)
    content = re.sub(r'<\?php[^>]*$', '', content, flags=re.MULTILINE)
    content = content.replace("<?php echo htmlspecialchars($_SESSION['name']); ?>", name)
    content = content.replace("<?php echo htmlspecialchars($_SESSION['email']); ?>", email)
    content = content.replace('<?php echo $project_id; ?>', '1')
    content = content.replace("<?php echo bin2hex(random_bytes(16)); ?>", 'preview_csrf')
    return content

def _field(key):
    return request.form.get(key) or (request.json or {}).get(key, '')

# Auth
def _do_login(role):
    u = MOCK_USERS[role]
    e, p = _field('email'), _field('password')
    if e == u['email'] and p == u['password']:
        session.update({'user_id':1,'name':u['name'],'email':u['email'],'user_type':role})
        return jsonify({'success':True,'message':'Login successful','redirect':u['redirect']})
    return jsonify({'success':False,'message':'Invalid email or password'}), 401

@app.route('/api/auth/admin-login.php', methods=['POST'])
def fe_admin_login(): return _do_login('admin')
@app.route('/api/auth/employee-login.php', methods=['POST'])
def fe_emp_login(): return _do_login('employee')
@app.route('/api/auth/client-login.php', methods=['POST'])
def fe_client_login(): return _do_login('client')
@app.route('/api/auth/test-mode-check.php')
def fe_test_check(): return jsonify({'testModeAvailable': True})
@app.route('/api/auth/test-mode-login.php', methods=['POST'])
def fe_test_login():
    role = request.args.get('type','admin')
    u = MOCK_USERS.get(role, MOCK_USERS['admin'])
    session.update({'user_id':1,'name':u['name']+' (Test)','email':u['email'],'user_type':role})
    return jsonify({'success':True,'user':{'id':1,'email':u['email'],'name':session['name'],'type':role,'testMode':True}})
@app.route('/api/auth/logout.php', methods=['POST'])
def fe_logout():
    session.clear(); return jsonify({'success':True,'message':'Logged out'})

# Dashboard
@app.route('/api/admin/dashboard.php')
def fe_dashboard():
    if not require_role('admin'):
        return jsonify({'success':False,'message':'Unauthorized'}), 401
    
    employees = db_execute("SELECT COUNT(*) as count FROM employees WHERE status = 'active'", fetch=True)['count']
    clients = db_execute("SELECT COUNT(*) as count FROM clients WHERE status = 'active'", fetch=True)['count']
    active_projects = db_execute("SELECT COUNT(*) as count FROM projects WHERE status = 'active'", fetch=True)['count']
    
    return jsonify({
        'success': True,
        'employeeCount': employees,
        'clientCount': clients,
        'activeProjectCount': active_projects,
        'inactiveProjectCount': 0
    })

# Employees
@app.route('/api/admin/employees.php')
def fe_employees(): return jsonify({'success':True,'employees':MOCK_DB['employees']})
@app.route('/api/admin/create-employee.php', methods=['POST'])
def fe_create_emp():
    n, e, pw, pw2 = _field('name'), _field('email'), _field('password'), _field('password_confirm')
    if not n or not e or not pw: return jsonify({'success':False,'message':'All fields required'}), 400
    if pw != pw2: return jsonify({'success':False,'message':'Passwords do not match'}), 400
    if any(x['email']==e for x in MOCK_DB['employees']): return jsonify({'success':False,'message':'Email already exists'}), 400
    eid = _next_id['emp']; _next_id['emp'] += 1
    emp = {'id':eid,'employee_code':f'EMP-{eid:03d}','name':n,'email':e,'status':'active','created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    MOCK_DB['employees'].append(emp)
    return jsonify({'success':True,'message':'Employee created successfully','employee':emp}), 201

# Client IDs
@app.route('/api/admin/client-ids.php')
def fe_client_ids(): return jsonify({'success':True,'data':{'client_ids':MOCK_DB['client_ids']}})
@app.route('/api/admin/create-client-id.php', methods=['POST'])
def fe_create_cid():
    code, name = _field('client_id_code'), _field('client_id_name')
    if not code or not name: return jsonify({'success':False,'message':'Code and name are required'}), 400
    if any(c['client_id_code']==code for c in MOCK_DB['client_ids']): return jsonify({'success':False,'message':'Code already exists'}), 400
    cid = _next_id['cid']; _next_id['cid'] += 1
    rec = {'id':cid,'client_id_code':code,'client_id_name':name,'status':'active','created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    MOCK_DB['client_ids'].append(rec)
    return jsonify({'success':True,'message':'Client ID created','data':rec}), 201

# Clients
@app.route('/api/admin/clients.php')
def fe_clients(): return jsonify({'success':True,'clients':MOCK_DB['clients']})
@app.route('/api/admin/create-client.php', methods=['POST'])
def fe_create_client():
    cn, e, pw, pw2, cid = _field('client_name'), _field('email'), _field('password'), _field('password_confirm'), int(_field('client_id') or 0)
    if not cn or not e or not pw or not cid: return jsonify({'success':False,'message':'All fields required'}), 400
    if pw != pw2: return jsonify({'success':False,'message':'Passwords do not match'}), 400
    if any(c['email']==e for c in MOCK_DB['clients']): return jsonify({'success':False,'message':'Email already exists'}), 400
    ci = next((c for c in MOCK_DB['client_ids'] if c['id']==cid), None)
    if not ci: return jsonify({'success':False,'message':'Invalid Client ID'}), 400
    nid = _next_id['client']; _next_id['client'] += 1
    rec = {'id':nid,'client_name':cn,'email':e,'client_id':cid,'client_id_code':ci['client_id_code'],'client_id_name':ci['client_id_name'],'status':'active','created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    MOCK_DB['clients'].append(rec)
    return jsonify({'success':True,'message':'Client created','data':rec}), 201

# Projects
@app.route('/api/admin/projects.php')
def fe_projects(): return jsonify({'success':True,'projects':MOCK_DB['projects']})

# Employee Endpoints
@app.route('/api/employee/dashboard.php')
def fe_emp_dashboard():
    emp_projects = [p for p in MOCK_DB['projects'] if p.get('employee_id')==1]
    return jsonify({'success':True,'data':{'projectCount':len(emp_projects),'activeProjects':len([p for p in emp_projects if p.get('status')=='active'])}})

@app.route('/api/employee/projects.php')
def fe_emp_projects():
    emp_projects = [p for p in MOCK_DB['projects'] if p.get('employee_id')==1]
    return jsonify({'success':True,'data':{'projects':emp_projects}})

@app.route('/api/employee/create-project.php', methods=['POST'])
def fe_emp_create_project():
    proj_name, proj_desc, client_id = _field('project_name'), _field('project_description'), int(_field('client_id') or 0)
    if not proj_name or not client_id: return jsonify({'success':False,'message':'Project name and client ID are required'}), 400
    ci = next((c for c in MOCK_DB['client_ids'] if c['id']==client_id), None)
    if not ci: return jsonify({'success':False,'message':'Invalid Client ID'}), 400
    pid = _next_id['proj']; _next_id['proj'] += 1
    proj = {'id':pid,'project_name':proj_name,'project_description':proj_desc,'employee_id':1,'client_id':client_id,'client_id_code':ci['client_id_code'],'client_id_name':ci['client_id_name'],'status':'active','created_at':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    MOCK_DB['projects'].append(proj)
    return jsonify({'success':True,'message':'Project created successfully','data':proj}), 201

# Frontend page serving
@app.route('/portal')
def portal():
    return send_from_directory('portal', 'index.html')

@app.route('/portal/<path:filename>')
def portal_static(filename):
    return send_from_directory('portal', filename)

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    Logger.error('Internal server error', {'error': str(error)})
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.before_request
def before_request():
    Logger.debug(f'Incoming request: {request.method} {request.path}')

# ==================== MAIN ====================

if __name__ == '__main__':
    Logger.info(f'Starting Document Chat System - {Config.get("APP_ENV")} environment')
    Logger.info('Frontend admin pages at: http://localhost:8000/frontend')
    Logger.info('  Admin login:    http://localhost:8000/admin/login.php')
    Logger.info('  Employee login: http://localhost:8000/employee/login.php')
    Logger.info('  Client login:   http://localhost:8000/client/login.php')
    app.run(
        host='localhost',
        port=8000,
        debug=Config.get('APP_ENV') == 'development',
        use_reloader=False
    )
