from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv, find_dotenv
from flask_bootstrap import Bootstrap5
from time import time
from random import choice


# Find .env file
dotenv_path = find_dotenv()
# Load .env file entries as environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
db = SQLAlchemy()
db.init_app(app)
Bootstrap5(app)


class ToDo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250), nullable=False)
    list_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=True)
    time = db.Column(db.String(20), nullable=False)
    condition = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary


with app.app_context():
    db.create_all()


def format_list_name(list_name):
    return list_name.replace("_", " ")


@app.route("/", methods=['GET'])
def home():
    todos = db.session.execute(db.select(ToDo)).scalars().all()
    lists_tuples = ToDo.query.with_entities(ToDo.list_name).distinct().all()
    lists = [format_list_name(name[0]) for name in lists_tuples]

    if request.args.get("list_name"):
        current_list = format_list_name(request.args.get("list_name"))
    else:
        current_list = choice(lists)

    return render_template("index.html", todos=todos, lists=lists, current_list=current_list)


@app.route("/move", methods=['POST'])
def move():
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        condition = request.form.get('condition')
        way = request.form.get('way')
        list_name = request.form.get('list_name')

        update = db.session.execute(db.select(ToDo).where(ToDo.id == item_id)).scalar()
        if update:
            if condition == "to_do" and way == "up":
                update.condition = "doing"
            elif condition == "doing" and way == "up":
                update.condition = "done"
            elif condition == "doing" and way == "down":
                update.condition = "to_do"
            elif condition == "done" and way == "down":
                update.condition = "doing"
            db.session.commit()

        return redirect(url_for('home', list_name=list_name))
    return redirect(url_for('home'))


@app.route("/delete_item", methods=["POST", "DELETE"])
def delete_item():
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        list_name = request.form.get('list_name')

        delete = db.session.execute(db.select(ToDo).where(ToDo.id == item_id)).scalar()
        if delete:
            db.session.delete(delete)
            db.session.commit()

        return redirect(url_for('home', list_name=list_name))
    return redirect(url_for('home'))


@app.route("/add_item", methods=["POST"])
def add_item():
    if request.method == 'POST':
        list_name = request.form.get('list_name').replace(" ", "_")
        new_item = ToDo(
            text=request.form.get('text'),
            list_name=list_name,
            date=request.form.get('date'),
            time="{:.2f}".format(time()),
            condition=request.form.get('condition'),
            )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('home', list_name=list_name))
    return redirect(url_for('home'))


@app.route("/add_list", methods=["POST"])
def add_list():
    if request.method == 'POST':
        list_name = request.form.get('list_name').replace(" ", "_")
        new_item = ToDo(
            text="Add a new item and then delete this.",
            list_name=list_name,
            time="{:.2f}".format(time()),
            condition="to_do",
            )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('home', list_name=list_name))
    return redirect(url_for('home'))


@app.route("/delete_list", methods=["POST", "DELETE"])
def delete_list():
    if request.method == 'POST':
        list_name = request.form.get('list_name').replace(" ", "_")
        delete = db.session.execute(db.select(ToDo).where(ToDo.list_name == list_name)).scalars()
        for item in delete:
            db.session.delete(item)
        db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)

