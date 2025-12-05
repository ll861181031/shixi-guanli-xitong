from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.models.message import Message
from app.utils.jwt import generate_token
from app.utils.decorators import token_required
from app.utils.errors import APIError
from app.utils.validators import validate_student_id, validate_required
import requests
import logging
import json
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """管理员/教师登录"""
    try:
        data = _load_request_data()
        validate_required(data, ['username', 'password'])
        
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            raise APIError('用户名或密码错误', 401, 'INVALID_CREDENTIALS')
        
        if user.role not in ['admin', 'teacher']:
            raise APIError('该账号无权访问管理端', 403, 'INSUFFICIENT_PERMISSIONS')
        
        if user.status == 0:
            raise APIError('账号已被禁用', 403, 'USER_DISABLED')
        
        if user.status == 0:
            raise APIError('账号已被禁用', 403, 'USER_DISABLED')
        
        token = generate_token(user.id, user.role)
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise APIError('登录失败', 500)

@auth_bp.route('/wx-login', methods=['POST'])
def wx_login():
    """微信小程序登录"""
    try:
        data = request.get_json()
        validate_required(data, ['code'])
        
        code = data.get('code')
        student_id = data.get('student_id')  # 可选，用于绑定学号
        
        # 调用微信API获取openid
        from flask import current_app
        appid = current_app.config.get('WX_APPID')
        secret = current_app.config.get('WX_SECRET')
        
        if not appid or not secret:
            # 开发环境，使用模拟openid
            openid = f"mock_openid_{code}"
        else:
            # 生产环境，调用微信API
            url = f"https://api.weixin.qq.com/sns/jscode2session"
            params = {
                'appid': appid,
                'secret': secret,
                'js_code': code,
                'grant_type': 'authorization_code'
            }
            response = requests.get(url, params=params)
            result = response.json()
            
            if 'errcode' in result:
                raise APIError('微信登录失败', 401, 'WX_LOGIN_FAILED')
            
            openid = result.get('openid')
        
        # 查找或创建用户
        user = User.query.filter_by(wx_openid=openid).first()
        
        if not user:
            # 新用户，需要绑定学号
            if not student_id:
                return jsonify({
                    'success': False,
                    'message': '请先绑定学号',
                    'need_bind': True
                }), 200
            
            validate_student_id(student_id)
            # 检查学号是否已被绑定
            existing_user = User.query.filter_by(student_id=student_id).first()
            if existing_user:
                raise APIError('该学号已被绑定', 400, 'STUDENT_ID_EXISTS')
            
            # 创建新用户
            user = User(
                wx_openid=openid,
                student_id=student_id,
                real_name=data.get('real_name', ''),
                role='student',
                username=f"student_{student_id}"
            )
            db.session.add(user)
            db.session.commit()
        else:
            # 已存在用户，更新学号（如果提供）
            if student_id and not user.student_id:
                validate_student_id(student_id)
                existing_user = User.query.filter_by(student_id=student_id).first()
                if existing_user:
                    raise APIError('该学号已被绑定', 400, 'STUDENT_ID_EXISTS')
                user.student_id = student_id
                db.session.commit()
        
        token = generate_token(user.id, user.role)
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"WX login error: {str(e)}", exc_info=True)
        raise APIError('登录失败', 500)

@auth_bp.route('/bind-student-id', methods=['POST'])
@token_required
def bind_student_id():
    """绑定学号"""
    try:
        from flask import request
        data = request.get_json()
        validate_required(data, ['student_id'])
        
        student_id = data.get('student_id')
        validate_student_id(student_id)
        
        # 检查学号是否已被绑定
        existing_user = User.query.filter_by(student_id=student_id).first()
        if existing_user and existing_user.id != request.current_user.id:
            raise APIError('该学号已被绑定', 400, 'STUDENT_ID_EXISTS')
        
        request.current_user.student_id = student_id
        if not request.current_user.real_name:
            request.current_user.real_name = data.get('real_name', '')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '绑定成功',
            'data': request.current_user.to_dict()
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Bind student ID error: {str(e)}", exc_info=True)
        raise APIError('绑定失败', 500)

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user_info():
    """获取当前用户信息"""
    try:
        from flask import request
        return jsonify({
            'success': True,
            'data': request.current_user.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"Get user info error: {str(e)}", exc_info=True)
        raise APIError('获取用户信息失败', 500)

@auth_bp.route('/student-login', methods=['POST'])
def student_login():
    """学生用户名密码登录"""
    try:
        data = _load_request_data()
        validate_required(data, ['username', 'password'])

        username = data.get('username').strip()
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if not user or user.role != 'student' or not user.check_password(password):
            raise APIError('用户名或密码错误', 401, 'INVALID_CREDENTIALS')
        
        if user.status == 0:
            raise APIError('账号已被禁用', 403, 'USER_DISABLED')

        token = generate_token(user.id, user.role)

        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        }), 200

    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Student login error: {str(e)}", exc_info=True)
        raise APIError('登录失败', 500)

def _load_request_data():
    raw_body = request.get_data(as_text=True)
    data = request.get_json(silent=True)
    if data is None:
        if request.form:
            data = request.form.to_dict()
        elif raw_body:
            try:
                data = json.loads(raw_body)
            except ValueError:
                parsed = parse_qs(raw_body)
                data = {k: v[0] for k, v in parsed.items()}
    if not data:
        raise APIError('请求体不能为空', 400, 'EMPTY_REQUEST')
    return data

