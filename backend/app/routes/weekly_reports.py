from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app import db
from app.models.weekly_report import WeeklyReport
from app.models.application import Application
from app.models.position import Position
from app.models.message import Message
from app.utils.decorators import token_required, role_required
from app.utils.errors import APIError
from app.utils.validators import validate_required
from flask import current_app
import os
import logging

logger = logging.getLogger(__name__)

weekly_reports_bp = Blueprint('weekly_reports', __name__)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@weekly_reports_bp.route('', methods=['GET'])
@token_required
def get_weekly_reports():
    """获取周报列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        student_id = request.args.get('student_id', type=int)
        position_id = request.args.get('position_id', type=int)
        status = request.args.get('status')
        
        query = WeeklyReport.query
        
        # 学生只能看自己的周报
        if request.current_user.role == 'student':
            query = query.filter_by(student_id=request.current_user.id)
        elif student_id:
            query = query.filter_by(student_id=student_id)
        
        if position_id:
            query = query.filter_by(position_id=position_id)
        
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.order_by(WeeklyReport.week_number.desc(), WeeklyReport.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'items': [r.to_dict() for r in pagination.items],
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get weekly reports error: {str(e)}", exc_info=True)
        raise APIError('获取周报列表失败', 500)

@weekly_reports_bp.route('/<int:report_id>', methods=['GET'])
@token_required
def get_weekly_report(report_id):
    """获取周报详情"""
    try:
        report = WeeklyReport.query.get_or_404(report_id)
        
        # 权限检查
        if request.current_user.role == 'student' and report.student_id != request.current_user.id:
            raise APIError('无权查看此周报', 403)
        
        return jsonify({
            'success': True,
            'data': report.to_dict()
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Get weekly report error: {str(e)}", exc_info=True)
        raise APIError('获取周报详情失败', 500)

@weekly_reports_bp.route('', methods=['POST'])
@token_required
def create_weekly_report():
    """提交周报"""
    try:
        # 只有学生可以提交周报
        if request.current_user.role != 'student':
            raise APIError('只有学生可以提交周报', 403)
        
        data = request.get_json()
        validate_required(data, ['position_id', 'week_number', 'content'])
        
        position_id = data['position_id']
        
        # 检查是否有已批准的申请
        application = Application.query.filter_by(
            student_id=request.current_user.id,
            position_id=position_id,
            status='approved'
        ).first()
        
        if not application:
            raise APIError('您未申请或该申请未通过', 400, 'NO_APPROVED_APPLICATION')
        
        # 检查该周是否已提交
        existing = WeeklyReport.query.filter_by(
            student_id=request.current_user.id,
            position_id=position_id,
            week_number=data['week_number']
        ).first()
        
        if existing:
            raise APIError('该周次已提交周报', 400, 'WEEK_ALREADY_SUBMITTED')
        
        report = WeeklyReport(
            student_id=request.current_user.id,
            position_id=position_id,
            week_number=data['week_number'],
            content=data['content'],
            attachment_path=data.get('attachment_path'),
            attachment_name=data.get('attachment_name')
        )
        
        db.session.add(report)
        db.session.commit()
        
        # 发送消息给教师
        position = Position.query.get(position_id)
        message = Message(
            user_id=position.publisher_id,
            title='新的周报提交',
            content=f'{request.current_user.real_name}提交了第{data["week_number"]}周周报',
            type='report',
            related_id=report.id
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '周报提交成功',
            'data': report.to_dict()
        }), 201
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Create weekly report error: {str(e)}", exc_info=True)
        raise APIError('提交周报失败', 500)

@weekly_reports_bp.route('/upload', methods=['POST'])
@token_required
def upload_attachment():
    """上传周报附件"""
    try:
        if 'file' not in request.files:
            raise APIError('没有上传文件', 400, 'NO_FILE')
        
        file = request.files['file']
        if file.filename == '':
            raise APIError('文件名为空', 400, 'EMPTY_FILENAME')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 添加时间戳避免重名
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            upload_folder = current_app.config['UPLOAD_FOLDER']
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            return jsonify({
                'success': True,
                'message': '上传成功',
                'data': {
                    'attachment_path': filename,
                    'attachment_name': file.filename
                }
            }), 200
        else:
            raise APIError('文件类型不允许', 400, 'INVALID_FILE_TYPE')
        
    except APIError as e:
        raise e
    except Exception as e:
        logger.error(f"Upload attachment error: {str(e)}", exc_info=True)
        raise APIError('上传失败', 500)

@weekly_reports_bp.route('/<int:report_id>/review', methods=['POST'])
@role_required('admin', 'teacher')
def review_weekly_report(report_id):
    """批改周报"""
    try:
        report = WeeklyReport.query.get_or_404(report_id)
        
        data = request.get_json()
        validate_required(data, ['score', 'comment'])
        
        score = float(data['score'])
        if not (0 <= score <= 100):
            raise APIError('评分必须在0-100之间', 400, 'INVALID_SCORE')
        
        report.score = score
        report.comment = data['comment']
        report.reviewer_id = request.current_user.id
        report.status = 'reviewed'
        from datetime import datetime
        report.reviewed_at = datetime.utcnow()
        
        db.session.commit()
        
        # 更新学生信用分
        from app.utils.credit import calculate_credit_score
        credit_score = calculate_credit_score(report.student_id)
        report.student.credit_score = credit_score
        db.session.commit()
        
        # 发送消息给学生
        message = Message(
            user_id=report.student_id,
            title='周报批改完成',
            content=f'您的第{report.week_number}周周报已批改，得分：{score}',
            type='report',
            related_id=report.id
        )
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '批改成功',
            'data': report.to_dict()
        }), 200
        
    except APIError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Review weekly report error: {str(e)}", exc_info=True)
        raise APIError('批改失败', 500)

