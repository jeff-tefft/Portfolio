
# The Flask app for creating inventory counts
from pathlib import Path
import os
from flask import Flask, flash, redirect, render_template, request, url_for, session, send_from_directory, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_required, login_user, LoginManager, UserMixin, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from csv import reader, writer
from inventory_count_database import db, User, Item, Assignments, Locations, ALLOWED_EXTENSIONS, SECURE_USER

inventory = Blueprint('inventory', __name__, url_prefix='/inv')

#app = Flask(__name__)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    try:
        return_user = User.query.filter_by(username=user_id).first()
    except:
        db.session.rollback()
        return_user = User.query.filter_by(username=user_id).first()
    return return_user


###Begin defining utility functions###
def render_loggedin_template(render_template_path, **kwargs):
    return render_template(str(render_template_path), **kwargs)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def file_to_item_database(filepath):

    locations_data = Locations.query.filter().all()
    locations = []
    for location in locations_data:
        locations.append(location.location)

    csvfile = open(filepath, encoding='cp1252')
    csvdata = list(reader(csvfile, dialect='excel'))

    #sets up column headings to feed into dictionary, case insensitive, order insensitive
    basic_headers = {}
    basic_headers['sku'] = {'value':'invalid', 'alternates':('sku', 'item', 'item id', 'item_id', 'itemid')}
    basic_headers['qb_count'] = {'value':'0', 'alternates':('qb_count', 'qb count', 'accounting count', 'quickbooks count')}
    basic_headers['description'] = {'value':'', 'alternates':('description', 'desc', 'item desc', 'item description')}
    basic_headers['vendor'] = {'value':'', 'alternates':('vendor', 'company', 'seller',)}
    basic_headers['location'] = {'value':'', 'alternates':('location', 'place',)}
    basic_headers['location_index'] = {'value':-1, 'alternates':('location_index', 'location index', 'loc_ind', 'loc ind')}
    basic_headers['backstock'] = {'value':'', 'alternates':('backstock', 'has_backstock', 'has backstock', 'hasbackstock')}
    basic_headers['count_1'] = {'value':'', 'alternates':('count_1', 'count 1', '1', 'one', 'count one', 'count1')}
    basic_headers['count_2'] = {'value':'', 'alternates':('count_2', 'count 2', '2', 'two', 'count two', 'count2')}
    basic_headers['count_3'] = {'value':'', 'alternates':('count_3', 'count 3', '3', 'three', 'count three', 'count3')}
    basic_headers['count_4'] = {'value':'', 'alternates':('count_4', 'count 4', '4', 'four', 'count four', 'count4')}
    basic_headers['final_count'] = {'value':'', 'alternates':('final_count', 'final count', 'count_final', 'count final', 'finalcount', 'countfinal', 'final')}


    csv_headers = csvdata[0]
    #pads basic headers to allow default behavior in next for loop
    incrementer = 0
    while len(csv_headers) > len(basic_headers.keys()):
        basic_headers[str(incrementer)] = {}
        basic_headers[str(incrementer)]['value'] = None
        basic_headers[str(incrementer)]['alternates'] = (None,)
        incrementer += 1
    headers = {}
    for csv_header, default in zip(csv_headers, list(basic_headers.keys())[:len(csv_headers)]):
        if csv_header in (None, '', 'NULL', 'None'):
                headers[default] = basic_headers[default]['value']

        for basic_header in basic_headers:
            alternates = basic_headers[basic_header]['alternates']
            if csv_header.lower() in alternates:
                headers[basic_header] = basic_headers[basic_header]['value']
                break
        else:
            headers[csv_header.lower()] = ''

    #put all headers not in upload file into submit_dict so that data will be consistent
    #later check against default values allows in-database data to override if item already present
    for header in basic_headers:
        if header not in headers:
            headers[header] = basic_headers[header]['value']

    for row in csvdata[1:]:
        submitdict = {}
        for header, value in zip(headers.keys(), row):
            if value == None:
                submitdict[header] = headers[header]
            else:
                submitdict[header] = value
            if type(submitdict[header]) == type('string'):
                submitdict[header] = clean_basic_text(submitdict[header])
                if header == 'sku':
                    submitdict[header] = clean_sku(submitdict[header])
        for extra_header in headers.keys():
            if extra_header not in submitdict.keys():
                submitdict[extra_header] = headers[extra_header]

        item = Item.query.filter(Item.sku == submitdict['sku']).first()
        if not item:
            item = Item(sku=str(submitdict['sku']), qb_count=submitdict['qb_count'],
                description=submitdict['description'], vendor=submitdict['vendor'], location=submitdict['location'],
                location_index=submitdict['location_index'], backstock=submitdict['backstock'],
                count_1=-1, count_2=-1, count_3=-1, count_4=-1, final_count=-1)

            if (submitdict['location'] not in (None, 'NULL', 'None', '')):
                if (submitdict['location'] not in locations):
                    locations.append(submitdict['location'])
                    db.session.add(Locations(location=submitdict['location']))
            db.session.add(item)
        else:
            for key, value in submitdict.items():
                if value != basic_headers[key]['value']:
                    if type(value) == type('abc'):
                        setattr(item, key, clean_basic_text(value))
                    else: setattr(item, key, value)
    db.session.commit()

