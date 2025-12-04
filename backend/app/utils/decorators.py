from functools import wraps
from flask import request, jsonify
from app.utils.jwt import verify_token, get_current_user
from app.utils.errors import APIError
from app.models.user import User

def token_required(f):
    """需要token认证的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                raise APIError('Token格式错误', 401, 'INVALID_TOKEN_FORMAT')
        
        if not token:
            raise APIError('缺少认证token', 401, 'MISSING_TOKEN')
        
        user = get_current_user(token)
        if not user:
            raise APIError('Token无效或已过期', 401, 'INVALID_TOKEN')
        
        request.current_user = user
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    """需要特定角色的装饰器"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.current_user.role not in roles:
                raise APIError('权限不足', 403, 'INSUFFICIENT_PERMISSIONS')
            return f(*args, **kwargs)
        return decorated
    return decorator

