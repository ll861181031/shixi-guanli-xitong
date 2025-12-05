from flask import Blueprint, request, jsonify
from app import db
from app.models.checkin import CheckIn
from app.models.application import Application
from app.models.position import Position
from app.utils.decorators import token_required, role_required
from app.utils.errors import APIError
from app.utils.validators import validate_required, validate_coordinates
from app.utils.distance import haversine_distance
from datetime import datetime, date, timedelta, time
from sqlalchemy import func
import logging
import time as time_lib

logger = logging.getLogger(__name__)

checkins_bp = Blueprint('checkins', __name__)


def _parse_query_date(raw_value, field_name):
    """解析查询参数中的日期字符串，确保无效输入不会导致 500"""
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value).date()
    except ValueError:
        raise APIError(f'{field_name}格式不正确，应为YYYY-MM-DD', 400, 'INVALID_DATE_RANGE')

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
        start_date = _parse_query_date(request.args.get('start_date'), 'start_date')
        end_date = _parse_query_date(request.args.get('end_date'), 'end_date')
        
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
            query = query.filter(CheckIn.checkin_date >= start_date)
        if end_date:
            query = query.filter(CheckIn.checkin_date <= end_date)
        
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
        start_ts = time_lib.time()
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
        
        # 检查今天是否已签到
        today = date.today()
        today_checkin = CheckIn.query.filter_by(
            student_id=request.current_user.id,
            position_id=position_id,
            checkin_date=today
        ).first()
        
        if today_checkin:
            raise APIError('今日已完成签到', 400, 'ALREADY_CHECKED_IN', code='1002')

        # 校验签到时间窗口
        from flask import current_app
        start_cfg = current_app.config.get('CHECKIN_WORKDAY_START', '09:00')
        end_cfg = current_app.config.get('CHECKIN_WORKDAY_END', '18:00')
        start_h, start_m = map(int, start_cfg.split(':'))
        end_h, end_m = map(int, end_cfg.split(':'))
        now_time = datetime.utcnow().time()
        start_time = time(start_h, start_m)
        end_time = time(end_h, end_m)
        late_minutes = 0
        if now_time < start_time:
            raise APIError('当前非签到时段', 400, 'NOT_IN_CHECKIN_WINDOW', code='1003')
        if now_time > end_time:
            delta = datetime.combine(today, now_time) - datetime.combine(today, end_time)
            late_minutes = max(0, int(delta.total_seconds() // 60))

        # 计算距离
        distance = haversine_distance(
            data['latitude'],
            data['longitude'],
            position.latitude,
            position.longitude
        )

        allowed_radius = position.checkin_radius or current_app.config.get('CHECKIN_NORMAL_DISTANCE', 200)
        status = 'normal'
        abnormal_reason = None
        if distance > allowed_radius:
            status = 'abnormal'
            abnormal_reason = f'超出签到范围，当前距离{round(distance,2)}米，允许{allowed_radius}米内'
        elif late_minutes > 0:
            status = 'late'
            abnormal_reason = f'迟到 {late_minutes} 分钟'
        
        checkin = CheckIn(
            student_id=request.current_user.id,
            position_id=position_id,
            checkin_date=today,
            latitude=data['latitude'],
            longitude=data['longitude'],
            distance=distance,
            status=status,
            abnormal_reason=abnormal_reason,
            remark=data.get('remark')
        )

        from app.models.message import Message
        db.session.add(checkin)
        message = Message(
            user_id=request.current_user.id,
            title='签到通知',
            content=f'您的签到已提交，状态：{status}，距离：{round(distance,2)}米',
            type='checkin',
            related_id=checkin.id
        )
        db.session.add(message)
        db.session.commit()

        duration_ms = int((time_lib.time() - start_ts) * 1000)
        logger.info(f"checkin_log|user={request.current_user.id}|position={position_id}|status={status}|distance={round(distance,2)}|allowed={allowed_radius}|late_minutes={late_minutes}|duration_ms={duration_ms}")

        if status == 'abnormal':
            raise APIError(
                f'超出签到范围，当前距离{round(distance,2)}米，允许{allowed_radius}米内',
                400,
                'OUT_OF_RANGE',
                code='1001',
                data={'distance': round(distance, 2), 'allowed': allowed_radius}
            )

        return jsonify({
            'success': True,
            'message': '签到成功' if status == 'normal' else '签到已记录',
            'data': {**checkin.to_dict(), 'late_minutes': late_minutes}
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