def file_to_user_database(filepath):
    #delete the current items in the database
    num_rows_deleted = db.session.query(User).filter(User.username != SECURE_USER).delete()
    db.session.commit()

    csvfile = open(filepath, encoding='cp1252')
    csvdata = list(reader(csvfile, dialect='excel'))
    headers = {'username':'invalid', 'password':'invalid',}
    for row in csvdata[1:]:
        submitdict = {}
        for header, value in zip(headers.keys(), row):
            if value == None:
                submitdict[header] = headers[header]
            else: submitdict[header] = clean_basic_text(value)
        user = User(username=str(submitdict['username']), passkey=(generate_password_hash(submitdict['password'])),)

        db.session.add(user)
    db.session.commit()


def item_table_to_file(filepath):

    #set up csv for writing
    csvfile = open(filepath, 'w', newline='')
    csvwriter = writer(csvfile)
    #write headings
    csvwriter.writerow(['SKU', 'Location', 'Location Index', 'Backstock', 'Vendor', 'Description', 'QB Count', 'Count 1', 'Count 2',
        'Count 3', 'Count 4', 'Final Count'])

    #grab database items
    items = Item.query.all()
    for item in items:#write all the output data to the csv
        csvwriter.writerow([item.sku, item.location, item.location_index, item.backstock, item.vendor, item.description, item.qb_count, item.count_1,
            item.count_2, item.count_3, item.count_4, item.final_count])

    csvfile.close()


def clear_all_tables(): #clears all tables except for admin user
    try:
        num_rows_deleted = db.session.query(User).filter(User.username != SECURE_USER).delete()
        db.session.commit()
    except:
        db.session.rollback()
    try:
        num_rows_deleted = db.session.query(Item).delete()
        db.session.commit()
    except:
        db.session.rollback()
    try:
        num_rows_deleted = db.session.query(Assignments).delete()
        db.session.commit()
    except:
        db.session.rollback()
    try:
        num_rows_deleted = db.session.query(Locations).delete()
        db.session.commit()
    except:
        db.session.rollback()

def clear_counts():
    items = Item.query.filter().all()
    for item in items:
        item.count_1 = -1
        item.count_2 = -1
        item.count_3 = -1
        item.count_4 = -1
        item.final_count = -1
        db.session.commit()
    try:
        num_rows_deleted = db.session.query(Assignments).delete()
        db.session.commit()
    except:
        db.session.rollback()


def clean_basic_text(text):
    text = str(text)
    clean_text = text
    if ';' in text:
        clean_text = ''
        for letter in text:
            if letter != ';':
                clean_text += letter
    if 'delete' in text.lower():
        clean_text = ''
    if 'drop' in text.lower():
        clean_text = ''
    return clean_text


def clean_sku(sku):
    sku = str(sku)
    if ' ' in sku:
        sku = sku.split(' ')[0]
    return sku

###End defining utility functions###


