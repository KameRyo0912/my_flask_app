from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# SQLiteデータベースの設定（instance/app.db に保存されます）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# データベースのテーブル定義（Memoモデル）
class Memo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.String(10), nullable=True)  # YYYY-MM-DD形式の文字列として保存
    content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Memo {self.last_name} {self.first_name}>'

# アプリ起動時にテーブルを自動作成
with app.app_context():
    db.create_all()

# トップページ（一覧表示 ＆ メモ追加機能）
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

    # DBから全メモを取得
    memos = Memo.query.all()
    return render_template('index.html', memos=memos)


@app.route('/about')
def about():
    # DBから全メモを取得して about.html に渡す
    memos = Memo.query.all()
    return render_template('about.html', memos=memos)

# メモの編集画面 ＆ 更新処理
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    # IDに該当するメモをDBから取得（存在しない場合は404エラー）
    memo = Memo.query.get_or_404(id)

    if request.method == 'POST':
        # フォーム送信された値で更新
        memo.last_name = request.form.get('last_name')
        memo.first_name = request.form.get('first_name')
        memo.content = request.form.get('content')

        # データベースに保存
        db.session.commit()
        return redirect(url_for('about'))  # 編集後は一覧画面（about等）へリダイレクト

    # GETアクセスの場合は既存のデータを入れた編集画面を表示
    return render_template('edit.html', memo=memo)
@app.route('/page_2026-09-08')
def page_2026_09_08():
    # DBから全メモを取得して about.html に渡す
    memos = Memo.query.all()
    return render_template('page_2026-09-08.html', memos=memos)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)