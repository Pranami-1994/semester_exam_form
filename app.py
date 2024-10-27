from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import uuid
import json
from flask import jsonify 
# import mysql.connector
# from mysql.connector import Error
from pymysql import MySQLError
import hashlib
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # For print messages

# RDS configuration
rds_host = 'database-1.c3qeysk6ww3b.ap-south-1.rds.amazonaws.com'  # Replace with your RDS endpoint
rds_port = 3306  # Default MySQL port
db_username = 'admin'  # Replace with your database username
db_password = 'pranamidas1994'  # Replace with your database password
db_name = 'examform'  # Replace with your database name

def connect_to_rds():
    try:
        connection = pymysql.connect(
            host=rds_host,
            user=db_username,
            password=db_password,
            database=db_name,
            port=rds_port
        )
        print("Connected to the database!")
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to the database: {e}")
        return None  


def generate_application_number():
    timestamp = str(datetime.now().timestamp())  # Get the current timestamp
    random_num = str(random.randint(1000, 9999))
    unique_str = timestamp + random_num
    application_number = hashlib.sha1(unique_str.encode()).hexdigest()[:10]  # Take first 10 characters of hash
    return f"APP{application_number}"


# Homepage route where movies are displayed
@app.route('/')
def index():
    print("enter into the index")
    return render_template('index.html')

