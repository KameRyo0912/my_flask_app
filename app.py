import os
from datetime import datetime
from werkzeug.utils import secure_filename
# 1. session をインポートに追加
from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User  # models.py から db と User をインポート
from PIL import Image

app = Flask(__name__)
# 画像の保存先フォルダ設定
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# セッション・Flashメッセージ用キー
app.config['SECRET_KEY'] = 'your-secret-key-here'

# SQLiteデータベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# models.py の db を app にバインド
db.init_app(app)

# LoginManager の初期化（デフォルトのログイン画面指定）
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'web_app_login'  # 未ログイン時はWebアプリ用ログインへ飛ばす

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
# --- 新規ユーザー登録画面 ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 既存ユーザーの重複チェック
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('そのユーザー名はすでに使用されています。')
            return redirect(url_for('register'))
        
        # 新しいユーザーを作成して保存
        new_user = User(username=username)
        new_user.set_password(password)  # パスワードのハッシュ化（models.pyのメソッドを利用）
        db.session.add(new_user)
        db.session.commit()
        
        flash('ユーザー登録が完了しました。ログインしてください。')
        return redirect(url_for('web_app_login'))
        
    return render_template('register.html')
# --- 1. Webアプリ専用 ログイン画面 ---
@app.route('/web_app/login', methods=['GET', 'POST'])
def web_app_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            # ログイン成功時はWebアプリ本体（/web_app）へ移動
            return redirect(url_for('web_app_index'))
        else:
            flash('ユーザー名またはパスワードが正しくありません。')
    return render_template('web_app_login.html')

# ログアウト処理
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('web_app_login'))

# --- 2. Webアプリ本体（メモ機能画面・ログイン保護あり） ---
@app.route('/web_app', methods=['GET', 'POST'])
@login_required
def web_app_index():
    # メインメニューを経由していない直リンクアクセスの場合は拒否
    if not session.get('from_main_menu'):
        flash('メインメニューからアクセスしてください。')
        return redirect(url_for('index'))
    
    # 処理完了後、または別のページへ移動するときにフラグを消したい場合はここでpopすることも可能
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birth_date = request.form.get('birth_date')
        content = request.form.get('content')
        if first_name and last_name:
            new_memo = Memo(first_name=first_name, last_name=last_name, birth_date=birth_date, content=content)
            db.session.add(new_memo)
            db.session.commit()
            return redirect(url_for('web_app_index'))
    memos = Memo.query.all()
    return render_template('web_app.html', memos=memos)

# --- 3. トップページ（後でメインメニューに変更予定） ---
# --- トップページ（メインメニュー画面） ---
@app.route('/')
def index():
    session['from_main_menu'] = True
    return render_template('index.html')

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

# --- 4. ブログ機能 ---
@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('blog_detail.html', post=post)

# --- ブログ一覧画面 ---
@app.route('/blog')
def blog_index():
    # メインメニューを経由していない場合はメインメニューへ戻す
    if not session.get('from_main_menu'):
        flash('メインメニューからアクセスしてください。')
        return redirect(url_for('index'))
        
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('blog_index.html', posts=posts)

@app.route('/blog/new', methods=['GET', 'POST'])
@login_required
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
# --- ブログ記事の編集 ---
@app.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def blog_edit(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form.get('title')
        post.body = request.form.get('body')
        db.session.commit()
        flash('記事を更新しました。')
        return redirect(url_for('blog_detail', post_id=post.id))
    return render_template('blog_edit.html', post=post)

# --- ブログ記事の削除 ---
@app.route('/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def blog_delete(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('記事を削除しました。')
    return redirect(url_for('blog_index'))
# --- 画像アップロード用 API ---
@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルがありません'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ファイルが選択されていません'}), 400

    if file:
        filename = secure_filename(file.filename)
        save_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], save_name)

        # --- 方法3: Python(Pillow)で画像リサイズ保存 ---
        img = Image.open(file)
        
        # スマホ写真の回転情報（Exif）を考慮してリサイズ
        max_size = (1200, 1200)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        img.save(filepath)

        image_url = url_for('static', filename=f'uploads/{save_name}')
        return jsonify({'location': image_url})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)