###Begin defining pages and page behavior###
@inventory.route('/count/', methods=['GET', 'POST'])
@login_required
def index():
    if session['skip_setup'] and request.method == 'GET':#catches back from confirm
        session['skip_setup'] = False
        item = Item.query.filter_by(sku=session['sku']).first()
        session['sku'] = item.sku
        if (item.backstock != 'NULL') and (item.backstock != ''):
            backstock = 'The selected item has backstock at location ' + item.backstock + '. Please make sure backstock is included in the count before continuing.'
        else: backstock = ''
        return render_loggedin_template('count_page.html', location=item.location, sku=session['sku'], description=item.description, vendor=item.vendor, backstock=backstock)

    if request.method == 'GET':
        if 'assignment_id' not in session:
            session['assignment_id'] = -1
            session['assignment'] = -1
        if session['assignment'] == -1:
            #choose an untaken assignment and post username to field
            assignment = Assignments.query.filter_by(username=current_user.username, complete=False).first()
            if assignment == None:
                if not assign_check():#False if no assignments available
                    return render_loggedin_template('main_page.html')
                else:
                    assignment = Assignments.query.filter_by(username=None, complete=False).first()
                    if assignment == None:
                        assignment = Assignments.query.filter_by(username='NULL', complete=False).first()
                        if assignment == None:
                            return render_loggedin_template('main_page.html')
            session['assignment_id'] = assignment.id
            session['assignment'] = assignment.assignment_type
        else: assignment = Assignments.query.filter_by(id=session['assignment_id']).first()

        if assignment.username != current_user.username:
            #choose an untaken assignment and post username to field
            assignment = Assignments.query.filter_by(username=current_user.username, complete=False).first()
            if assignment == None:
                if not assign_check():#False if no assignments available
                    return render_loggedin_template('main_page.html')
                assignment = Assignments.query.filter_by(username=None, complete=False).first()
                if assignment == None:
                    assignment = Assignments.query.filter_by(username='NULL', complete=False).first()
            session['assignment'] = assignment.assignment_type
            session['assignment_id'] = assignment.id
        if session['assignment'] == 1:
            item = Item.query.filter_by(location=assignment.location, count_1=-1, final_count=-1).order_by(Item.location_index).first()
            next_level_check = Item.query.filter_by(location=assignment.location, count_2=-1, final_count=-1).order_by(Item.location_index).first()
        elif session['assignment'] == 2:
            item = Item.query.filter_by(location=assignment.location, count_2=-1, final_count=-1).order_by(Item.location_index).first()
            next_level_check = Item.query.filter_by(location=assignment.location, count_3=-1, final_count=-1).order_by(Item.location_index).first()
        elif session['assignment'] == 3:
            item = Item.query.filter_by(location=assignment.location, count_3=-1, final_count=-1).order_by(Item.location_index).first()
            next_level_check = Item.query.filter_by(location=assignment.location, count_1=-1, final_count=-1).order_by(Item.location_index).first()
        elif session['assignment'] == 4:
            item = Item.query.filter_by(location=assignment.location, count_4=-1, final_count=-1).order_by(Item.location_index).first()
            next_level_check = None #no way to implement more counts even if invalid
        else: item = None

        if item == None:

            assignment.complete = True
            db.session.commit()

            #create new assignment for next level of count
            #check that there are items that need to be re-counted
            if session['assignment'] == 1:
                next_level_check = Item.query.filter_by(location=assignment.location, count_2=-1, final_count=-1).order_by(Item.location_index).first()
            elif session['assignment'] == 2:
                next_level_check = Item.query.filter_by(location=assignment.location, count_3=-1, final_count=-1).order_by(Item.location_index).first()
            elif session['assignment'] == 3:
                next_level_check = Item.query.filter_by(location=assignment.location, count_4=-1, final_count=-1).order_by(Item.location_index).first()
            elif session['assignment'] == 4:
                next_level_check = None #no way to implement more counts even if invalid
            else: next_level_check = None

            if next_level_check != None:
                new_assignment = Assignments(location=assignment.location, username=None, assignment_type=(assignment.assignment_type + 1), complete=False)
                db.session.add(new_assignment)
                db.session.commit()

            session['assignment'] = -1
            return redirect(url_for('inventory.complete'))

        session['sku'] = item.sku
        if (item.backstock != 'NULL') and (item.backstock != ''):
            backstock = 'The selected item has backstock at location ' + item.backstock + '. Please make sure backstock is included in the count before continuing.'
        else: backstock = ''
        return render_loggedin_template('count_page.html', location=item.location, sku=session['sku'], description=item.description, vendor=item.vendor, backstock=backstock)

    action = request.form['submit_control']

    if action == 'Enter count':
        count = request.form["Count"]
        if count == '':
            flash('Please enter a value. Use 0 if there are none of that item.')
            return redirect(url_for('inventory.index'))
        session['count'] = int(count)
        if session['count'] < 0: session['count'] = 0 #cleans negatives into zeroes
        return redirect(url_for('inventory.confirm'))
    elif action == 'Wrong SKU':
        return redirect(url_for('inventory.redefine_sku'))
    else: return redirect(url_for('inventory.index'))


def assign_check():
    assignment = Assignments.query.filter_by(username=None).first()
    if assignment == None:
        assignment = Assignments.query.filter_by(username='NULL').first()
        if assignment == None:
            return False
    else:
        assignment.username = current_user.username
        db.session.commit()
        session['assignment'] = assignment.assignment_type
        session['assignment_id'] = assignment.id
        return True


