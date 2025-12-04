from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.models.message import Message
from app.utils.decorators import token_required, role_required
from app.utils.errors import APIError
from app.utils.validators import validate_required, validate_email, validate_phone, validate_student_id
import logging
import json

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)

@users_bp.route('/messages', methods=['GET'])
@token_required
def get_messages():
    """获取消息列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        is_read = request.args.get('is_read')
        
        query = Message.query.filter_by(user_id=request.current_user.id)
        
        if is_read is not None:
            query = query.filter_by(is_read=is_read == 'true')
        
        pagination = query.order_by(Message.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [m.to_dict() for m in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get messages error: {str(e)}", exc_info=True)
        raise APIError('获取消息列表失败', 500)

@users_bp.route('/messages/<int:message_id>/read', methods=['POST'])
@token_required
def mark_message_read(message_id):
    """标记消息为已读"""
    try:
        message = Message.query.get_or_404(message_id)
        
        if message.user_id != request.current_user.id:
            raise APIError('无权操作此消息', 403)
        
        message.is_read = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '标记成功'
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Mark message read error: {str(e)}", exc_info=True)
        raise APIError('标记失败', 500)

MODULE_PERMISSIONS = ['positions', 'applications', 'checkins', 'reports', 'statistics', 'users']

@users_bp.route('', methods=['GET'])
@role_required('admin', 'teacher')
def get_users():
    """获取用户列表（管理员/教师）"""
    try:
        if request.current_user.role == 'teacher' and 'users' not in request.current_user.get_permissions():
            raise APIError('权限不足', 403, 'INSUFFICIENT_PERMISSIONS')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        role = request.args.get('role', 'student')
        keyword = request.args.get('keyword', '')
        
        query = User.query
        if role != 'all':
            query = query.filter_by(role=role)
        
        if keyword:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    User.username.like(f'%{keyword}%'),
                    User.real_name.like(f'%{keyword}%'),
                    User.student_id.like(f'%{keyword}%')
                )
            )
        
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [u.to_dict() for u in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get users error: {str(e)}", exc_info=True)
        raise APIError('获取用户列表失败', 500)

@users_bp.route('/<int:user_id>', methods=['GET'])
@role_required('admin', 'teacher')
def get_user(user_id):
    """获取用户详情"""
    try:
        if request.current_user.role == 'teacher' and 'users' not in request.current_user.get_permissions():
            raise APIError('权限不足', 403, 'INSUFFICIENT_PERMISSIONS')
        user = User.query.get_or_404(user_id)
        return jsonify({
            'success': True,
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get user error: {str(e)}", exc_info=True)
        raise APIError('获取用户详情失败', 500)

@users_bp.route('', methods=['POST'])
@role_required('admin')
def create_user():
    """管理员创建用户"""
    try:
        data = request.get_json() or {}
        validate_required(data, ['username', 'password', 'real_name', 'role'])
        username = data.get('username').strip()
        password = data.get('password')
        real_name = data.get('real_name').strip()
        role = data.get('role').strip()

        if role not in ['admin', 'teacher', 'student']:
            raise APIError('角色不合法', 400, 'INVALID_ROLE')

        if User.query.filter_by(username=username).first():
            raise APIError('用户名已存在', 400, 'USERNAME_EXISTS')

        if data.get('phone'):
            validate_phone(data['phone'])
        if data.get('email'):
            validate_email(data['email'])

        student_id = data.get('student_id')
        if role == 'student':
            validate_student_id(student_id or '')
            if User.query.filter_by(student_id=student_id).first():
                raise APIError('学号已存在', 400, 'STUDENT_ID_EXISTS')

        user = User(
            username=username,
            real_name=real_name,
            role=role,
            student_id=student_id if role == 'student' else None,
            phone=data.get('phone'),
            email=data.get('email')
        )
        user.set_password(password)

        if role == 'teacher':
            user.set_permissions(_normalize_permissions(data.get('permissions')))
        else:
            user.set_permissions([])

        db.session.add(user)
        db.session.commit()

        return jsonify({'success': True, 'message': '创建成功', 'data': user.to_dict()}), 201
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create user error: {str(e)}", exc_info=True)
        raise APIError('创建用户失败', 500)

@users_bp.route('/<int:user_id>', methods=['PUT'])
@role_required('admin')
def update_user(user_id):
    """管理员更新用户信息/权限"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json() or {}

        if 'real_name' in data:
            user.real_name = data['real_name'].strip()

        if 'phone' in data and data['phone']:
            validate_phone(data['phone'])
            user.phone = data['phone']

        if 'email' in data and data['email']:
            validate_email(data['email'])
            user.email = data['email']

        if user.role == 'student' and 'student_id' in data:
            new_student_id = data['student_id']
            validate_student_id(new_student_id or '')
            if new_student_id != user.student_id and User.query.filter_by(student_id=new_student_id).first():
                raise APIError('学号已存在', 400, 'STUDENT_ID_EXISTS')
            user.student_id = new_student_id

        if 'password' in data and data['password']:
            user.set_password(data['password'])

        if user.role == 'teacher' and 'permissions' in data:
            user.set_permissions(_normalize_permissions(data.get('permissions')))

        db.session.commit()

        return jsonify({'success': True, 'message': '更新成功', 'data': user.to_dict()}), 200
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update user error: {str(e)}", exc_info=True)
        raise APIError('更新用户失败', 500)

def _normalize_permissions(raw):
    if raw is None:
        return []
    perms = raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return []
        try:
            perms = json.loads(raw)
        except ValueError:
            perms = [p.strip() for p in raw.split(',')]
    if not isinstance(perms, list):
        raise APIError('权限格式不正确', 400, 'INVALID_PERMISSIONS')
    cleaned = [p for p in perms if p in MODULE_PERMISSIONS]
    return cleaned

