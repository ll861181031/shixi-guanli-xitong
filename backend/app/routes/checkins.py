from flask import Blueprint, request, jsonify
from app import db
from app.models.checkin import CheckIn
from app.models.application import Application
from app.models.position import Position
from app.utils.decorators import token_required, role_required
from app.utils.errors import APIError
from app.utils.validators import validate_required, validate_coordinates
from app.utils.distance import haversine_distance, check_checkin_status
from datetime import datetime, date, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

checkins_bp = Blueprint('checkins', __name__)

@checkins_bp.route('', methods=['GET'])
@token_required
def get_checkins():
    """获取签到记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        student_id = request.args.get('student_id', type=int)
        position_id = request.args.get('position_id', type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = CheckIn.query
        
        # 学生只能看自己的签到
        if request.current_user.role == 'student':
            query = query.filter_by(student_id=request.current_user.id)
        elif student_id:
            query = query.filter_by(student_id=student_id)
        
        if position_id:
            query = query.filter_by(position_id=position_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if start_date:
            query = query.filter(CheckIn.checkin_date >= datetime.fromisoformat(start_date).date())
        if end_date:
            query = query.filter(CheckIn.checkin_date <= datetime.fromisoformat(end_date).date())
        
        pagination = query.order_by(CheckIn.checkin_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [c.to_dict() for c in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get checkins error: {str(e)}", exc_info=True)
        raise APIError('获取签到记录失败', 500)

@checkins_bp.route('', methods=['POST'])
@token_required
def create_checkin():
    """提交签到"""
    try:
        # 只有学生可以签到
        if request.current_user.role != 'student':
            raise APIError('只有学生可以签到', 403)
        
        data = request.get_json()
        validate_required(data, ['position_id', 'latitude', 'longitude'])
        
        validate_coordinates(data['latitude'], data['longitude'])
        
        position_id = data['position_id']
        position = Position.query.get_or_404(position_id)
        
        # 检查是否有已批准的申请
        application = Application.query.filter_by(
            student_id=request.current_user.id,
            position_id=position_id,
            status='approved'
        ).first()
        
        if not application:
            raise APIError('您未申请或该申请未通过', 400, 'NO_APPROVED_APPLICATION')
        
        # 计算距离
        distance = haversine_distance(
            data['latitude'],
            data['longitude'],
            position.latitude,
            position.longitude
        )
        
        # 判断签到状态
        from flask import current_app
        status = check_checkin_status(
            distance,
            current_app.config['CHECKIN_NORMAL_DISTANCE'],
            current_app.config['CHECKIN_ABNORMAL_DISTANCE']
        )
        
        # 检查今天是否已签到
        today = date.today()
        today_checkin = CheckIn.query.filter_by(
            student_id=request.current_user.id,
            position_id=position_id,
            checkin_date=today
        ).first()
        
        if today_checkin:
            raise APIError('今天已签到', 400, 'ALREADY_CHECKED_IN')
        
        checkin = CheckIn(
            student_id=request.current_user.id,
            position_id=position_id,
            checkin_date=today,
            latitude=data['latitude'],
            longitude=data['longitude'],
            distance=distance,
            status=status,
            remark=data.get('remark')
        )
        
        db.session.add(checkin)
        db.session.commit()
        
        # 如果是异常签到，发送消息给教师
        if status == 'abnormal':
            from app.models.message import Message
            message = Message(
                user_id=position.publisher_id,
                title='异常签到提醒',
                content=f'{request.current_user.real_name}在{position.title}位置签到异常，距离{round(distance, 2)}米',
                type='checkin',
                related_id=checkin.id
            )
            db.session.add(message)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '签到成功',
            'data': checkin.to_dict()
        }), 201
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create checkin error: {str(e)}", exc_info=True)
        raise APIError('签到失败', 500)

@checkins_bp.route('/statistics', methods=['GET'])
@token_required
def get_checkin_statistics():
    """获取签到统计"""
    try:
        student_id = request.args.get('student_id', type=int)
        position_id = request.args.get('position_id', type=int)
        
        # 学生只能看自己的统计
        if request.current_user.role == 'student':
            student_id = request.current_user.id
        
        query = CheckIn.query
        if student_id:
            query = query.filter_by(student_id=student_id)
        if position_id:
            query = query.filter_by(position_id=position_id)
        
        total = query.count()
        normal_count = query.filter_by(status='normal').count()
        abnormal_count = query.filter_by(status='abnormal').count()
        
        # 计算出勤率（假设实习期为60个工作日）
        total_work_days = 60
        attendance_rate = (normal_count / total_work_days * 100) if total_work_days > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'normal_count': normal_count,
                'abnormal_count': abnormal_count,
                'attendance_rate': round(attendance_rate, 2)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get checkin statistics error: {str(e)}", exc_info=True)
        raise APIError('获取签到统计失败', 500)

