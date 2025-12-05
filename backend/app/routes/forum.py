from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.forum import ForumCategory, ForumPost, ForumComment, ForumLike
from app.models.message import Message
from app.utils.decorators import token_required, role_required
from app.utils.errors import APIError
from sqlalchemy import or_
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
from uuid import uuid4

forum_bp = Blueprint('forum', __name__)


def _parse_pagination():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    return page, per_page


def _ensure_category(category_id):
    category = ForumCategory.query.get(category_id)
    if not category or category.status != 1:
        raise APIError('分类不可用', 400, 'CATEGORY_INVALID')
    return category


def _ensure_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if post.status in ['disabled', 'rejected']:
        raise APIError('帖子不可用', 400, 'POST_DISABLED')
    return post


def _check_sensitive(text):
    if not text:
        return
    if not current_app.config.get('FORUM_SENSITIVE_CHECK_ENABLED'):
        return
    words = current_app.config.get('FORUM_SENSITIVE_WORDS') or []
    for w in words:
        if w and w in text:
            raise APIError('包含敏感词，发布失败', 400, 'SENSITIVE_BLOCK')


def _save_image(file_storage):
    if not file_storage or file_storage.filename == '':
        raise APIError('文件为空', 400, 'EMPTY_FILE')
    filename = secure_filename(file_storage.filename)
    ext = filename.rsplit('.', 1)[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png']:
        raise APIError('仅支持jpg/png', 400, 'INVALID_IMAGE_TYPE')
    upload_root = current_app.config['UPLOAD_FOLDER']
    now = datetime.utcnow()
    relative_dir = os.path.join('forum', str(now.year), f"{now.month:02d}")
    target_dir = os.path.join(upload_root, relative_dir)
    os.makedirs(target_dir, exist_ok=True)
    final_name = f"{now.strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}.{ext}"
    path = os.path.join(target_dir, final_name)
    file_storage.save(path)
    return os.path.join(relative_dir, final_name).replace('\\', '/')


@forum_bp.route('/categories', methods=['GET'])
@token_required
def list_categories():
    categories = ForumCategory.query.order_by(ForumCategory.created_at.desc()).all()
    return jsonify({'success': True, 'data': [c.to_dict() for c in categories]}), 200


@forum_bp.route('/categories', methods=['POST'])
@role_required('admin', 'teacher')
def create_category():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        raise APIError('分类名称不能为空', 400, 'CATEGORY_NAME_REQUIRED')
    if ForumCategory.query.filter_by(name=name).first():
        raise APIError('分类名称已存在', 400, 'CATEGORY_NAME_EXISTS')
    category = ForumCategory(name=name, status=data.get('status', 1))
    db.session.add(category)
    db.session.commit()
    return jsonify({'success': True, 'data': category.to_dict()}), 201


@forum_bp.route('/categories/<int:category_id>', methods=['PUT'])
@role_required('admin', 'teacher')
def update_category(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    data = request.get_json() or {}
    if 'name' in data:
        name = (data.get('name') or '').strip()
        if not name:
            raise APIError('分类名称不能为空', 400, 'CATEGORY_NAME_REQUIRED')
        exists = ForumCategory.query.filter(ForumCategory.id != category_id, ForumCategory.name == name).first()
        if exists:
            raise APIError('分类名称已存在', 400, 'CATEGORY_NAME_EXISTS')
        category.name = name
    if 'status' in data:
        category.status = 1 if str(data.get('status')) == '1' else 0
    db.session.commit()
    return jsonify({'success': True, 'data': category.to_dict()}), 200


@forum_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@role_required('admin', 'teacher')
def delete_category(category_id):
    category = ForumCategory.query.get_or_404(category_id)
    in_use = ForumPost.query.filter_by(category_id=category_id).first()
    if in_use:
        raise APIError('该分类下仍有帖子，不能删除', 400, 'CATEGORY_IN_USE')
    db.session.delete(category)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'}), 200


@forum_bp.route('/posts', methods=['GET'])
@token_required
def list_posts():
    page, per_page = _parse_pagination()
    status = request.args.get('status')
    category_id = request.args.get('category_id', type=int)
    keyword = (request.args.get('keyword') or '').strip()
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    query = ForumPost.query
    # 学生只能看已审核的
    if request.current_user.role == 'student':
        query = query.filter(ForumPost.status == 'reviewed')
    elif status:
        query = query.filter(ForumPost.status == status)

    if category_id:
        query = query.filter(ForumPost.category_id == category_id)
    if keyword:
        like_key = f"%{keyword}%"
        query = query.filter(or_(ForumPost.title.like(like_key), ForumPost.content.like(like_key)))
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time)
            query = query.filter(ForumPost.created_at >= start_dt)
        except ValueError:
            raise APIError('start_time格式应为YYYY-MM-DDTHH:MM:SS', 400, 'INVALID_TIME')
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time)
            query = query.filter(ForumPost.created_at <= end_dt)
        except ValueError:
            raise APIError('end_time格式应为YYYY-MM-DDTHH:MM:SS', 400, 'INVALID_TIME')

    pagination = query.order_by(ForumPost.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for p in pagination.items:
        data = p.to_dict(with_content=False)
        # 裁剪摘要
        if p.content:
            data['summary'] = p.content[:120]
        items.append(data)

    return jsonify({
        'success': True,
        'data': {
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    }), 200


@forum_bp.route('/posts', methods=['POST'])
@token_required
def create_post():
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    category_id = data.get('category_id')
    images = data.get('images') or []

    if not title or len(title) < 5 or len(title) > 50:
        raise APIError('标题需5-50字', 400, 'INVALID_TITLE')
    if not content or len(content) < 20:
        raise APIError('内容需至少20字', 400, 'INVALID_CONTENT')
    if not category_id:
        raise APIError('分类必选', 400, 'CATEGORY_REQUIRED')

    _ensure_category(category_id)

    _check_sensitive(title)
    _check_sensitive(content)

    images_json = json.dumps(images, ensure_ascii=False) if images else None
    post = ForumPost(
        title=title,
        content=content,
        images=images_json,
        category_id=category_id,
        author_id=request.current_user.id,
        status='pending'
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'success': True, 'data': post.to_dict()}), 201


@forum_bp.route('/posts/<int:post_id>', methods=['GET'])
@token_required
def get_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if post.status != 'reviewed' and request.current_user.role == 'student':
        raise APIError('无权查看该帖子', 403)
    return jsonify({'success': True, 'data': post.to_dict(with_content=True)}), 200


@forum_bp.route('/posts/<int:post_id>/like', methods=['POST'])
@token_required
def like_post(post_id):
    post = _ensure_post(post_id)
    exists = ForumLike.query.filter_by(post_id=post_id, user_id=request.current_user.id).first()
    if exists:
        raise APIError('已点赞', 400, 'ALREADY_LIKED')
    like = ForumLike(post_id=post_id, user_id=request.current_user.id)
    post.like_count += 1
    db.session.add(like)
    db.session.commit()
    return jsonify({'success': True, 'data': {'like_count': post.like_count}}), 200


@forum_bp.route('/posts/<int:post_id>/comments', methods=['GET'])
@token_required
def list_comments(post_id):
    _ensure_post(post_id)
    page, per_page = _parse_pagination()
    pagination = ForumComment.query.filter_by(post_id=post_id, status='active') \
        .order_by(ForumComment.created_at.desc()) \
        .paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'success': True,
        'data': {
            'items': [c.to_dict() for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    }), 200


@forum_bp.route('/posts/<int:post_id>/comments', methods=['POST'])
@token_required
def create_comment(post_id):
    post = _ensure_post(post_id)
    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    if not content or len(content) > 200:
        raise APIError('评论需1-200字', 400, 'INVALID_COMMENT')

    _check_sensitive(content)

    comment = ForumComment(
        post_id=post_id,
        user_id=request.current_user.id,
        content=content
    )
    post.comment_count += 1
    db.session.add(comment)
    db.session.commit()
    return jsonify({'success': True, 'data': comment.to_dict(), 'comment_count': post.comment_count}), 201


@forum_bp.route('/posts/<int:post_id>/moderate', methods=['POST'])
@role_required('admin', 'teacher')
def moderate_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    data = request.get_json() or {}
    action = data.get('action')
    msg_title = None
    msg_content = None
    if action == 'approve':
        post.status = 'reviewed'
        post.reject_reason = None
        msg_title = '帖子审核通过'
        msg_content = f'您的帖子《{post.title}》已通过审核'
    elif action == 'reject':
        reason = (data.get('reason') or '').strip()
        if not reason:
            raise APIError('请填写驳回原因', 400, 'REJECT_REASON_REQUIRED')
        post.status = 'rejected'
        post.reject_reason = reason
        msg_title = '帖子审核未通过'
        msg_content = f'您的帖子《{post.title}》被驳回，原因：{reason}'
    elif action == 'disable':
        post.status = 'disabled'
        msg_title = '帖子已下架'
        msg_content = f'您的帖子《{post.title}》已被下架'
    else:
        raise APIError('无效操作', 400, 'INVALID_ACTION')
    if msg_title:
        message = Message(
            user_id=post.author_id,
            title=msg_title,
            content=msg_content,
            type='forum',
            related_id=post.id
        )
        db.session.add(message)
    db.session.commit()
    return jsonify({'success': True, 'data': post.to_dict()}), 200


@forum_bp.route('/posts/<int:post_id>', methods=['DELETE'])
@role_required('admin', 'teacher')
def delete_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'}), 200


@forum_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@role_required('admin', 'teacher')
def delete_comment(comment_id):
    comment = ForumComment.query.get_or_404(comment_id)
    comment.status = 'deleted'
    db.session.commit()
    return jsonify({'success': True, 'message': '删除成功'}), 200


@forum_bp.route('/comments', methods=['GET'])
@role_required('admin', 'teacher')
def list_all_comments():
    page, per_page = _parse_pagination()
    post_id = request.args.get('post_id', type=int)
    query = ForumComment.query
    if post_id:
        query = query.filter_by(post_id=post_id)
    pagination = query.order_by(ForumComment.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'success': True,
        'data': {
            'items': [c.to_dict() for c in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    }), 200


@forum_bp.route('/upload', methods=['POST'])
@token_required
def upload_image():
    """论坛图片上传，限制jpg/png，单张<=5MB"""
    try:
        if 'file' not in request.files:
            raise APIError('没有上传文件', 400, 'NO_FILE')
        file = request.files['file']
        size = request.content_length or 0
        max_size = current_app.config.get('FORUM_MAX_IMAGE_SIZE_MB', 5) * 1024 * 1024
        if size > max_size:
            raise APIError('文件过大，限制5MB', 400, 'FILE_TOO_LARGE')
        path = _save_image(file)
        return jsonify({'success': True, 'data': {'path': path}}), 200
    except APIError as e:
        raise e
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Upload image error: {str(e)}', exc_info=True)
        raise APIError('上传失败', 500)

