from app import db
from datetime import datetime


class ForumCategory(db.Model):
    __tablename__ = 'forum_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, comment='分类名称')
    status = db.Column(db.Integer, default=1, comment='状态:1=启用/0=禁用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ForumPost(db.Model):
    __tablename__ = 'forum_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, comment='标题')
    content = db.Column(db.Text, nullable=False, comment='内容')
    images = db.Column(db.Text, nullable=True, comment='图片JSON数组')
    status = db.Column(db.String(20), default='pending', comment='pending/reviewed/rejected/disabled')
    reject_reason = db.Column(db.String(500), nullable=True, comment='驳回原因')
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('ForumCategory', backref='posts')
    author = db.relationship('User', backref='forum_posts')

    def to_dict(self, with_content=True):
        data = {
            'id': self.id,
            'title': self.title,
            'content': self.content if with_content else None,
            'images': self.images,
            'status': self.status,
            'reject_reason': self.reject_reason,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'author_id': self.author_id,
            'author_name': self.author.real_name if self.author else None,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if not with_content:
            data.pop('content', None)
        return data


class ForumComment(db.Model):
    __tablename__ = 'forum_comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='active', comment='active/deleted')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    post = db.relationship('ForumPost', backref='comments')
    user = db.relationship('User', backref='forum_comments')

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else None,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ForumLike(db.Model):
    __tablename__ = 'forum_likes'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    post = db.relationship('ForumPost', backref='likes')
    user = db.relationship('User', backref='forum_likes')

    __table_args__ = (
        db.UniqueConstraint('post_id', 'user_id', name='uq_forum_like_post_user'),
    )

