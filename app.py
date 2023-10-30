from unicodedata import name
from flask import Response, jsonify  # Import jsonify
from flask import Flask, render_template , url_for,session,redirect,request
from flask_pymongo import PyMongo
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import cv2
from bson import ObjectId

import face_recognition
import os
from simple_detect import SimpleDetect


app = Flask(__name__)
app.config['SECRET_KEY'] = 'EL Handaoui Ahemri'

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client.stage






global adminStatus,employeStatus,names,nameemploye,servi
adminStatus = False
employeStatus = False
names=[]
nameemploye =''
servi= ''
#--------- Login and redirect to page -------------- 
@app.route('/', methods=['POST', 'GET'])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for('admindashboard'))

    if request.method == "POST":
        global adminStatus, employeStatus,mailemploye
        adminStatus = False 
        employeStatus = False
        email = request.form.get("email")
        password = request.form.get("password")

        dbUsers = client.get_database('stage')
        user = dbUsers.user.find({'Email': email, 'Password': password})
        for docuser in user:
            if docuser is not None:
                if docuser['Type'] == "admin":
                    adminStatus = True
                    return redirect(url_for('admindashboard'))
                if docuser['Type'] == "employe":
                    employeStatus = True
                    mailemploye = email
                    checkseance = getSeance()
                    if checkseance == 'no sceance':
                        return render_template('no_seance.html')
                    else:
                        return redirect(url_for('home'))
        else:
            message = 'Email or Password wrong'
            return render_template('login.html', message=message)

    return render_template('login.html', message=message)
#-------Admin Dashboard --------
@app.route('/admin')
def admindashboard():
    if adminStatus == True:
        serviceList = list()
        employeList = list()
        timetabledb = client.get_database('timetable')
        table = timetabledb.timetable.find({},{"_id":0,"service":1})
        employeListdb = client.get_database('stage')
        employe = employeListdb.employe.find({})
        for t in table:
            serviceList.append(t['service'])
        for p in employe:
            employeList.append(p['Name_employe'])
        return render_template('admin.html',services=serviceList,employes=employeList)
    else:
        return redirect(url_for('login'))
########## home#################
@app.route('/home')
def home():
    if employeStatus == True:
        global servi, mailemploye, nameemploye
        dataList = []
        employeListdb = client.get_database('stage')
        data = employeListdb.user.find({'Email': mailemploye}, {'_id': 0})
        for doc in data:
            for key in doc:
                dataList.append(doc[key])
        nameemploye = dataList[0]
        servi = str(dataList[1])  # Convert to string

        # Pass the 'employe' variable to the template
        employe = {
            'Name_employe': nameemploye,
            'Email': dataList[2],
            'service': dataList[3:]
        }

        day = datetime.today().strftime('%A')
        time = getSeance()
        timdb = client.get_database('timetable')
        tableresults = timdb.timetable.find({'service': {'$in': [servi]}}, {'service': 0, '_id': 0})
        timeTablle = None
        for t in tableresults:
            timeTablle = dict(t)
        if timeTablle and day in timeTablle:
            if time in timeTablle[day]:
                if timeTablle[day][time][1] != nameemploye:
                    return render_template('no_seance.html')

        # Pass the 'employe' variable to the template
        return render_template("home.html", employe=employe, filierName=servi, len=len(servi))
    else:
        return redirect(url_for('admindashboard'))

########### search PAGE ##################
@app.route('/employe', methods=['GET', 'POST'])
def employe():
    if request.method == 'POST':
        employe = request.form.get('searching_employe')
        employeListdb = client.get_database('stage')
        data = employeListdb.employe.find_one({'Name_employe': employe}, {'_id': 0})
        if data is None:
            return render_template("admin.html")
        
        return render_template("employe.html", employe=data, len=len)
    
   
def getSeance():
    current = datetime.now()
    hour = int(current.hour)
    if hour >= 8 and hour <= 14:
        return '08:30-14'
    if hour >= 14 and hour <=23:
        return '14:30-23'
    else:
        return 'no sceance'
   # Ajouter un nouveau professeur