@inventory.route('/count2/', methods=['GET', 'POST'])
@login_required
def confirm():
    item = Item.query.filter_by(sku=session['sku']).first()
    if request.method == 'GET':
        if (item.backstock != 'NULL') and (item.backstock != ''):
            backstock = 'The selected item has backstock at location ' + item.backstock + '. Please make sure backstock is included in the count before continuing.'
        else: backstock = ''
        return render_loggedin_template('confirm_page.html', location=item.location, sku=session['sku'], description=item.description, count=session['count'], backstock=backstock, vendor=item.vendor)

    #check to go back or post
    action = request.form['submit_control']
    if action == 'Confirm':
        if not current_user.is_authenticated:#keeps logged out users from posting to database
            return redirect(url_for('inventory.index'))
        try:
            item = Item.query.filter_by(sku=session['sku']).first()

            if check_if_done(item):#must be done first
                item.final_count = session['count']

            if item.count_1 == -1:
                item.count_1 = session["count"]
            elif item.count_2 == -1:
                item.count_2 = session["count"]
            elif item.count_3 == -1:
                item.count_3 = session["count"]
            elif item.count_4 == -1:
                item.count_4 = session["count"]
            else:
                flash('Sorry, the count for ' + str(session['sku']) + ' could not be submitted because this item has too many counts./nPlease contact the administrator.')
        except:
            flash('An error occurred when submitting your count. /nPlease contact the administrator.')
        db.session.commit()
        return redirect(url_for('inventory.index'))
    #go back case
    session['skip_setup'] = True
    return redirect(url_for('inventory.index'))

def check_if_done(item):
    count_list = [item.qb_count, item.count_1, item.count_2, item.count_3, item.count_4]
    if session['count'] in count_list:
        return True
    return False


@inventory.route("/sku/", methods=['GET', 'POST'])
@login_required
def redefine_sku():
    if request.method == 'GET':
        assignment = Assignments.query.filter_by(id=session['assignment_id']).first()
        return render_loggedin_template('sku_page.html', location=assignment.location)
    session['sku'] = request.form["SKU"]
    return redirect(url_for('inventory.confirm_sku'))


@inventory.route("/sku2/", methods=['GET', 'POST'])
@login_required
def confirm_sku():
    item = Item.query.filter_by(sku=session['sku']).first()
    assignment = Assignments.query.filter_by(id=session['assignment_id']).first()

    if request.method == 'GET':
        if item == None:
            message = "This item SKU shouldn't exist. Please double-check before proceeding."
            vendor = ''
            description = ''
        else:
            if (item.count_1 != 0) and (item.count_1 != -1):
                message = 'This item was already counted in location ' + item.location + '. Please double-check before proceeding.'
            else: message = ''
            vendor = item.vendor
            description = item.description
        return render_loggedin_template('sku_confirm_page.html', location=assignment.location, vendor=vendor, description=description, message=message, sku=session['sku'] )

    #when a POST request is sent
    action = request.form['submit_control']

    if action == 'Confirm':
        if item == None:
            item = Item(sku=session['sku'], qb_count=-10,
            description='', vendor='', location=assignment.location,
            location_index=0, backstock='NULL',
            count_1=-1, count_2=-1, count_3=-1, count_4=-1, final_count=-1)
            db.session.add(item)
        else:
            if assignment.location == item.location:
                if item.count_2 == -1:
                    item.count_1 = -1
                if item.count_3 == -1:
                    item.count_2 = -1
                if item.count_4 == -1:
                    item.count_3 = -1
            else:
                item.location = assignment.location
                item.location_index = 0
                item.count_1 = -1
                item.count_2 = -1
                item.count_3 = -1
                item.count_4 = -1
        db.session.commit()
        return redirect(url_for('inventory.index'))
    elif action == 'Back': return redirect(url_for('inventory.redefine_sku'))
    else: return redirect(url_for('inventory.confirm_sku'))


@inventory.route("/complete/", methods=['GET', 'POST'])
@login_required
def complete():
    if request.method == 'GET':
        return render_loggedin_template('assignment_page.html')
    return redirect(url_for('inventory.index'))


@inventory.route("/", methods=['GET', 'POST'])
def login():
    #user = User(username='Natsume', passkey=(generate_password_hash('Lingjian')),)
    #db.session.add(user)
    #db.session.commit()
    if request.method == "GET":
        return render_template("login_page.html", error=False)

    #try:
    user = load_user(request.form["username"])
    #except StatementError:
        #db.session.rollback()
    if user is None:
        return render_template("login_page.html", error=True)
    if not user.validate_user(request.form["password"]):
        return render_template("login_page.html", error=True)
    login_user(user)
    if current_user.username == SECURE_USER:

        session['message'] = ''
        session['warning'] = False #used for confirm on Clear Data function
        session['warning sample'] = False #used for confirm on Load Sample function
        return redirect(url_for('inventory.controls'))
    session['assignment'] = -1
    session['skip_setup'] = False

    return redirect(url_for('inventory.index'))


