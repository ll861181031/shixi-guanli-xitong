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

ALLOWED_POSITION_STATUSES = {0, 1, 2}


def parse_optional_int(value, field_name):
    if value is None or value == '':
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise APIError(f'{field_name}参数无效', 400, f'INVALID_{field_name.upper()}')


def normalize_non_negative_int(value, field_name):
    if value is None or value == '':
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise APIError(f'{field_name}必须为整数', 400, f'INVALID_{field_name.upper()}')
    if parsed < 0:
        raise APIError(f'{field_name}不能小于0', 400, f'INVALID_{field_name.upper()}')
    return parsed


def validate_position_status(value):
    if value is None:
        return
    if value not in ALLOWED_POSITION_STATUSES:
        raise APIError('岗位状态无效', 400, 'INVALID_POSITION_STATUS')


def validate_salary_range(min_salary, max_salary):
    if min_salary is not None and max_salary is not None and min_salary > max_salary:
        raise APIError('最低薪资不能高于最高薪资', 400, 'INVALID_SALARY_RANGE')

@positions_bp.route('', methods=['GET'])
@token_required
def get_positions():
    """获取岗位列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        keyword = (request.args.get('keyword') or '').strip()
        location = request.args.get('location')
        internship_duration = request.args.get('internship_duration')
        min_salary = parse_optional_int(request.args.get('min_salary'), 'min_salary')
        max_salary = parse_optional_int(request.args.get('max_salary'), 'max_salary')
        status_value = parse_optional_int(request.args.get('status'), 'status')
        
        validate_salary_range(min_salary, max_salary)
        validate_position_status(status_value)
        
        query = Position.query
        
        # 学生默认只能看到在招岗位，若明确选择状态则按所选过滤
        if request.current_user.role == 'student':
            if status_value is None:
                query = query.filter_by(status=1)
            else:
                query = query.filter_by(status=status_value)
        elif status_value is not None:
            query = query.filter_by(status=status_value)
        
        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    Position.title.like(f'%{keyword}%'),
                    Position.company_name.like(f'%{keyword}%'),
                    Position.location.like(f'%{keyword}%')
                )
            )
        
        if location:
            query = query.filter_by(location=location)
        
        if internship_duration:
            query = query.filter_by(internship_duration=internship_duration)
        
        if min_salary is not None:
            query = query.filter(Position.min_salary >= min_salary)
        
        if max_salary is not None:
            query = query.filter(Position.max_salary <= max_salary)
        
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
        
        min_salary = normalize_non_negative_int(data.get('min_salary'), 'min_salary')
        max_salary = normalize_non_negative_int(data.get('max_salary'), 'max_salary')
        validate_salary_range(min_salary, max_salary)
        
        status_raw = data.get('status', 1)
        try:
            status_value = int(status_raw)
        except (TypeError, ValueError):
            raise APIError('岗位状态格式不正确', 400, 'INVALID_POSITION_STATUS')
        validate_position_status(status_value)
        
        position = Position(
            title=data['title'],
            company_name=data['company_name'],
            description=data.get('description'),
            requirements=data.get('requirements'),
            location=data['location'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            min_salary=min_salary,
            max_salary=max_salary,
            internship_duration=data.get('internship_duration'),
            max_students=data.get('max_students', 1),
            status=status_value,
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
        if 'min_salary' in data or 'max_salary' in data:
            min_salary = normalize_non_negative_int(
                data.get('min_salary', position.min_salary),
                'min_salary'
            )
            max_salary = normalize_non_negative_int(
                data.get('max_salary', position.max_salary),
                'max_salary'
            )
            validate_salary_range(min_salary, max_salary)
            position.min_salary = min_salary
            position.max_salary = max_salary
        if 'internship_duration' in data:
            position.internship_duration = data.get('internship_duration')
        if 'max_students' in data:
            position.max_students = data.get('max_students')
        if 'status' in data:
            try:
                status_value = int(data['status'])
            except (TypeError, ValueError):
                raise APIError('岗位状态格式不正确', 400, 'INVALID_POSITION_STATUS')
            validate_position_status(status_value)
            position.status = status_value
        
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


@positions_bp.route('/batch-delete', methods=['POST'])
@role_required('admin')
def batch_delete_positions():
    """批量删除岗位"""
    try:
        data = request.get_json() or {}
        ids = data.get('ids')
        if not isinstance(ids, list) or not ids:
            raise APIError('请选择要删除的岗位', 400, 'INVALID_IDS')
        
        positions = Position.query.filter(Position.id.in_(ids)).all()
        if not positions:
            raise APIError('未找到对应岗位', 404, 'POSITION_NOT_FOUND')
        
        blocked = []
        for position in positions:
            approved_count = Application.query.filter_by(
                position_id=position.id,
                status='approved'
            ).count()
            if approved_count > 0:
                blocked.append(position.title)
        
        if blocked:
            raise APIError(f"以下岗位已有已批准申请，无法删除: {', '.join(blocked)}", 400, 'POSITION_HAS_APPROVED')
        
        deleted_ids = []
        for position in positions:
            deleted_ids.append(position.id)
            db.session.delete(position)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '批量删除成功',
            'data': {'deleted': deleted_ids}
        }), 200
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Batch delete positions error: {str(e)}", exc_info=True)
        raise APIError('批量删除失败', 500)


@positions_bp.route('/locations', methods=['GET'])
@token_required
def get_position_locations():
    """获取岗位地点列表"""
    try:
        locations = db.session.query(Position.location).filter(
            Position.location.isnot(None)
        ).distinct().all()
        location_list = sorted({loc for (loc,) in locations if loc})
        return jsonify({
            'success': True,
            'data': location_list
        }), 200
    except Exception as e:
        logger.error(f"Get position locations error: {str(e)}", exc_info=True)
        raise APIError('获取岗位地点失败', 500)