@app.route('/admin/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        name_employe = request.form['Name_employe']
        email = request.form['Email']
        service = request.form['service'].split(",")
        password = request.form['Password']
        
        # Enregistrer le nouvel employé dans la base de données
        employe = client.stage.employe
        _id = employe.insert_one({
            "Name_employe": name_employe,
            "Email": email,
            "service": service,
            "Password": password,
            "Type": "employe"
        }).inserted_id
        
        # Rediriger vers la page de gestion des professeurs
        return redirect(url_for('admindashboard'))
    else:
        # Afficher le formulaire d'ajout d'employé
        return render_template('add.html')
#################Supprimer un employé########################
@app.route('/employe/delete/<employe_name>', methods=['POST'])
def delete_employe(employe_name):
    # Logique de suppression de l'employé à partir de son nom
    employeListdb = db.employe
    employeListdb.delete_one({'Name_employe': employe_name})
    
    return redirect(url_for('admindashboard'))
################ Modifier un employé###############
@app.route('/employe/<employe_name>', methods=['POST'])
def modify_employe(employe_name):
    # Récupérer les données du formulaire
    new_name = request.form.get('Name_employe')
    new_email = request.form.get('email_')
    new_service = request.form.get('service')
    # Modifier les informations de l'employé dans la base de données
    employe_collection = db['employe']
    employe_collection.update_one({'Name_employe': employe_name}, {'$set': {'Name_employe': new_name, 'Email': new_email, 'service': new_service}})
    print("employe_name:", employe_name)
    return redirect(url_for('admindashboard'))



@app.route('/employe_abse', methods = ['GET','POST'])
def Students():
    if request.method == 'POST':
        name_list=list()
        
        templist=[]
        name_list=[]
        services=request.form.get('searching_student')
        dbemploye = client.get_database('stage')
        services= dbemploye.employe.find({'service':services},{'_id':0,'service':0})
        for doc in services:
            for key in doc:
                 templist=doc[key]
      
        return render_template("students.html",services_n=services,list_employe=name_list)
    else:
        return redirect(url_for('admindashboard'))

#------------ EDIT STUDENTS LIST -----------------------------
@app.route('/students/Edit/<filiere_n>/<s>',methods=['POST'])
def editStudent(filiere_n,s):
    if request.method == 'POST':
        newName = request.form.get('fullname')
        dbStudent = client.students
        dbStudent.student.update_one({'Filiere':filiere_n,'Students.Name':str(s)},{"$set":{'Students.$.Name':newName}})
        return redirect(url_for('Students'))
################### time table ######################
# Liste des services
services = ['informatique', 'technique', 'marketing', 'commercial']
@app.route('/')
def index():
    return render_template('admin.html', service=services)

################ timetable ###################
@app.route('/timetable', methods=['GET', 'POST'])
def timetable():
    if request.method == 'POST':
        collection = db.timetable
        data = list(collection.find())
        time_table_data = {
            'lundi': {
                '08:30-14': data[0]['Lundi']['08:30'][0],
                '14:30-02:00': data[0]['Lundi']['14:30'][0]
            },
            'mardi': {
                '08:30-14': data[0]['Mardi']['08:30'][0],
                '14:30-02:00': data[0]['Mardi']['14:30'][0]
            },
            'mercredi': {
                '08:30-14': data[0]['Mercredi']['08:30'][0],
                '14:30-02:00': data[0]['Mercredi']['14:30'][0]
            },
            'jeudi': {
                '08:30-14': data[0]['Jeudi']['08:30'][0],
                '14:30-02:00': data[0]['Jeudi']['14:30'][0]
            },
            'vendredi': {
                '08:30-14': data[0]['Vendredi']['08:30'][0],
                '14:30-02:00': data[0]['Vendredi']['14:30'][0]
            }
        }
        servi = request.form.get('searching_timetable')
        dbTable = client.get_database('timetable')
        tableresults = dbTable.timetable.find({'service': servi})
        for table in tableresults:
            timetable = dict(table)
        return render_template("timetable.html", service=servi, time_table=time_table_data)
    else:
        return redirect(url_for('admindashboard'))

# -------- Edit time table -----------
@app.route('/edit_time/<service>', methods=['GET', 'POST'])
def edit_time(service):
    if request.method == 'POST':
        # Retrieve the form data
        day = request.form.get('day')
        first_seance = request.form.get('Firstseance')
        second_seance = request.form.get('Secondseance')

        # Update the data in the database
        collection = db.timetable
        collection.update_many({'service': service}, {'$set': {day: {'08:30': [first_seance], '14:30': [second_seance]}}})

        # Redirect to the timetable page with the updated service
        return redirect(url_for('admindashboard'))

    # Return any necessary response if the request method is not POST
    return ''
    # Return any necessary response if the request method is not POST
   
#################  ####################

@app.route('/absence')
def absence():
    if employeStatus == True:
        if request.method == 'GET':
            serviList=[]
            servidb = client.get_database('stage')
            table = servidb.timetable.find({},{"_id":0,"service":1})
            for t in table:
                serviList.append(t['service'])
            return render_template("absence.html",services=serviList)
    else:
        return redirect(url_for("login"))


@app.route('/absence/list/<service>', methods =['GET'] )
def listabs(service):
    abs_days = []
    names = []
    listemploye = client.get_database('stage')
    data = listemploye.listAbs.find({'service':service},{'_id':0,'service':0})
    for doc in data:
            for key in doc:
                names.append(doc[key]['Name'])
                abs_days.append(doc[key]['abs_days'])
    return render_template('liste_abs.html',service=service,employeNames = names, absencedays = abs_days,zip=zip)
# Chemin du dossier contenant les images enregistrées


@app.route('/list_abs', methods=['GET', 'POST'])
def list_abs():
    collection = db.listAbs
    data = list(collection.find())
    for c in data:
        if c['Name_employe'] != 'ASMA' : 
            collection.update_one({"Name_employe": c['Name_employe']}, {"$inc": {"abs_days": 1}})
            
    
    return render_template('liste_abs.html' , listbs = data) 
##################### caméra #########################
mongo = PyMongo(app, uri="mongodb://localhost:27017/stage")

@app.route('/employee')
def employe_page():
    # Récupérer les informations de tous les employés depuis la base de données
    employe_data = mongo.db.collection_name.find()

    return render_template('employe.html', employes=employe_data)

camera = cv2.VideoCapture(0)
def generate_cam():
    simple = SimpleDetect()
    simple.load_image('image')
    while True:
        success, frame = camera.read()
        if not success or frame is None:
            break

        location, name = simple.knowing_faces(frame)
        for cordination, name in zip(location, name):
            Y1, X2, Y2, X1 = cordination[0], cordination[1], cordination[2], cordination[3]
            cv2.putText(frame, name, (X1+30, Y1-10), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 200), 2)
            cv2.rectangle(frame, (X1, Y1), (X2, Y2), (0, 0, 200), 4)
        
        ref, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n'+frame+b'\r\n')