@inventory.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('inventory.login'))


@inventory.route("/control-panel/add-items/", methods=['GET', 'POST'])
@login_required
def add_items_by_location_location():
    if current_user.username != SECURE_USER:
        return redirect(url_for('inventory.index'))
    if request.method == 'GET':
        ids = []
        locations = []
        active_locations = Locations.query.filter().all()
        for location in active_locations:
            ids.append(location.id)
            locations.append(location.location)

        return render_loggedin_template('locations_page.html', locations=zip(ids, locations))

    else:
        action = request.form['submit_control']
        if action == 'Back to Control Panel':
            return redirect(url_for('inventory.controls'))
        location = request.form['Location']
        if action == 'Delete Location':
            location = Locations.query.filter_by(location=location).first()

            if location:
                db.session.query(Locations).filter(Locations.id == location.id).delete()
                db.session.commit()
            else:
                flash('Could not delete the location specified. Did not find in database.')
                return redirect(url_for('inventory.add_items_by_location_location'))

        elif action == 'Add Items to Location':
            session['sizes'] = {}
            session['sizes']['1'] = ['XXS', False]
            session['sizes']['2'] = ['XS', False]
            session['sizes']['3'] = ['S', False]
            session['sizes']['4'] = ['M', False]
            session['sizes']['5'] = ['L', False]
            session['sizes']['6'] = ['X', False]
            session['sizes']['7'] = ['XX', False]
            session['sizes']['8'] = ['XXX', False]

            session['last item'] = "None"
            session['cur item index'] = 1 #starts at 1, not zero, because it allows better behavior when doing "Wrong SKU" in the main count
            if Item.query.filter_by(location=location).first():
                items = Item.query.filter_by(location=location).all()
                for item in items:
                    if session['cur item index'] <= item.location_index:
                        session['cur item index'] = item.location_index + 1
                        session['last item entered'] = item.sku
            session['location'] = location
            return redirect(url_for('inventory.add_items_by_location_item'))

    return redirect(url_for('inventory.add_items_by_location_location'))


@inventory.route("/control-panel/add-items/item/", methods=['GET', 'POST'])
@login_required
def add_items_by_location_item():
    if current_user.username != SECURE_USER:
        return redirect(url_for('inventory.index'))
    if request.method == 'GET':
        sizes = []
        check_bools = []
        for key in session['sizes']:
            sizes.append(session['sizes'][key][0])
            check_bools.append(session['sizes'][key][1])
        return render_loggedin_template('location_item_page.html', location=session['location'], last_item_entered=session['last item'], current_item_index=str(session['cur item index']), sizes=zip(sizes, check_bools), backstock=session.get('backstock_on',False))

    else:
        action = request.form['submit_control']
        if action == 'Location Complete':
            session.pop('backstock_on', False)
            return redirect(url_for('inventory.add_items_by_location_location'))

        elif action == 'Enter SKU':
            sizes = request.form.getlist('size')
            sku_root = clean_basic_text(request.form['SKU'])
            backstock = bool(request.form.get('backstock'))
            if sizes:
                for values in session['sizes']:
                    size = session['sizes'][values][0]
                    if size in sizes:
                        session['sizes'][values][1] = True
                    else:
                        session['sizes'][values][1] = False

                    if session['sizes'][values][1]:
                        if sku_root[-1] == '-':
                            sku = sku_root + size
                        else: sku = sku_root + '-' + size
                        item = Item.query.filter_by(sku=sku).first()
                        if not backstock:
                            if item == None:
                                item = Item(sku=sku, qb_count=-10,
                                description='', vendor='', location=session['location'],
                                location_index=session['cur item index'], backstock='NULL',
                                count_1=-1, count_2=-1, count_3=-1, count_4=-1, final_count=-1)
                                db.session.add(item)
                            else:
                                item.location = session['location']
                                item.location_index = session['cur item index']
                            if not Locations.query.filter_by(location=session['location']).first():
                                location = Locations(location=session['location'])
                                db.session.add(location)
                            session['cur item index'] += 1
                        else:
                            if item == None:
                                item = Item(sku=sku, qb_count=-10,
                                description='', vendor='', location='NULL',
                                location_index=0, backstock=session['location'],
                                count_1=-1, count_2=-1, count_3=-1, count_4=-1, final_count=-1)
                                db.session.add(item)
                            else:
                                item.backstock = session['location']

            elif not sizes:
                sku = sku_root
                for key in session['sizes']:
                    session['sizes'][key][1] = False
                item = Item.query.filter_by(sku=sku).first()
                if not backstock:
                    if item == None:
                        item = Item(sku=sku, qb_count=-10,
                        description='', vendor='', location=session['location'],
                        location_index=session['cur item index'], backstock='NULL',
                        count_1=-1, count_2=-1, count_3=-1, count_4=-1, final_count=-1)
                        db.session.add(item)
                    else:
                        item.location = session['location']
                        item.location_index = session['cur item index']
                    session['cur item index'] += 1
                    if not Locations.query.filter_by(location=session['location']).first():
                        location = Locations(location=session['location'])
                        db.session.add(location)
                else:
                    if item == None:
                        item = Item(sku=sku, qb_count=-10,
                        description='', vendor='', location='NULL',
                        location_index=0, backstock=session['location'],
                        count_1=-1, count_2=-1, count_3=-1, count_4=-1, final_count=-1)
                        db.session.add(item)
                    else:
                        item.backstock = session['location']
            session['backstock_on'] = backstock
            db.session.commit()
        session['last item'] = sku
    return redirect(url_for('inventory.add_items_by_location_item'))



