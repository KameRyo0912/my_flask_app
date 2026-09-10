from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User  # models.py から db と User をインポート

app = Flask(__name__)

# セッション・Flashメッセージ用キー（必須）
app.config['SECRET_KEY'] = 'your-secret-key-here'  

# SQLiteデータベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# models.py の db を app にバインド
db.init_app(app)

# LoginManager の初期化
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ブログ記事用のテーブル定義
class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<BlogPost {self.title}>'

# メモ用のテーブル定義
class Memo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.String(10), nullable=True)
    content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Memo {self.last_name} {self.first_name}>'

# アプリ起動時にテーブルを自動作成
with app.app_context():
    db.create_all()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('blog_index'))  # 管理者向けのリダイレクト先
            else:
                return redirect(url_for('index'))      # 一般ユーザー向けのリダイレクト先
        else:
            flash('ユーザー名またはパスワードが正しくありません。')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birth_date = request.form.get('birth_date')
        content = request.form.get('content')

        if first_name and last_name:
            new_memo = Memo(first_name=first_name, last_name=last_name, birth_date=birth_date, content=content)
            db.session.add(new_memo)
            db.session.commit()
            return redirect(url_for('index'))

    memos = Memo.query.all()
    return render_template('index.html', memos=memos)

@app.route('/about')
def about():
    memos = Memo.query.all()
    return render_template('about.html', memos=memos)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    memo = Memo.query.get_or_404(id)

    if request.method == 'POST':
        memo.last_name = request.form.get('last_name')
        memo.first_name = request.form.get('first_name')
        memo.content = request.form.get('content')
        db.session.commit()
        return redirect(url_for('about'))

    return render_template('edit.html', memo=memo)

@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog_detail.html', post=post)

@app.route('/blog')
def blog_index():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog_index.html', posts=posts)

@app.route('/blog/new', methods=['GET', 'POST'])
@login_required  # ログイン必須化
def blog_new():
    if request.method == 'POST':
        title = request.form.get('title')
        body = request.form.get('body')

        if title and body:
            new_post = BlogPost(title=title, body=body)
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('blog_index'))

    return render_template('blog_new.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)