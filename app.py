from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import os

app=Flask(__name__)

# Get the secret key from the environment variable
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')


CORS(app)
db=SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins=os.getenv('CORS_ALLOWED_ORIGINS'))

# Database classes
class User(db.Model):
    name=db.Column(db.String(80))
    email=db.Column(db.String(80), primary_key=True)
    password=db.Column(db.String(80))

    def __init__(self, email, name, password):
        self.name=name
        self.email=email
        self.password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


    
class Session(db.Model):        
    session_id=db.Column(db.String(80), primary_key=True)
    email=db.Column(db.String(80), db.ForeignKey('user.email', ondelete='CASCADE'))

    def __init__(self, session_id, email):
        self.session_id=session_id
        self.email=email


class Message(db.Model):
    message_id=db.Column(db.String(80),primary_key=True)
    query=db.Column(db.String(500))
    response=db.Column(db.String(500))
    session_id=db.Column(db.String(80), db.ForeignKey('session.session_id', ondelete='CASCADE'))

    def __init__(self, message_id, query,response,session_id):
        self.message_id=message_id
        self.query=query
        self.response=response
        self.session_id=session_id
    def to_dict(self):
        return {
            'message_id': self.message_id,
            'query': self.query,
            'response': self.response,
            'session_id': self.session_id
        }


with app.app_context():
    db.create_all()



# Routes configuration
@app.route('/')
def index():
    if 'email' in session:
        # check if user exist in the database
        user = User.query.filter_by(email=session['email']).first()

        if user:
            return render_template('index.html', name=session['name'], email=session['email'])
        else:
            return redirect(url_for('login'))
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
            session_name=user.name
            session_email=user.email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid email or password')
    else:
        return render_template('login.html')

# Chat route
@app.route('/chat')
def chat():
    # fetch all messages of a user from the message table using the email set in the session variable
    # A user can have multiple sessions, so fetch all the sessions of the user from the session table 
    # and also for each session fetch the first message from the message table

    sessions = db.session.query(Session).filter_by(email=session['email']).all()
    session_ids = [session.session_id for session in sessions]
    messages = []
    for session_id in session_ids:
        message = db.session.query(Message).filter_by(session_id=session_id).first()
        messages.append(message)
    message_dicts = [message.to_dict() for message in messages]
    # reverse the list of messages
    # message_dicts.reverse()
    return render_template('chat.html',messages=message_dicts, name=session['name'], email=session['email'])
    

@app.route('/chat/<id>')
def chat_history(id):
    messages = db.session.query(Message).filter_by(session_id=id).all()
    message_dicts = [message.to_dict() for message in messages]
    return render_template('chat_history.html',messages=message_dicts, name=session['name'], email=session['email'])
   
@app.route('/clear_chats')
def clear_chats():
    # Delete all sessions of a user from session table
    
    if 'email' in session:
        # delete all sessions of the user
        # check if user exist in the database
        user = User.query.filter_by(email=session['email']).first()
        if user:
            db.session.query(Session).filter_by(email=session['email']).delete()
            db.session.commit()
            return redirect(url_for('chat'))
        return redirect(url_for('chat'))
    
    return redirect(url_for('login'))





# Websocket configuration

@socketio.on('connection_id', namespace='/chat')
def handle_connection_id(connection_id):
    print(f"Received connection ID: {connection_id}")




@socketio.on('message', namespace='/chat')
def handle_message(data):
    # connection_id = data['connection_id']  # Get the connection_id from the data dictionary
    socket_id = data['socket_id']
    message_id = data['message_id']
    message_text = data['message_text']
    email=data['email']

    # Check if the socket_id exists in the session table
    existing_sessions = Session.query.filter_by(session_id=socket_id).first()
    if existing_sessions:
        # Store the message in the message table
        message = Message(message_id=message_id, query=message_text, response='hello dear', session_id=socket_id)
        db.session.add(message)
        db.session.commit()
    else:

        existing_sessions = Session(session_id=socket_id, email=email)
        db.session.add(existing_sessions)
        db.session.commit()
        message = Message(message_id=message_id, query=message_text, response='hello dear', session_id=socket_id)
        db.session.add(message)
        db.session.commit()

    # send hllo back to the client
    emit('message', {'message_text': 'hello from server'}, room=socket_id)


    

if __name__ == '__main__':
    app.run(debug=True)