@inventory.route("/control-panel/", methods=['GET', 'POST'])
@login_required
def controls():
    if current_user.username != SECURE_USER:
        return redirect(url_for('inventory.index'))
    if request.method == 'GET':
        users = []
        locations = []
        counts = []
        active_assignments = Assignments.query.filter(Assignments.username != None, Assignments.complete == False).all()
        for assignment in active_assignments:
            users.append(assignment.username)
            locations.append(assignment.location)
            counts.append(assignment.assignment_type)

        unused_assignments = Assignments.query.filter(Assignments.username == None, Assignments.complete == False).all()
        the_ids = []
        unused_locations = []
        for assignment in unused_assignments:
            the_ids.append(assignment.id)
            unused_locations.append(assignment.location)
        return render_loggedin_template("control_page.html", user_assignments=zip(users, locations, counts), open_assignments=zip(the_ids, unused_locations), message=session['message'])

    action = request.form['submit_control']
    if action in ('Clear All Data', 'Clear Only Count Data'):
        if session['warning'] == False:
            flash('Are you sure you want to clear data? This action connot be reversed.')
            session['warning'] = True
            return redirect(url_for('inventory.controls'))
        else:
            session['warning'] = False
            if action == 'Clear All Data':
                clear_all_tables()
                flash('All data has been cleared from the tables.')
            elif action == 'Clear Only Count Data':
                clear_counts()
                flash('Only count data has been cleared from the tables.')
            return redirect(url_for('inventory.controls'))

    elif action == 'Add Users':
        return redirect(url_for('inventory.user_management'))

    elif action == 'Add Items by Location':
        return redirect(url_for('inventory.add_items_by_location_location'))

    elif action == 'Start':
        if current_user.username != SECURE_USER:
            return redirect(url_for('inventory.index'))#kicks out unauthorized users

        #check that item database has data
        item = Item.query.first()
        if item == None:
            flash('The database is empty./nPlease upload the items first.')
            return redirect(url_for('inventory.controls'))

        #check that assignments table is empty, empty if not
        assignments = Assignments.query.all()
        if assignments != None:
            Assignments.query.delete()
            db.session.commit()

        #generate initial assignments by location
        locations = Locations.query.order_by(Locations.id).all()
        if locations:
            for location in locations:
                new_assignment = Assignments(location=location.location, username=None, assignment_type=1, complete=False)
                db.session.add(new_assignment)
                db.session.commit()
        else: flash('The locations table is empty.')
        return redirect(url_for('inventory.controls'))

    elif action == 'Items without Locations':
        session['search sku'] = None
        return redirect(url_for('inventory.item_management'))

    elif action == 'Upload File':
        return redirect(url_for('inventory.uploader'))

    elif action == 'Load Sample Data':
        if session['warning sample'] == False:
            flash('This will clear existing data and cannot be reversed. Press the button again to continue.')
            session['warning sample'] = True
            return redirect(url_for('inventory.controls'))
        else:
            session['warning sample'] = False
            try:
                clear_all_tables()
                filepath = Path.cwd()
                os.chdir(filepath)
                file_to_item_database('SampleDataItems.csv')
                file_to_user_database('SampleDataUsers.csv')
                flash('The data has been cleared and replaced with test data.')
            except Exception as error:
                flash('An unknown error has occurred. ' + str(error))
        return redirect(url_for('inventory.controls'))

    elif action == 'Download File':
        if current_user.username != SECURE_USER:
            return redirect(url_for('inventory.index'))#kicks out unauthorized users

        filename = 'Download.csv'
        filepath = Path.cwd()
        filepath2 = os.path.join(filepath, 'mysite')
        filepath2 = os.path.join(filepath2, 'assets')

        os.chdir(filepath2)

        item_table_to_file(filename)
        os.chdir(filepath)

        #return send_from_directory(directory=Path(app.config['UPLOAD_FOLDER']), filename=filename)
        return send_from_directory(directory=filepath2, filename=filename, as_attachment=True, attachment_filename='CountData.csv')
        return redirect(url_for('inventory.controls'))

    elif action == 'CurrentTest':
        flash('No current test loaded.')
        return redirect(url_for('inventory.tester'))

    elif action == "Reassign":
        if current_user.username != SECURE_USER:
            return redirect(url_for('inventory.index'))#kicks out unauthorized users
        assign_user = request.form["Username"]
        assign_id = request.form["ID"]

        old_assignment = Assignments.query.filter(Assignments.username == assign_user, Assignments.complete == False).all()
        if len(old_assignment) > 0:
            for assignment in old_assignment:
                assignment.username = None
                db.session.commit()
        new_assignment = Assignments.query.filter_by(id=assign_id).first()
        if new_assignment:
            new_assignment.username = assign_user
            db.session.commit()
        return redirect(url_for('inventory.controls'))
    return redirect(url_for('inventory.controls'))

