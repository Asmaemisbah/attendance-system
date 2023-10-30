from unicodedata import name
import cv2
from flask import Flask, render_template , url_for,session,redirect,request,Response
from pymongo import MongoClient
from datetime import datetime
from simple_detect import SimpleDetect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'EL Handaoui Ahemri'

client = MongoClient(port= 27017)

global adminStatus,profStatus,names,nameprof,filier
adminStatus = False
profStatus = False
names=[]
nameprof =''
filier = ''
#--------- Login and redirect to page -------------- 
@app.route('/', methods=['POST', 'GET'])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for('admindashboard'))

    if request.method == "POST":
        global adminStatus, profStatus,mailprof
        adminStatus = False 
        profStatus = False
        email = request.form.get("email")
        password = request.form.get("password")

        dbUsers = client.get_database('admin')
        user = dbUsers.admin.find({'E-mail': email, 'Password': password})
        for docuser in user:
            if docuser is not None:
                if docuser['Type'] == "admin":
                    adminStatus = True
                    return redirect(url_for('admindashboard'))
                if docuser['Type'] == "prof":
                    profStatus = True
                    mailprof = email
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
        filierList = list()
        profList = list()
        timetabledb = client.get_database('timetable')
        table = timetabledb.timetable.find({},{"_id":0,"filiere":1})
        profListdb = client.get_database('profs')
        prof = profListdb.profs.find({})
        for t in table:
            filierList.append(t['filiere'])
        for p in prof:
            profList.append(p['Full Name'])
        return render_template('admin.html',filieres=filierList,profs=profList)
    else:
        return redirect(url_for('login'))
########## home#################
@app.route('/home')
def home():
    if profStatus == True:
        global filier,mailprof,nameprof
        dataList = []
        profListdb = client.get_database('profs')
        data = profListdb.profs.find({'E-mail':mailprof},{'_id':0})
        for doc in data:
            for key in doc:
                dataList.append(doc[key])
        nameprof=dataList[0]
        filier= dataList[1]
        day = datetime.today().strftime('%A')
        time = getSeance()
        timdb = client.get_database('timetable')
        tableresults = timdb.timetable.find({'filiere':{"$in":filier}},{'filiere':0,"_id":0})
        for t in tableresults:
            timeTablle = dict(t)
        for key in timeTablle:
                if key == day:
                    for value in timeTablle[key]:
                        if (time == value) is True:
                            if timeTablle[key][value][1] != nameprof:
                                return render_template('no_seance.html')
        return render_template("home.html",ProfName=dataList[0],filierName=filier,len=len)
    else:
        return redirect(url_for('admindashboard'))
          
########## Students Page ################

#------------- GET STUDETS LIST ----------------------
@app.route('/students', methods = ['GET','POST'])
def Students():
    if request.method == 'POST':
        name_list=list()
        templist=[]
        name_list=[]
        filiere=request.form.get('searching_student')
        dbStudents = client.get_database('students')
        students= dbStudents.student.find({'Filiere':filiere},{'_id':0,'Filiere':0})
        for doc in students:
            for key in doc:
                 templist=doc[key]
        for i in range(len(templist)):
            name_list.append(templist[i]['Name'])
        return render_template("students.html",nombre_students=len(templist),filiere_n=filiere,list_students=name_list)
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
#----------ADD a student---------------
@app.route('/students/Add/<filiere_n>',methods=['POST'])
def addstudent(filiere_n):
    if request.method == 'POST':
        fullname = request.form.get('Name')
        dbstudent =client.students
        dbstudent.student.update_one({'Filiere':filiere_n},{"$push":{'Students':{'Name':fullname}}})
        return redirect(url_for('admindashboard'))
#------------- Delete a student-------
@app.route('/students/delete/<filiere_n>/<s>', methods=['POST'])
def deletestudent(filiere_n,s):
    if request.method =='POST':
        dbstudent=client.students
        dbstudent.student.update_one({'Filiere':filiere_n},{"$pull":{"Students":{"Name":str(s)}}})
        return redirect(url_for('admindashboard'))
######### TIME TABLE PAGE ########################

#----------- GET TIME TABLE -----------------------
@app.route('/timetable', methods = ['GET','POST'])
def tiime():
    if request.method == 'POST':
        timetable = dict()
        filier = request.form.get('searching_timetable')
        dbTable = client.get_database('timetable')
        tableresults = dbTable.timetable.find({'filiere':filier})
        for table in tableresults:
            timetable = dict(table)
        return render_template("timetable.html",filiereName=filier,time_table=timetable)
    else:
        return redirect(url_for('admindashboard'))
#--------Edit time table-----------
@app.route('/save_time/<filiereName>',methods=['POST'])
def editTime(filiereName):
    Nday = request.form.get('day')
    Fseance = request.form.get('Firstseance')
    Sseance = request.form.get('Secondseance')
    dbtimetable = client.get_database('timetable')
    dbtimetable.timetable.update_one({'filiere':filiereName},{"$set":{Nday:{"08:30-12":Fseance,"14:30-18":Sseance}}})
    return redirect(url_for('admindashboard'))

