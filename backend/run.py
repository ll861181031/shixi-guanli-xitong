from app import create_app, db
from app.models import User
from app.utils.logger import setup_logger
import os

app = create_app()
setup_logger(app)

@app.cli.command('init-db')
def init_db():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        
        # 创建默认管理员账户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                real_name='系统管理员',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('默认管理员账户已创建: admin/admin123')
        else:
            print('数据库已初始化')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

