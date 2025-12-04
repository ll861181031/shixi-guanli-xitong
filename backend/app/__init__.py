from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import inspect, text
import os

db = SQLAlchemy()

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    from config import Config
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 确保数据库结构所需列存在
    with app.app_context():
        ensure_user_permissions_column()
    
    # 创建上传目录
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.positions import positions_bp
    from app.routes.applications import applications_bp
    from app.routes.checkins import checkins_bp
    from app.routes.weekly_reports import weekly_reports_bp
    from app.routes.statistics import statistics_bp
    from app.routes.users import users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(positions_bp, url_prefix='/api/positions')
    app.register_blueprint(applications_bp, url_prefix='/api/applications')
    app.register_blueprint(checkins_bp, url_prefix='/api/checkins')
    app.register_blueprint(weekly_reports_bp, url_prefix='/api/weekly-reports')
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # 注册错误处理
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)
    
    return app

def ensure_user_permissions_column():
    """确保 users 表包含 permissions 字段"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'permissions' not in columns:
        db.session.execute(text(
            "ALTER TABLE users ADD COLUMN permissions TEXT COMMENT '权限配置(JSON)'"
        ))
        db.session.execute(text(
            "UPDATE users SET permissions='[]' WHERE permissions IS NULL"
        ))
        db.session.commit()

