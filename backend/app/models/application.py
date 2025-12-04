from app import db
from datetime import datetime

class Application(db.Model):
    """实习申请模型"""
    __tablename__ = 'applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='学生ID')
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False, comment='岗位ID')
    resume = db.Column(db.Text, nullable=True, comment='简历内容')
    motivation = db.Column(db.Text, nullable=True, comment='申请动机')
    status = db.Column(db.String(20), default='pending', comment='状态: pending/approved/rejected')
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, comment='审核人ID')
    review_comment = db.Column(db.Text, nullable=True, comment='审核意见')
    reviewed_at = db.Column(db.DateTime, nullable=True, comment='审核时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
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
            'resume': self.resume,
            'motivation': self.motivation,
            'status': self.status,
            'reviewer_id': self.reviewer_id,
            'reviewer_name': self.reviewer.real_name if self.reviewer else None,
            'review_comment': self.review_comment,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<Application {self.id}>'

