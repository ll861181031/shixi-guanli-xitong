import jwt
from datetime import datetime, timedelta
from flask import current_app
from app.models.user import User

def generate_token(user_id, role):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'iat': datetime.utcnow()
    }
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm=current_app.config['JWT_ALGORITHM']
    )
    return token

def verify_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=[current_app.config['JWT_ALGORITHM']]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user(token):
    """根据token获取当前用户"""
    payload = verify_token(token)
    if not payload:
        return None
    user = User.query.get(payload.get('user_id'))
    return user

