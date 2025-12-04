from flask import Blueprint, request, jsonify
from app import db
from app.models.position import Position
from app.models.application import Application
from app.utils.decorators import token_required, role_required
from app.utils.errors import APIError
from app.utils.validators import validate_required, validate_coordinates
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)

positions_bp = Blueprint('positions', __name__)

@positions_bp.route('', methods=['GET'])
@token_required
def get_positions():
    """获取岗位列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'active')
        keyword = request.args.get('keyword', '')
        
        query = Position.query
        
        # 学生只能看到active的岗位
        if request.current_user.role == 'student':
            query = query.filter_by(status='active')
        elif status:
            query = query.filter_by(status=status)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    Position.title.like(f'%{keyword}%'),
                    Position.company_name.like(f'%{keyword}%'),
                    Position.location.like(f'%{keyword}%')
                )
            )
        
        # 分页
        pagination = query.order_by(Position.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [p.to_dict() for p in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get positions error: {str(e)}", exc_info=True)
        raise APIError('获取岗位列表失败', 500)

@positions_bp.route('/<int:position_id>', methods=['GET'])
@token_required
def get_position(position_id):
    """获取岗位详情"""
    try:
        position = Position.query.get_or_404(position_id)
        
        # 学生只能查看active的岗位
        if request.current_user.role == 'student' and position.status != 'active':
            raise APIError('岗位不存在或已关闭', 404)
        
        return jsonify({
            'success': True,
            'data': position.to_dict()
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Get position error: {str(e)}", exc_info=True)
        raise APIError('获取岗位详情失败', 500)

@positions_bp.route('', methods=['POST'])
@role_required('admin', 'teacher')
def create_position():
    """创建岗位"""
    try:
        data = request.get_json()
        validate_required(data, ['title', 'company_name', 'location', 'latitude', 'longitude'])
        
        validate_coordinates(data['latitude'], data['longitude'])
        
        position = Position(
            title=data['title'],
            company_name=data['company_name'],
            description=data.get('description'),
            requirements=data.get('requirements'),
            location=data['location'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            salary=data.get('salary'),
            duration=data.get('duration'),
            max_students=data.get('max_students', 1),
            publisher_id=request.current_user.id
        )
        
        db.session.add(position)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '创建成功',
            'data': position.to_dict()
        }), 201
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create position error: {str(e)}", exc_info=True)
        raise APIError('创建岗位失败', 500)

@positions_bp.route('/<int:position_id>', methods=['PUT'])
@role_required('admin', 'teacher')
def update_position(position_id):
    """更新岗位"""
    try:
        position = Position.query.get_or_404(position_id)
        
        # 检查权限：只能修改自己发布的或管理员可以修改所有
        if position.publisher_id != request.current_user.id and request.current_user.role != 'admin':
            raise APIError('无权修改此岗位', 403)
        
        data = request.get_json()
        
        if 'title' in data:
            position.title = data['title']
        if 'company_name' in data:
            position.company_name = data['company_name']
        if 'description' in data:
            position.description = data.get('description')
        if 'requirements' in data:
            position.requirements = data.get('requirements')
        if 'location' in data:
            position.location = data['location']
        if 'latitude' in data and 'longitude' in data:
            validate_coordinates(data['latitude'], data['longitude'])
            position.latitude = data['latitude']
            position.longitude = data['longitude']
        if 'salary' in data:
            position.salary = data.get('salary')
        if 'duration' in data:
            position.duration = data.get('duration')
        if 'max_students' in data:
            position.max_students = data.get('max_students')
        if 'status' in data:
            position.status = data['status']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': position.to_dict()
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update position error: {str(e)}", exc_info=True)
        raise APIError('更新岗位失败', 500)

@positions_bp.route('/<int:position_id>', methods=['DELETE'])
@role_required('admin', 'teacher')
def delete_position(position_id):
    """删除岗位"""
    try:
        position = Position.query.get_or_404(position_id)
        
        # 检查权限
        if position.publisher_id != request.current_user.id and request.current_user.role != 'admin':
            raise APIError('无权删除此岗位', 403)
        
        # 检查是否有已批准的申请
        approved_count = Application.query.filter_by(
            position_id=position_id,
            status='approved'
        ).count()
        
        if approved_count > 0:
            raise APIError('该岗位已有学生申请，无法删除', 400)
        
        db.session.delete(position)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete position error: {str(e)}", exc_info=True)
        raise APIError('删除岗位失败', 500)

