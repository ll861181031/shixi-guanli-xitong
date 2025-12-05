from app import db
from datetime import datetime, date

class CheckIn(db.Model):
    """签到记录模型"""
    __tablename__ = 'checkins'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='学生ID')
    position_id = db.Column(db.Integer, db.ForeignKey('positions.id'), nullable=False, comment='岗位ID')
    checkin_date = db.Column(db.Date, nullable=False, default=date.today, comment='签到日期')
    checkin_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='签到时间')
    latitude = db.Column(db.Float, nullable=False, comment='签到纬度')
    longitude = db.Column(db.Float, nullable=False, comment='签到经度')
    distance = db.Column(db.Float, nullable=False, comment='距离（米）')
    status = db.Column(db.String(20), default='normal', comment='状态: normal/abnormal/late/not_signed')
    abnormal_reason = db.Column(db.Text, nullable=True, comment='异常原因')
    remark = db.Column(db.String(500), nullable=True, comment='备注')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    position = db.relationship('Position', foreign_keys=[position_id])
    
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
            'checkin_date': self.checkin_date.isoformat() if self.checkin_date else None,
            'checkin_time': self.checkin_time.isoformat() if self.checkin_time else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'distance': round(self.distance, 2),
            'status': self.status,
            'abnormal_reason': self.abnormal_reason,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<CheckIn {self.id}>'

