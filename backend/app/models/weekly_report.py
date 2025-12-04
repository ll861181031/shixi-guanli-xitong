from app import db
from datetime import datetime

class WeeklyReport(db.Model):
    """周报模型"""
    __tablename__ = 'weekly_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='学生ID')
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False, comment='岗位ID')
    week_number = db.Column(db.Integer, nullable=False, comment='周次')
    content = db.Column(db.Text, nullable=False, comment='周报内容')
    attachment_path = db.Column(db.String(500), nullable=True, comment='附件路径')
    attachment_name = db.Column(db.String(200), nullable=True, comment='附件名称')
    status = db.Column(db.String(20), default='submitted', comment='状态: submitted/reviewed')
    score = db.Column(db.Float, nullable=True, comment='评分')
    comment = db.Column(db.Text, nullable=True, comment='批改意见')
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='批改人ID')
    reviewed_at = db.Column(db.DateTime, nullable=True, comment='批改时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    position = db.relationship('Position', foreign_keys=[position_id])
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.real_name if self.student else None,
            'student_id_number': self.student.student_id if self.student else None,
            'position_id': self.position_id,
            'position_title': self.position.title if self.position else None,
            'position_company': self.position.company_name if self.position else None,
            'week_number': self.week_number,
            'content': self.content,
            'attachment_path': self.attachment_path,
            'attachment_name': self.attachment_name,
            'status': self.status,
            'score': self.score,
            'comment': self.comment,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer.real_name if self.reviewer else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<WeeklyReport {self.id}>'

