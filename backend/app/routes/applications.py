from flask import Blueprint, request, jsonify
from app import db
from app.models.application import Application
from app.models.position import Position
from app.models.message import Message
from app.utils.decorators import token_required, role_required
from app.utils.errors import APIError
from app.utils.validators import validate_required
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)

applications_bp = Blueprint('applications', __name__)


def _audit_application(application, status, review_comment, reviewer):
    if status not in ['approved', 'rejected']:
        raise APIError('状态值不正确', 400, 'INVALID_STATUS')
    
    if application.status != 'pending':
        raise APIError('仅能审核待处理的申请', 400, 'INVALID_APPLICATION_STATUS')
    
    if status == 'approved':
        position = application.position
        if position.current_students >= position.max_students:
            raise APIError('该岗位已满员', 400, 'POSITION_FULL')
        
        existing_approved = Application.query.filter_by(
            student_id=application.student_id,
            status='approved'
        ).filter(Application.id != application.id).first()
        
        if existing_approved:
            raise APIError('该学生已有已批准的申请', 400, 'HAS_APPROVED_APPLICATION')
        
        position.current_students += 1
    
    application.status = status
    application.reviewer_id = reviewer.id
    application.review_comment = review_comment
    application.reviewed_at = datetime.utcnow()
    
    message = Message(
        user_id=application.student_id,
        title='申请审核结果',
        content=f'您的实习申请已{"通过" if status == "approved" else "拒绝"}',
        type='application',
        related_id=application.id
    )
    db.session.add(message)
    return application

@applications_bp.route('', methods=['GET'])
@token_required
def get_applications():
    """获取申请列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = Application.query
        
        # 学生只能看自己的申请
        if request.current_user.role == 'student':
            query = query.filter_by(student_id=request.current_user.id)
        # 教师和管理员可以看所有申请
        elif status:
            query = query.filter_by(status=status)
        
        pagination = query.order_by(Application.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [a.to_dict() for a in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get applications error: {str(e)}", exc_info=True)
        raise APIError('获取申请列表失败', 500)

@applications_bp.route('/<int:application_id>', methods=['GET'])
@token_required
def get_application(application_id):
    """获取申请详情"""
    try:
        application = Application.query.get_or_404(application_id)
        
        # 权限检查
        if request.current_user.role == 'student' and application.student_id != request.current_user.id:
            raise APIError('无权查看此申请', 403)
        
        return jsonify({
            'success': True,
            'data': application.to_dict()
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Get application error: {str(e)}", exc_info=True)
        raise APIError('获取申请详情失败', 500)

@applications_bp.route('', methods=['POST'])
@token_required
def create_application():
    """提交申请"""
    try:
        # 只有学生可以提交申请
        if request.current_user.role != 'student':
            raise APIError('只有学生可以提交申请', 403)
        
        if not request.current_user.student_id:
            raise APIError('请先绑定学号', 400, 'NEED_BIND_STUDENT_ID')
        
        data = request.get_json()
        validate_required(data, ['position_id'])
        
        position_id = data['position_id']
        position = Position.query.get_or_404(position_id)
        
        if position.status != 1:
            raise APIError('该岗位暂不可申请', 400, 'POSITION_NOT_OPEN')
        
        # 检查是否已申请
        existing = Application.query.filter_by(
            student_id=request.current_user.id,
            position_id=position_id
        ).first()
        
        if existing:
            raise APIError('您已申请过该岗位', 400, 'ALREADY_APPLIED')
        
        # 检查是否已有已批准的申请
        approved = Application.query.filter_by(
            student_id=request.current_user.id,
            status='approved'
        ).first()
        
        if approved:
            raise APIError('您已有已批准的申请，无法再申请其他岗位', 400, 'HAS_APPROVED_APPLICATION')
        
        application = Application(
            student_id=request.current_user.id,
            position_id=position_id,
            resume=data.get('resume'),
            motivation=data.get('motivation')
        )
        
        db.session.add(application)
        db.session.commit()
        
        # 发送消息给岗位发布者
        message = Message(
            user_id=position.publisher_id,
            title='新的实习申请',
            content=f'{request.current_user.real_name}申请了您发布的岗位：{position.title}',
            type='application',
            related_id=application.id
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '申请提交成功',
            'data': application.to_dict()
        }), 201
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create application error: {str(e)}", exc_info=True)
        raise APIError('提交申请失败', 500)

@applications_bp.route('/<int:application_id>/review', methods=['POST'])
@role_required('admin', 'teacher')
def review_application(application_id):
    """审核申请"""
    try:
        application = Application.query.get_or_404(application_id)
        
        data = request.get_json()
        validate_required(data, ['status'])
        
        status = data['status']
        review_comment = data.get('review_comment')
        
        _audit_application(application, status, review_comment, request.current_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '审核成功',
            'data': application.to_dict()
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Review application error: {str(e)}", exc_info=True)
        raise APIError('审核失败', 500)


@applications_bp.route('/batch-audit', methods=['POST'])
@role_required('admin')
def batch_audit_applications():
    """批量审核申请"""
    try:
        data = request.get_json() or {}
        ids = data.get('ids')
        status = data.get('status')
        review_comment = data.get('review_comment')
        if not isinstance(ids, list) or not ids:
            raise APIError('请选择需要审核的申请', 400, 'INVALID_IDS')
        
        applications = Application.query.filter(Application.id.in_(ids)).all()
        if not applications:
            raise APIError('未找到对应申请', 404, 'APPLICATION_NOT_FOUND')
        
        app_map = {app.id: app for app in applications}
        missing = [app_id for app_id in ids if app_id not in app_map]
        if missing:
            raise APIError(f'部分申请不存在: {missing}', 404, 'APPLICATION_NOT_FOUND')
        
        for application in applications:
            _audit_application(application, status, review_comment, request.current_user)
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '批量审核成功',
            'data': {'updated': ids, 'status': status}
        }), 200
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Batch audit applications error: {str(e)}", exc_info=True)
        raise APIError('批量审核失败', 500)

