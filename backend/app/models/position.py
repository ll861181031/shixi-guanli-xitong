from app import db
from datetime import datetime

class Position(db.Model):
    """实习岗位模型"""
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, comment='岗位标题')
    company_name = db.Column(db.String(200), nullable=False, comment='公司名称')
    description = db.Column(db.Text, nullable=True, comment='岗位描述')
    requirements = db.Column(db.Text, nullable=True, comment='岗位要求')
    location = db.Column(db.String(200), nullable=False, comment='工作地点')
    latitude = db.Column(db.Float, nullable=False, comment='纬度')
    longitude = db.Column(db.Float, nullable=False, comment='经度')
    salary = db.Column(db.String(50), nullable=True, comment='薪资')
    duration = db.Column(db.String(50), nullable=True, comment='实习时长')
    max_students = db.Column(db.Integer, default=1, comment='最大接收学生数')
    current_students = db.Column(db.Integer, default=0, comment='当前学生数')
    status = db.Column(db.String(20), default='active', comment='状态: active/closed')
    publisher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='发布者ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    publisher = db.relationship('User', foreign_keys=[publisher_id])
    applications = db.relationship('Application', backref='position', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'company_name': self.company_name,
            'description': self.description,
            'requirements': self.requirements,
            'location': self.location,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'salary': self.salary,
            'duration': self.duration,
            'max_students': self.max_students,
            'current_students': self.current_students,
            'status': self.status,
            'publisher_id': self.publisher_id,
            'publisher_name': self.publisher.real_name if self.publisher else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<Position {self.title}>'

