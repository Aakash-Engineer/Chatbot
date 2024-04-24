from flask import Flask, request, jsonify, render_template, session

app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Login route
@app.route('/login')
def login():
    return render_template('login.html')

# Register route

@app.route('/register')
def register():

    # if method == 'POST':
    return render_template('register.html')



# Chat route
@app.route('/chat')
def chat():
    return render_template('chat.html')

# @app.route('/chat/<chatID>')
# def chat(chatID):
#     return render_template('chat.html', chatID=chatID)


if __name__ == '__main__':
    app.run(debug=True)