@inventory.route("/control-panel/users/", methods=['GET', 'POST'])
@login_required
def user_management():
    if current_user.username != SECURE_USER:
        return redirect(url_for('inventory.index'))#kicks out unauthorized users
    if request.method == 'GET':
        users = []
        active_users = User.query.filter().all()
        for user in active_users:
            users.append(user.username)

        return render_loggedin_template("control_users_page.html", users=users, message=session['message'])

    action = request.form['submit_control']
    if action == 'Back to Control Panel':
            return redirect(url_for('inventory.controls'))
    elif action == 'Add User':
        if current_user.username != SECURE_USER:
            return redirect(url_for('inventory.index'))#kicks out unauthorized users
        assign_user = request.form["Username"]
        assign_password = request.form["Password"]
        if assign_user == None or assign_password == None:
            flash('Creating a user requires both a username and password to be entered.')
            return redirect(url_for('inventory.user_management'))
        #check database for username, change password instead
        user = User.query.filter_by(username=assign_user).first()
        if user != None:
            assign_key = generate_password_hash(assign_password)
            user.passkey = assign_key
            db.session.commit()
        else:
            try:
                #add a user
                assign_key = generate_password_hash(assign_password)
                new_user = User(username=assign_user, passkey=assign_key)
                db.session.add(new_user)
                db.session.commit()
            except:
                flash('Could not add user. Please try again.')
                return redirect(url_for('inventory.user_management'))

    elif action == 'Delete User':
        if current_user.username != SECURE_USER:
            return redirect(url_for('inventory.index'))#kicks out unauthorized users
        delete_user = request.form["Username"]
        if delete_user == 'Natsume':
            flash('The Admin User cannot be deleted.')
            return redirect(url_for('inventory.user_management'))
        try:
            db.session.query(User).filter(User.username == delete_user).delete()
            #User.query.filter_by(username=delete_user).first().delete()
            db.session.commit()
        except Exception as error:
            flash(str(error))
            flash('Could not delete user. Please try again.')
            return redirect(url_for('inventory.user_management'))

    return redirect(url_for('inventory.user_management'))


