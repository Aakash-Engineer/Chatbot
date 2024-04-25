from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import os

app=Flask(__name__)
database_uri=os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri;
app.secret_key=os.environ.get('SECRET_KEY')
db=SQLAlchemy(app)

# Database class
class User(db.Model):
    name=db.Column(db.String)
    email=db.Column(db.String, primary_key=True)
    password=db.Column(db.String)

    def __init__(self, email, name, password):
        self.name=name
        self.email=email
        self.password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    
with app.app_context():
    db.create_all()



# Routes configuration
@app.route('/')
def index():
    if 'email' in session:
        return render_template('index.html', name=session['name'], email=session['email'])
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST']) # Register route
def register():
    if request.method=='POST':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']

        new_user=User(email, name, password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    
    return render_template('register.html')
    

@app.route('/login', methods=['POST', 'GET']) # Login route
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']

        user=User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email']=email
            session['name']=user.name
            return redirect(url_for('index'))
        else:
            return render_template('/login', error='Invalid email or password')
    else:
        return render_template('login.html')

# Chat route
@app.route('/chat')
def chat():
    return render_template('chat.html', name=session['name'], email=session['email'])

# @app.route('/chat/<chatID>')
# def chat(chatID):
#     return render_template('chat.html', chatID=chatID)


if __name__ == '__main__':
    app.run(debug=True)