########### PROFESSORS PAGE ##################
@app.route('/prof', methods = ['GET','POST'])
def prof():
    if request.method == 'POST':
        dataList = []
        prof = request.form.get('searching_prof')
        profListdb = client.get_database('profs')
        data = profListdb.profs.find({'Full Name': prof},{'_id':0})
        for doc in data:
            for key in doc:
                dataList.append(doc[key]) 
        return render_template("prof.html",prof_name=dataList[0],email=dataList[2],filieres=dataList[1],len=len)
#--------Edit Professor------------
@app.route('/prof/<prof_name>' ,methods = ['POST'])
def editprof(prof_name):
    if request.method == 'POST':
        filieres = []
        filieres = request.form.get('courses_').split(',')
        NprofName = request.form.get('FName_')
        email = request.form.get('email_')
        dbprofs = client.profs
        dbprofs.profs.update_one({'Full Name':prof_name },{"$set":{'Full Name':NprofName, "E-mail" : email ,"FiliersEnseignes" :filieres }})
        return redirect(url_for('admindashboard'))
#----------------Add prof---------------
@app.route('/admin/add',methods=['POST'])
def addprof():
    if request.method == 'POST':
         profName=request.form.get('FullName')
         filieres=request.form.get('courses').split(',')
         emailprof=request.form.get('email')
         
         dbprofs=client.profs
         dbprofs.profs.insert_one({'Full Name':profName , 'FiliersEnseignes':filieres ,'E-mail':emailprof })
         return redirect(url_for('admindashboard'))
   
#-------------Delete prof-----------------

@app.route('/prof/<prof_name>',methods=['POST'])  
def deletprof(prof_name):
    if request.method == 'POST':
        dbprofs=client.profs
        dbprofs.profs.delete_one({'Full Name':prof_name})
        return redirect(url_for('admindashboard'))

############### ABSENCE MANAGEMENT PAGE ##############

@app.route('/absence')
def absence():
    if profStatus == True:
        if request.method == 'GET':
            filierList=[]
            filierdb = client.get_database('timetable')
            table = filierdb.timetable.find({},{"_id":0,"filiere":1})
            for t in table:
                filierList.append(t['filiere'])
            return render_template("absence.html",filiers=filierList)
    else:
        return redirect(url_for("login"))


@app.route('/absence/list/<filiere>', methods =['GET'] )
def listabs(filiere):
    abs_hours = []
    names = []
    listStudents = client.get_database('listAbs')
    data = listStudents.listAbs.find({'Filiere':filiere},{'_id':0,'Filiere':0})
    for doc in data:
            for key in doc:
                names.append(doc[key]['Name'])
                abs_hours.append(doc[key]['abs_hours'])
    return render_template('liste_abs.html',filiere=filiere,studentsNames = names, absenceHours = abs_hours,zip=zip)

########### video #######################
camera = cv2.VideoCapture(0)
def generate_cam():
    simple = SimpleDetect()
    simple.load_image('image')
    while True:
        
        success, frame = camera.read()
        location , name = simple.knowing_faces(frame)
        if not success:
            break
        else:
            for cordination, name in zip(location, name):
                Y1, X2,Y2,X1 = cordination[0], cordination[1],cordination[2],cordination[3]
                cv2.putText(frame,name,(X1+30,Y1-10),cv2.FONT_HERSHEY_DUPLEX,1,(0,0,200),2)
                cv2.rectangle(frame,(X1,Y1),(X2,Y2),(0,0,200),4)
                cv2.imshow("Frame",frame)
                if name not in names:
                    names.append(name)
        ref, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n'+frame+b'\r\n')

@app.route('/video')
def video():
    return Response(generate_cam(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/done')
def done():
    camera.release()
    cv2.destroyAllWindows()
    makeattandence()
    return render_template('no_seance.html')

def makeattandence():
    global filier,names
    filier = filier[0]
    day = datetime.today().strftime('%A')
    time = getSeance()
    subject = ''
    Name=[]
    abss= []
    timeTablle = dict()
    db = client.get_database('timetable')
    tableresults = db.timetable.find({'filiere':filier},{'filiere':0,"_id":0})
    for t in tableresults:
        timeTablle = dict(t)
    for key in timeTablle:
        if key == day:
            for value in timeTablle[key]:
                if (time == value) is True:
                    temp =  timeTablle[key][value]
                    subject = temp[0]
    absenceDb = client.get_database('listAbs')
    addabsence = absenceDb[subject]
    fomatedDay = str(datetime.today()).split(' ')[0]
    addabsence.insert_one({'Day': fomatedDay,'time':time,'presence':names})
    namesList = absenceDb.listAbs.find({'Filiere':filier},{'_id':0,'Filiere':0})
    for n in namesList:
        for key in n:
            Name.append(key+'.'+'Name')
            abss.append(key+'.'+'abs_hours')
    for i,j in zip(Name,abss):
        absenceDb.listAbs.update_one({'Filiere':filier,i:{"$nin":list(names)}},{"$inc":{j:3}})
    
def getSeance():
    current = datetime.now()
    hour = int(current.hour)
    if hour >= 8 and hour <= 12:
        return '08:30-12'
    if hour >= 14 and hour <=18:
        return '14:30-18'
    else:
        return 'no sceance'


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

