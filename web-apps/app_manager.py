from flask import Flask, flash, redirect, render_template, request, url_for, session, send_from_directory
from flask_login import login_required, login_user, LoginManager, UserMixin, logout_user, current_user
import inventory_count_app
from flask_sqlalchemy import SQLAlchemy
from inventory_count_app import inventory
from inventory_count_database import login_manager as inv_login_manager
from inventory_count_database import db as inv_db
from inventory_count_database import User as inv_User
import bc_sales_app
from bc_sales_app import bc_sales
from bc_sales_database import db as bc_db
from bc_sales_database import login_manager as bc_login_manager
from bc_sales_database import User as bc_User
from sqlalchemy.exc import StatementError


###Beginning of upload definitions###
UPLOAD_FOLDER = 'home/jtefft/mysite/assets'
###End of upload definitions###


###App, blueprints, and configs###
app = Flask(__name__)


SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="jtefft",
    password="patratpatrol",
    hostname="NSPtefft.mysql.pythonanywhere-services.com",
    databasename='jtefft$default',
    )

SQLALCHEMY_BINDS = {'inventory':"mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="jtefft",
    password="patratpatrol",
    hostname="jtefft.mysql.pythonanywhere-services.com",
    databasename='jtefft$Inventory',
    ),
    'bc_sales':"mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="jtefft",
    password="patratpatrol",
    hostname="jtefft.mysql.pythonanywhere-services.com",
    databasename='jtefft$BigCommerceSales',
    ),}

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_BINDS"] = SQLALCHEMY_BINDS
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "#/j{Py%&H_s6h?i,vv$(aHjL48?CXiV3mN&g[2hochD8{vP1hlwRYw(7kC{51SYI1l"

db = SQLAlchemy(app)

app.register_blueprint(inventory)
app.register_blueprint(bc_sales)

bc_login_manager.init_app(app)
inv_login_manager.init_app(app)

@bc_login_manager.user_loader
def bc_load_user(user_id):
    return bc_User.query.filter_by(username=user_id).first()

@inv_login_manager.user_loader
def inv_load_user(user_id):
    return inv_User.query.filter_by(username=user_id).first()

app.config["DEBUG"] = True
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



@app.route("/", methods=['GET', 'POST'])
def index():

    try:
        if request.method == "GET":
            return render_template("choose_app_page.html")
    except StatementError:
        db.session.rollback()
    action = request.form["submit_control"]
    if action == "Inventory Count App":
        return redirect(url_for('inventory.login'))
    elif action == "BC Sales App":
        return redirect(url_for('bc_sales.login'))
    return redirect(url_for('index'))

