from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_required, login_user, LoginManager, UserMixin, logout_user, current_user

###Beginning of upload definitions###
#UPLOAD_FOLDER = 'home/NSPtefft/mysite/assets'
ALLOWED_EXTENSIONS = {'csv',}
SECURE_USER = 'Natsume'
###End of upload definitions###

###App and configs###
#app = Flask(__name__)
#app.config["DEBUG"] = True
#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
###End App and configs###

###Begin defining the Database and Users###
#SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
#    username="jtefft",
#    password="patratpatrol",
#    hostname="NSPtefft.mysql.pythonanywhere-services.com",
#    databasename="NSPtefft$Inventory",
#)
#app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
#app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy()


SECRET_KEY = "JfthKLFrgdhBL3GyhCySrdgLD8G123A"
login_manager = LoginManager()


class User(UserMixin, db.Model):

    __tablename__ = "users"
    __bind_key__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16))
    passkey = db.Column(db.String(128))

    def get_id(self):
        return self.username

    def validate_user(self, password):
        return check_password_hash(self.passkey, password)


class Item(db.Model):

    __tablename__ = "items"
    __bind_key__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True) #true key
    sku = db.Column(db.String(16), unique=True, nullable=False) #this SHOULD function as a key as well
    qb_count = db.Column(db.Integer, nullable=False) #QB count, imported from file
    description = db.Column(db.String(128), nullable=False) #QB description, imported
    vendor = db.Column(db.String(64)) #vendor, imported
    location = db.Column(db.String(32), nullable=False) #main box location, imported
    location_index = db.Column(db.Integer, nullable=False) #index for ordering presentation of SKUs
    backstock = db.Column(db.String(16)) #location of backstock, imported
    count_1 = db.Column(db.Integer) #unspecified to begin
    count_2 = db.Column(db.Integer) #unspecified to begin
    count_3 = db.Column(db.Integer) #unspecified to begin
    count_4 = db.Column(db.Integer) #unspecified to begin
    final_count = db.Column(db.Integer) #unspecified to begin

class Assignments(db.Model):

    __tablename__ = "assignments"
    __bind_key__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True) #true key
    location = db.Column(db.String(32), nullable=False)
    username = db.Column(db.String(32))
    assignment_type = db.Column(db.Integer, nullable=False) #1 or 2 or 3 or 4
    complete = db.Column(db.Boolean, nullable=False) #-1 or int starting at 1

class Locations(db.Model):
    __tablename__ = 'locations'
    __bind_key__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True) #true key
    location = db.Column(db.String(32), unique=True, nullable=False)

###End of defining Database and Users###
