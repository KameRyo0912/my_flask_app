from app import app
from models import db, User

with app.app_context():
    # すでに同じユーザー名が存在しないか確認
    admin_user = User.query.filter_by(username='admin').first()
    
    if not admin_user:
        # 新しい管理者ユーザーを作成
        admin_user = User(username='admin', is_admin=True)
        # パスワードをハッシュ化してセット（お好みのパスワードに変更してください）
        admin_user.set_password('admin123')
        
        db.session.add(admin_user)
        db.session.commit()
        print("管理者ユーザー (admin) を作成しました！")
    else:
        print("管理者ユーザー (admin) は既に存在します。")