@app.route('/video')
def video():
    return Response(generate_cam(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/done')
def done():
    global camera, names
    camera.release()
    cv2.destroyAllWindows()
    make_attendance()

    return render_template('no_seance.html')
def make_attendance():
    global servi, names

    servi = servi[0]
    day = datetime.today().strftime('%A')
    time = getSeance()

    # Recherche de l'emploi du temps correspondant dans la base de données
    db = client.get_database('stage')
    timetable = db.timetable.find_one()

    # Recherche de l'employé correspondant au nom actuel
    employe = db.employee.find_one({'Name_employe': names})

    if employe:
        employe_name = employe['Name_employe']
        employe_service = employe['Service']

        absenceDb = client.get_database('listAbs')
        addabsence = absenceDb[employe_service]
        formatted_day = datetime.today().strftime('%Y-%m-%d')
        addabsence.insert_one({'Day': formatted_day, 'time': time, 'employe': employe_name})
        namesList = absenceDb[employe_service].find({}, {'_id': 0})

        for n in namesList:
            if n['employe'] != employe_name:
                absenceDb[employe_service].update_one({'employe': n['employe']}, {"$inc": {'abs_hours': 3}})


########## THE END ######################
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if "email" in session:
        session.pop("email", None)
        return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))
if __name__ == '__main__':
   app.run(debug = True,port=5000)
