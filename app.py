from flask import Flask, render_template, redirect, request, make_response
from flask_login import  LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, func, desc
import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = 'seacret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///message.db'
app.config['SESSION_COOKIE_HTTPONLY'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'nologin'


class User(db.Model, UserMixin):
    __tablename__ = 't_user'
    user_id = db.Column(String(1024), primary_key=True)
    user_password = db.Column(String(1024))
    def get_id(self):
           return (self.user_id)


class Message(db.Model):
    __tablename__ = 't_message'
    message_id = db.Column(Integer, primary_key=True)
    recieved_user_id = db.Column(String(1024))
    send_user_id = db.Column(String(1024))
    message = db.Column(String(1024))
    send_time = db.Column(String(30))

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.user_id == user_id).one_or_none()


@app.route("/")
def hello():
    return render_template("index.html")


@app.route("/login")
def nologin():
    info="ログインしてください"
    return render_template("index.html", info=info)


@app.route("/login" ,methods=["POST"])
def login():
    user = Message()
    user.user_id = request.form["userid"]
    user.user_password = request.form["password"]

    exist_user = db.session.query(User).filter(User.user_id == user.user_id).one_or_none()

    if exist_user is None or not exist_user.user_password == user.user_password:
        info = "ユーザ名もしくはパスワードが間違っています"
        return render_template("index.html", info=info)
    else:
        login_user(exist_user, remember=True)
        return redirect("/main")


@app.route("/main")
@login_required
def main(info=""):
    message_list = db.session.query(Message).filter(Message.recieved_user_id == current_user.user_id).order_by(desc(Message.send_time)).all()
    for m in message_list:
        print(m)
    admin_message = ""
    if current_user.user_id == "Admin":
        admin_message = "flag{tekitou}"
    return render_template("main.html", message_list=message_list, info=info, admin_message=admin_message)


@app.route("/send" ,methods=["POST"])
@login_required
def send_message():
    message = Message()
    message.recieved_user_id = request.form["userid"]

    print(not message.recieved_user_id == current_user.user_id)

    if not message.recieved_user_id == current_user.user_id and not message.recieved_user_id == "Admin":
        info = "機能は開発中であるため、自分自身か管理者(Admin)にしか送信できません"
        return main(info=info)

    message.message = request.form["message"]
    message.send_user_id = current_user.user_id
    res = db.session.query(func.max(Message.message_id).label("max_id")).one_or_none()
    if res.max_id is None:
        message.message_id = 0
    else:
        message.message_id = res.max_id + 1

    message.send_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    print(message.message_id)
    db.session.add(message)
    db.session.commit()

    info = "メッセージを送信しました"
    return main(info=info)


@app.route("/messagedetail" ,methods=["POST"])
@login_required
def messagedetail():
    message = db.session.query(Message).filter(Message.message_id == request.form["messageid"]).first()
    if not message.recieved_user_id == current_user.user_id:
        info = "そのメッセージは参照できません"
        return main(info=info)
    resp = make_response(render_template("message.html", message=message))
    # CSPの設定
#    resp.headers['Content-Security-Policy'] = "script-src 'none' img-src 'none'"
    return resp


@app.route("/registration")
def registration():
    return render_template("registration.html")


@app.route("/registration" ,methods=["POST"])
def user_registration():
    user = User()
    user.user_id = request.form["userid"]
    user.user_password = request.form["password"]

    exist_user = db.session.query(User).filter_by(user_id=user.user_id).first()

    if exist_user == None:
        db.session.add(user)
        db.session.commit()
        info = "登録完了しました"
        return render_template("index.html", info=info)
    else:
        info = "すでにそのユーザは登録されています"
        return render_template("registration.html", info=info)


@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True, host="0.0.0.0")
