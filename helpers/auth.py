import bcrypt
from helpers.database import db_execute

USERS_TABLES = {
    'admin': 'admins',
    'employee': 'employees',
    'client': 'clients'
}

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def authenticate(email, password, role):
    table = USERS_TABLES.get(role)
    if not table:
        return False, 'Invalid role'
    
    user = db_execute(
        f"SELECT id, name, email, password_hash FROM {table} WHERE email = ? AND status = 'active'",
        (email,),
        fetch=True
    )
    
    if not user or not verify_password(password, user['password_hash']):
        return False, 'Invalid credentials'
    
    return True, user

def get_current_user():
    user_id = session.get('user_id')
    user_type = session.get('user_type')
    if not user_id or not user_type:
        return None
    
    table = USERS_TABLES.get(user_type)
    if not table:
        return None
    
    user = db_execute(
        f"SELECT id, name, email FROM {table} WHERE id = ?",
        (user_id,),
        fetch=True
    )
    if user:
        user['type'] = user_type
    return user

def require_role(role):
    user = get_current_user()
    if not user or user['type'] != role:
        return False
    return True