# Route to register
@app.route('/register', methods=['GET','POST'])
def register():
    print("enter into the register")
    if request.method == 'POST':
        name = request.form['name']
        rollno = request.form['rollno']
        batch = request.form['batch']
        department  = request.form['department']
        fathername = request.form['fathername']
        mothername = request.form['mothername']
        address = request.form['address']
        email = request.form['email']
        password = request.form['password']
        print(name)

        connection = connect_to_rds()
        if  connection:
            cursor =  connection.cursor()
            try:
                cursor.execute("INSERT INTO student_details (student_name,batch,rollno,department,father_name,mother_name,address,email,password) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (name,batch,rollno,department,fathername,mothername,address,email,password))
                connection.commit()
                print("Thanks for registering!","success")
                return redirect(url_for('login'))
            except pymysql.MySQLError as err:
                print(f"Error: {err}", "danger")
            finally:
                cursor.close()
                connection.close()
        else:
            print("Error connecting to the database")

    return render_template('register.html')    
    
# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    print("enter into the login")
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = connect_to_rds()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT * FROM student_details WHERE email=%s AND password=%s", (email, password))
                student = cursor.fetchone()

                if student:
                    print("current user", student)
                    session['student_id'] = student[0]
                    session['student_name'] = student[3]


                    print("Login successful!", "success")

                    return redirect(url_for('select_exam'))
                else:
                    print("Invalid login. Please try again.", "danger")
            except pymysql.MySQLError as err:
                print(f"Error: {err}", "danger")
            finally:
                cursor.close()
                connection.close()
        else:
            print("Database connection failed!", "danger")
    return render_template('login.html')


@app.route('/exam_selection', methods=['GET','POST'])
def select_exam():
    
    connection = connect_to_rds()

    if request.method ==  'POST':
        session['year'] = request.form['year']
        session['semester'] = request.form['semester']

        if connection:
            
            cursor = connection.cursor()

            try:
                print("enter to the try block")       
                cursor.execute("SELECT * FROM exam_fee WHERE  year=%s and semester=%s", (session['year'], session['semester'],))
                exam_fee = cursor.fetchone()
                print(exam_fee)
                session['fee'] = exam_fee[2]
                print(exam_fee[2])
                
                if  exam_fee:

                    cursor.execute("INSERT INTO application (student_id, year, semester, payment) VALUES (%s,%s,%s,%s)",
                                (session['student_id'], session['year'], session['semester'], session['fee']))
                    print("1234")
                    connection.commit()

                    return redirect(url_for('application'))
            
            except pymysql.MySQLError as err:
                return redirect(url_for('login'))
            finally:
                cursor.close()
                connection.close()
        else:
            return redirect(url_for('submit_application_no'))
    
    return render_template('exam_selection.html')

    

@app.route('/application', methods=['GET','POST'])
def application():
    try:
        print("enter into application")
        connection = connect_to_rds()
        cursor = connection.cursor()

        cursor.execute("""select s.student_id, s.student_name,s.batch,s.department,a.year,a.semester,s.rollno,a.payment,
                       s.father_name,s.mother_name,s.address,s.email 
                       from student_details s join application a
                       on s.student_id = a.student_id
                       where  s.student_id = %s and a.year = %s and a.semester = %s""", (session['student_id'],session['year'],session['semester']))
        application_details = cursor.fetchone()

        application_details = list(application_details)
        
        # print("application details are: ", session['application_details'])

        if len(application_details) > 0 :
            keys = ['student_id','name','batch','department','year','semester','rollno', 'fee', 'father', 'mother', 'address','email']
            session['application'] = dict(zip(keys,  application_details))

            print(application)

            cursor.close()
            return render_template('application.html',application = session['application'])
            
    except pymysql.MySQLError as err:
        return redirect(url_for('login'))
    
    finally:
        cursor.close()
        connection.close()

@app.route('/select_payment', methods =['GET','POST'])

def confirm_payment():

    if request.method == 'POST':

        payment_method = request.form['payment']
        
        print(payment_method)

        if payment_method:
            payment_status = "Paid"
            session['application_number'] = generate_application_number()
            # str(uuid.uuid4())
            
            print(session['application_number'])
        else:
            payment_status = "Not Paid"
            session['application_number'] = 'None'
        print("payment_status")

        connection = connect_to_rds()
        
        if  connection:

            cursor =  connection.cursor()

            try:

                student_data = session.get('application')

                if student_data:
                    # Now access the 'username' key
                    studentid = student_data['student_id']
                    studentname = student_data.get('name')
                    batch = student_data.get('batch')
                    department = student_data.get('department')
                    year = student_data.get('year')
                    semester = student_data.get('semester')
                    rollno = student_data.get('rollno')
                    fee = student_data.get('fee')
                    father = student_data.get('father')
                    mother = student_data.get('mother')
                    address = student_data.get('address')
                    email = student_data.get('email')

                cursor.execute("""INSERT INTO application_details (student_id, student_name, batch, department, year, 
                               semester, rollno, payment, father_name, mother_name, address, email, payment_status, 
                               application_number) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                                (studentid,studentname,batch,department,year,semester,rollno,fee,father,mother,address,email,payment_status,session['application_number']))
                
                # cursor.execute("update application_details set payment_status = %s and application_number=%s where student_id = %s and year =%s and semester=%s",
                #                 (payment_status,session['application_number'], session['student_id'],session['year'],session['semester']))  
                    
                connection.commit()

                return redirect(url_for('submission'))
            
            except pymysql.MySQLError as err:

                return redirect(url_for('login'))
            
            finally:
                cursor.close()
                connection.close()
            
    return render_template('select_payment.html')
  

@app.route('/submission')
def submission():

    if 'application_number' not in session:

        return "Application number not found"
    
    application_number = {'app_num' : session['application_number']}

    # application_number['app_num'] = session['application_number']
  
    return render_template('submission.html', application_number = application_number)



@app.route('/view_application')
def view_application():

    application_no1 = session['application_number']
    application_no2 = session['application_no2']
      
    try:
        connection = connect_to_rds()
        
        if  connection:
            cursor = connection.cursor()

            cursor.execute("""select student_name, batch, department, year, semester, rollno,payment,
                            father_name,mother_name,address,email,payment_status, application_number
                           from  application_details where application_number=%s or application_number=%s""", 
                            (application_no1,application_no2))

            application = cursor.fetchone()

            application = list(application)
        
        print(application)

        if len(application) > 0 :
            keys = ['name','batch','department','year','semester','rollno', 'fee', 'father', 'mother', 'address','email','payment_status','application_number']
            application = dict(zip(keys,  application))
            print(application)

            cursor.close()
            return render_template('view_application.html',application = application)
            
    except pymysql.MySQLError as err:
        return redirect(url_for('login'))   

@app.route('/submit_application_no', methods =  ['GET','POST'])

def submit_application_no():

    if request.method == 'POST':
        session['application_no2'] = request.form['application_no']
        name = request.form['name']
        password = request.form['password']
      
        return  redirect(url_for('view_application', application_number = session['application_no2'], name=name, password=password))
    else:
        print('Application number is not found')

    return render_template('submit_application_no.html')

    
if __name__ == '__main__':
    app.run(debug=True, port=3000)




