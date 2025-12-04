from app import db
from datetime import datetime

class Message(db.Model):
    """消息模型"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='接收用户ID')
    title = db.Column(db.String(200), nullable=False, comment='消息标题')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    type = db.Column(db.String(20), default='system', comment='消息类型: system/application/checkin/report')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    related_id = db.Column(db.Integer, nullable=True, comment='关联ID（如申请ID、周报ID等）')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'is_read': self.is_read,
            'related_id': self.related_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<Message {self.id}>'

