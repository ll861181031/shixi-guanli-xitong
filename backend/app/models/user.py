from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(255), nullable=True, comment='密码哈希')
    real_name = db.Column(db.String(50), nullable=False, comment='真实姓名')
    student_id = db.Column(db.String(20), unique=True, nullable=True, comment='学号')
    wx_openid = db.Column(db.String(100), unique=True, nullable=True, comment='微信OpenID')
    role = db.Column(db.String(20), nullable=False, default='student', comment='角色: student/teacher/admin')
    phone = db.Column(db.String(20), nullable=True, comment='手机号')
    email = db.Column(db.String(100), nullable=True, comment='邮箱')
    credit_score = db.Column(db.Float, default=100.0, comment='信用分')
    permissions = db.Column(db.Text, default='[]', comment='权限配置(JSON)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    applications = db.relationship(
        'Application',
        foreign_keys='Application.student_id',
        backref='student',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    checkins = db.relationship('CheckIn', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    weekly_reports = db.relationship(
        'WeeklyReport',
        foreign_keys='WeeklyReport.student_id',
        backref='student',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    messages = db.relationship('Message', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'student_id': self.student_id,
            'role': self.role,
            'phone': self.phone,
            'email': self.email,
            'credit_score': self.credit_score,
            'permissions': self.get_permissions(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            data['wx_openid'] = self.wx_openid
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'

    def get_permissions(self):
        try:
            return json.loads(self.permissions or '[]')
        except json.JSONDecodeError:
            return []

    def set_permissions(self, permissions_list):
        self.permissions = json.dumps(permissions_list or [])

