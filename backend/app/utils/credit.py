from app.models.user import User
from app.models.checkin import CheckIn
from app.models.weekly_report import WeeklyReport
from app.models.application import Application
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

def calculate_credit_score(student_id):
    """
    计算学生信用分
    根据出勤率、周报提交率、单位评价计算
    
    Returns:
        信用分（0-100）
    """
    student = User.query.get(student_id)
    if not student or student.role != 'student':
        return 100.0
    
    # 获取已批准的申请
    approved_app = Application.query.filter_by(
        student_id=student_id,
        status='approved'
    ).first()
    
    if not approved_app:
        return 100.0
    
    position_id = approved_app.position_id
    
    # 1. 计算出勤率（30%权重）
    # 假设实习期为3个月，每周5天，共约60个工作日
    total_work_days = 60
    checkin_count = CheckIn.query.filter_by(
        student_id=student_id,
        position_id=position_id,
        status='normal'
    ).count()
    attendance_rate = min(checkin_count / total_work_days, 1.0) if total_work_days > 0 else 0
    attendance_score = attendance_rate * 30
    
    # 2. 计算周报提交率（30%权重）
    # 假设实习期为12周
    total_weeks = 12
    report_count = WeeklyReport.query.filter_by(
        student_id=student_id,
        position_id=position_id
    ).count()
    report_rate = min(report_count / total_weeks, 1.0) if total_weeks > 0 else 0
    report_score = report_rate * 30
    
    # 3. 计算周报平均分（30%权重）
    avg_score = db.session.query(func.avg(WeeklyReport.score)).filter_by(
        student_id=student_id,
        position_id=position_id
    ).scalar() or 0
    score_rate = avg_score / 100.0 if avg_score > 0 else 0
    score_component = score_rate * 30
    
    # 4. 异常签到扣分（10%权重）
    abnormal_count = CheckIn.query.filter_by(
        student_id=student_id,
        position_id=position_id,
        status='abnormal'
    ).count()
    # 每个异常签到扣1分，最多扣10分
    penalty = min(abnormal_count, 10)
    penalty_score = 10 - penalty
    
    # 计算总分
    total_score = attendance_score + report_score + score_component + penalty_score
    
    # 确保分数在0-100之间
    total_score = max(0, min(100, total_score))
    
    return round(total_score, 2)

