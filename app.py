from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pastes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
db = SQLAlchemy(app)

class Paste(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.route('/')
def index():
    pastes = Paste.query.order_by(Paste.created_at.desc()).all()
    return render_template('index.html', pastes=pastes)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        language = request.form.get('language')
        
        if not title or not content:
            return redirect(url_for('create'))
            
        paste = Paste(title=title, content=content, language=language)
        db.session.add(paste)
        db.session.commit()
        
        return redirect(url_for('view_paste', paste_id=paste.id))
    
    return render_template('create.html')

@app.route('/paste/<int:paste_id>')
def view_paste(paste_id):
    paste = Paste.query.get_or_404(paste_id)
    paste.views += 1
    db.session.commit()
    return render_template('view_paste.html', paste=paste)

@app.route('/paste/<int:paste_id>/raw')
def view_raw_paste(paste_id):
    paste = Paste.query.get_or_404(paste_id)
    paste.views += 1
    db.session.commit()
    response = make_response(paste.content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000) 
