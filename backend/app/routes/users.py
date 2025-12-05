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
# CSV 模板，包含表头与示例行（注意使用真实换行符）
TEMPLATE_CSV = "username,real_name,role,student_id,password,phone,email,status\nstudent001,张三,student,20230001,123456,13800000000,student001@qq.com,1(1启用 0禁用)"

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
        status_filter = request.args.get('status', type=int)
        
        query = User.query
        if role != 'all':
            query = query.filter_by(role=role)
        
        if status_filter is not None:
            query = query.filter_by(status=status_filter)
        
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
            status=data.get('status', 1),
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

        if 'status' in data:
            status_value = data['status']
            if status_value not in [0, 1]:
                raise APIError('状态值不正确', 400, 'INVALID_STATUS')
            user.status = status_value

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

@users_bp.route('/batch-status', methods=['POST'])
@role_required('admin')
def batch_update_user_status():
    """批量启用/禁用用户"""
    try:
        data = request.get_json() or {}
        ids = data.get('ids')
        status = data.get('status')
        if not isinstance(ids, list) or not ids:
            raise APIError('请选择需要操作的用户', 400, 'INVALID_IDS')
        if status not in [0, 1]:
            raise APIError('状态值不正确', 400, 'INVALID_STATUS')
        users = User.query.filter(User.id.in_(ids)).all()
        if not users:
            raise APIError('未找到对应用户', 404, 'USERS_NOT_FOUND')
        for user in users:
            user.status = status
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '批量更新状态成功',
            'data': {
                'updated': [u.id for u in users],
                'status': status
            }
        }), 200
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Batch update user status error: {str(e)}", exc_info=True)
        raise APIError('批量更新状态失败', 500)


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


@users_bp.route('/import', methods=['POST'])
@role_required('admin')
def import_users():
    """批量导入用户，接受 JSON 数组 users"""
    try:
        payload = request.get_json() or {}
        users_data = payload.get('users')
        if not isinstance(users_data, list) or len(users_data) == 0:
            raise APIError('users 必须为非空数组', 400, 'INVALID_USERS')
        created = 0
        skipped = []
        for item in users_data:
            username = (item.get('username') or '').strip()
            real_name = (item.get('real_name') or '').strip()
            role = (item.get('role') or 'student').strip()
            password = item.get('password') or '123456'
            status = item.get('status', 1)
            if not username or not real_name or role not in ['admin', 'teacher', 'student']:
                skipped.append(username or '未知')
                continue
            if User.query.filter_by(username=username).first():
                skipped.append(username)
                continue
            student_id = item.get('student_id')
            if role == 'student':
                validate_student_id(student_id or '')
                if User.query.filter_by(student_id=student_id).first():
                    skipped.append(username)
                    continue
            user = User(
                username=username,
                real_name=real_name,
                role=role,
                status=status,
                student_id=student_id if role == 'student' else None,
                phone=item.get('phone'),
                email=item.get('email')
            )
            user.set_password(password)
            if role == 'teacher':
                user.set_permissions(_normalize_permissions(item.get('permissions')))
            else:
                user.set_permissions([])
            db.session.add(user)
            created += 1
        db.session.commit()
        return jsonify({'success': True, 'data': {'created': created, 'skipped': skipped}}), 200
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Import users error: {str(e)}", exc_info=True)
        raise APIError('批量导入失败', 500)


@users_bp.route('/import/template', methods=['GET'])
@role_required('admin')
def download_import_template():
    """下载批量导入模板 CSV"""
    from flask import Response
    return Response(
        TEMPLATE_CSV,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename="users_import_template.csv"'}
    )

