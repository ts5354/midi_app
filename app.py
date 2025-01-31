from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os

# .env ファイルを読み込む
load_dotenv()

app = Flask(__name__)

# 環境変数から設定を取得
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# データベースモデル
class MidiFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)  # ジャンルを追加

# アップロードフォルダの作成
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# **修正：Flask アプリコンテキスト内でデータベースを作成**
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    genre_filter = request.args.get('genre', '')
    genres = db.session.query(MidiFile.genre).distinct()
    if genre_filter:
        files = MidiFile.query.filter_by(genre=genre_filter).all()
    else:
        files = MidiFile.query.all()
    return render_template('index.html', files=files, genres=[g[0] for g in genres], selected_genre=genre_filter)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    genre = request.form.get('genre')

    if file.filename == '' or not genre:
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_file = MidiFile(filename=filename, genre=genre)
        db.session.add(new_file)
        db.session.commit()

        return redirect(url_for('index'))

@app.route('/download/<int:file_id>')
def download_file(file_id):
    file = MidiFile.query.get(file_id)
    if file:
        return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename, as_attachment=True)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