@inventory.route("/control-panel/items/", methods=['GET', 'POST'])
@login_required
def item_management():
    if current_user.username != SECURE_USER:
        return redirect(url_for('inventory.index'))#kicks out unauthorized users
    if request.method == 'GET':
        nl_ids = []
        nl_skus = []
        nl_locations = []
        nl_descs = []
        nl_items = Item.query.filter(Item.location=='NULL').all()
        for item in nl_items:
            nl_ids.append(item.id)
            nl_skus.append(item.sku)
            nl_locations.append(item.location)
            nl_descs.append(item.description)

        nl_items = Item.query.filter(Item.location==None).all()
        for item in nl_items:
            nl_ids.append(item.id)
            nl_skus.append(item.sku)
            nl_locations.append(item.location)
            nl_descs.append(item.description)

        nl_items = Item.query.filter(Item.location=='').all()
        for item in nl_items:
            nl_ids.append(item.id)
            nl_skus.append(item.sku)
            nl_locations.append(item.location)
            nl_descs.append(item.description)

        if not session['search sku']:
            return render_loggedin_template("control_items_page.html", no_loc_items=zip(nl_ids, nl_skus, nl_locations, nl_descs), search_items=zip(['',], ['',], ['',], ['',]), message='')
        else:
            s_ids = []
            s_skus = []
            s_locations = []
            s_descs = []
            search = "%{}%".format(session['search sku'])
            search_items = Item.query.filter(Item.sku.like(search)).all()
            for item in search_items:
                s_ids.append(item.id)
                s_skus.append(item.sku)
                s_locations.append(item.location)
                s_descs.append(item.description)
            return render_loggedin_template("control_items_page.html", no_loc_items=zip(nl_ids, nl_skus, nl_locations, nl_descs), search_items=zip(s_ids, s_skus, s_locations, s_descs), message='')


    action = request.form['submit_control']
    if action == 'Search':
        session['search sku'] = clean_basic_text(request.form["Search SKU"])

    if action == 'Merge':
        item_1 = request.form['ID 1']
        item_1_keep = Item.query.filter(Item.id==item_1).first()
        item_2 = request.form['ID 2']
        item_2_merge = Item.query.filter(Item.id==item_2).first()
        if item_1_keep and item_2_merge:
            if item_1_keep.qb_count == -10:
                item_1_keep.qb_count = item_2_merge.qb_count
            if item_1_keep.description == '':
                item_1_keep.description = item_2_merge.description
            if item_1_keep.vendor == '':
                item_1_keep.vendor = item_2_merge.vendor
            if item_1_keep.location in ('NULL', None):
                item_1_keep.location = item_2_merge.location
            if item_1_keep.location_index == 0:
                item_1_keep.location_index = item_2_merge.location_index
            if item_1_keep.backstock in ('NULL', None):
                item_1_keep.backstock = item_2_merge.backstock
            if item_1_keep.count_1 == -1:
                item_1_keep.count_1 = item_2_merge.count_1
            if item_1_keep.count_2 == -1:
                item_1_keep.count_2 = item_2_merge.count_2
            if item_1_keep.count_3 == -1:
                item_1_keep.count_3 = item_2_merge.count_3
            if item_1_keep.count_4 == -1:
                item_1_keep.count_4 = item_2_merge.count_4
            if item_1_keep.final_count == -1:
                item_1_keep.final_count = item_2_merge.final_count
            db.session.query(Item).filter(Item.id == item_2).delete()
            db.session.commit()
        elif item_2_merge:
            db.session.query(Item).filter(Item.id == item_2).delete()
            db.session.commit()
        else:
            flash('The Item 2 you selected doesn\'t exist in the database. If you meant to delete an item, put it in Item 2 and leave item 1 blank.')
    elif action == 'Back to Control Panel':
        return redirect(url_for('inventory.controls'))

    return redirect(url_for('inventory.item_management'))



@inventory.route('/control-panel/upload/', methods=['GET','POST'])
@login_required
def uploader():
    if current_user.username != SECURE_USER:
        return redirect(url_for('inventory.index'))#kicks out unauthorized users

    if request.method == 'POST':
        action = request.form['submit_control']
        if action == 'Back to Control Panel':
            return redirect(url_for('inventory.controls'))
        # check if the post request has the file part
        elif 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        elif file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = Path.cwd()
            #if filepath != '/home/jtefft/mysite/assets/':
                #filepath2 = os.path.join(filepath, 'mysite')
                #filepath2 = os.path.join(filepath2, 'assets')
            #else: filepath2 = filepath
            filepath2 = filepath
            os.chdir(filepath2)
            file.save(os.path.join(filepath2, filename))
            file_to_item_database(filename)

            os.chdir(filepath)
            return redirect(url_for('inventory.controls'))
    #on a GET request, loads the following html without using a template
    return '''
    <!doctype html>
    <title>Upload Data File</title>
    <h1>Upload Data File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input name='submit_control' type=submit value=Upload>
    </form>
    <div class="row" style="font-size:150%">
        <form action="." method="POST">
            <input type="submit" name='submit_control' class="btn btn-success" value="Back to Control Panel">
        </form>
    </div>
    '''
@inventory.route('/tester/', methods=['GET','POST'])
@login_required
def tester():
    if request.method == 'GET':
        return render_loggedin_template("test_page.html", message=session['message'])
    seq = str(request.form.get('check'))
    seq += str(request.form.get('size'))
    flash(seq)
    return redirect(url_for('inventory.tester'))

###End defining pages and page behavior###
