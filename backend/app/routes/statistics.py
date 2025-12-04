from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.models.position import Position
from app.models.application import Application
from app.models.checkin import CheckIn
from app.models.weekly_report import WeeklyReport
from app.utils.decorators import role_required
from app.utils.errors import APIError
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

statistics_bp = Blueprint('statistics', __name__)

@statistics_bp.route('/overview', methods=['GET'])
@role_required('admin', 'teacher')
def get_overview():
    """获取概览统计"""
    try:
        # 学生总数
        total_students = User.query.filter_by(role='student').count()
        
        # 岗位总数
        total_positions = Position.query.count()
        active_positions = Position.query.filter_by(status='active').count()
        
        # 申请总数
        total_applications = Application.query.count()
        pending_applications = Application.query.filter_by(status='pending').count()
        approved_applications = Application.query.filter_by(status='approved').count()
        
        # 签到统计
        total_checkins = CheckIn.query.count()
        normal_checkins = CheckIn.query.filter_by(status='normal').count()
        abnormal_checkins = CheckIn.query.filter_by(status='abnormal').count()
        
        # 周报统计
        total_reports = WeeklyReport.query.count()
        submitted_reports = WeeklyReport.query.filter_by(status='submitted').count()
        reviewed_reports = WeeklyReport.query.filter_by(status='reviewed').count()
        
        return jsonify({
            'success': True,
            'data': {
                'students': {
                    'total': total_students
                },
                'positions': {
                    'total': total_positions,
                    'active': active_positions
                },
                'applications': {
                    'total': total_applications,
                    'pending': pending_applications,
                    'approved': approved_applications
                },
                'checkins': {
                    'total': total_checkins,
                    'normal': normal_checkins,
                    'abnormal': abnormal_checkins
                },
                'reports': {
                    'total': total_reports,
                    'submitted': submitted_reports,
                    'reviewed': reviewed_reports
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get overview error: {str(e)}", exc_info=True)
        raise APIError('获取概览统计失败', 500)

@statistics_bp.route('/attendance-rate', methods=['GET'])
@role_required('admin', 'teacher')
def get_attendance_rate():
    """获取出勤率统计"""
    try:
        # 按学生统计出勤率
        students = User.query.filter_by(role='student').all()
        attendance_data = []
        
        for student in students:
            # 获取已批准的申请
            application = Application.query.filter_by(
                student_id=student.id,
                status='approved'
            ).first()
            
            if not application:
                continue
            
            # 计算出勤率
            total_work_days = 60
            checkin_count = CheckIn.query.filter_by(
                student_id=student.id,
                position_id=application.position_id,
                status='normal'
            ).count()
            
            attendance_rate = (checkin_count / total_work_days * 100) if total_work_days > 0 else 0
            
            attendance_data.append({
                'student_id': student.id,
                'student_name': student.real_name,
                'student_id_number': student.student_id,
                'attendance_rate': round(attendance_rate, 2),
                'checkin_count': checkin_count
            })
        
        return jsonify({
            'success': True,
            'data': attendance_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get attendance rate error: {str(e)}", exc_info=True)
        raise APIError('获取出勤率统计失败', 500)

@statistics_bp.route('/report-submission-rate', methods=['GET'])
@role_required('admin', 'teacher')
def get_report_submission_rate():
    """获取周报提交率统计"""
    try:
        students = User.query.filter_by(role='student').all()
        submission_data = []
        
        for student in students:
            application = Application.query.filter_by(
                student_id=student.id,
                status='approved'
            ).first()
            
            if not application:
                continue
            
            total_weeks = 12
            report_count = WeeklyReport.query.filter_by(
                student_id=student.id,
                position_id=application.position_id
            ).count()
            
            submission_rate = (report_count / total_weeks * 100) if total_weeks > 0 else 0
            
            submission_data.append({
                'student_id': student.id,
                'student_name': student.real_name,
                'student_id_number': student.student_id,
                'submission_rate': round(submission_rate, 2),
                'report_count': report_count
            })
        
        return jsonify({
            'success': True,
            'data': submission_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get report submission rate error: {str(e)}", exc_info=True)
        raise APIError('获取周报提交率统计失败', 500)

@statistics_bp.route('/position-distribution', methods=['GET'])
@role_required('admin', 'teacher')
def get_position_distribution():
    """获取岗位分布统计"""
    try:
        positions = Position.query.all()
        distribution_data = []
        
        for position in positions:
            application_count = Application.query.filter_by(
                position_id=position.id,
                status='approved'
            ).count()
            
            distribution_data.append({
                'position_id': position.id,
                'position_title': position.title,
                'company_name': position.company_name,
                'student_count': application_count,
                'max_students': position.max_students
            })
        
        return jsonify({
            'success': True,
            'data': distribution_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get position distribution error: {str(e)}", exc_info=True)
        raise APIError('获取岗位分布统计失败', 500)

@statistics_bp.route('/checkin-trend', methods=['GET'])
@role_required('admin', 'teacher')
def get_checkin_trend():
    """获取签到趋势（按日期）"""
    try:
        days = request.args.get('days', 30, type=int)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 按日期统计签到数量
        checkins = db.session.query(
            CheckIn.checkin_date,
            func.count(CheckIn.id).label('count')
        ).filter(
            CheckIn.checkin_date >= start_date,
            CheckIn.checkin_date <= end_date
        ).group_by(CheckIn.checkin_date).all()
        
        trend_data = [{
            'date': str(date),
            'count': count
        } for date, count in checkins]
        
        return jsonify({
            'success': True,
            'data': trend_data
        }), 200
        
    except Exception as e:
        logger.error(f"Get checkin trend error: {str(e)}", exc_info=True)
        raise APIError('获取签到趋势失败', 500)

