from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
  
app = Flask(__name__)
  
app.secret_key = 'xyzsdfg'
  
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Breaking@947'
app.config['MYSQL_DB'] = 'railway_management_system'
  
mysql = MySQL(app)
  
@app.route('/')
@app.route('/main_page')
def main_page():
    # Render the booking page template
    return render_template('main_page.html')

@app.route('/login', methods =['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            return render_template('user.html', message=message)
        else:
            message = 'Please enter correct email / password!'
    return render_template('login.html', message=message)

@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff_users WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['staffid']
            session['name'] = user['name']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            return render_template('staff.html', message=message)
        else:
            message = 'Please enter correct email / password!'
    return render_template('staff_login.html', message=message)

@app.route('/add_train', methods=['GET', 'POST'])
def add_train():
    if request.method == 'GET':
        # Check if the user is logged in and has the necessary permissions (e.g., staff role)
        if 'loggedin' in session and session['loggedin'] and 'role' in session and session['role'] == 'staff':
            return render_template('add_train.html')
        else:
            # If user is not logged in or does not have staff permissions, redirect to login page
            return redirect(url_for('staff_login'))
    elif request.method == 'POST':
        # Extract data from the form submission
        train_name = request.form['name']
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        departure_time = request.form['departure_time']
        price = request.form['price']
        staff_id = request.form['staff_id']
        
        # Insert the data into the trains table in the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO trains name, from_location, to_location, departure_time, price, staff_id) VALUES (%s, %s, %s, %s, %s, %s)",
                       (train_name, from_location, to_location, departure_time, price, staff_id))
        mysql.connection.commit()
        cursor.close()

        # Redirect the user back to the staff dashboard after adding a train
    return render_template('staff.html')



@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin WHERE email = %s AND password = %s', (email, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['adminid']
            session['name'] = user['name']
            session['email'] = user['email']
            message = 'Logged in successfully!'
            return render_template('admin.html', message=message)
        else:
            message = 'Please enter correct email / password!'
    return render_template('admin_login.html', message=message)
  
  
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))
  
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO user (userid, name, email, password) VALUES (NULL, %s, %s, %s)', (userName, email, password))
            mysql.connection.commit()
            message = 'You have successfully registered!'
    elif request.method == 'POST':
        message = 'Please fill out the form!'
    return render_template('register.html', message=message)

@app.route('/search', methods=['GET'])
def search():
    # Get the search query and other parameters from the URL parameters
    query = request.args.get('query')
    from_location = request.args.get('from')
    to_location = request.args.get('to')
    date = request.args.get('date')

    if not query and not from_location and not to_location and not date:
        # If no search criteria is provided, render an error message
        return render_template('error.html', message='Please provide at least one search criteria.')

    # Execute a SQL query to fetch train details based on the search criteria
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query_params = []
    query_string = "SELECT * FROM trains WHERE 1=1"  # Base query string

    if from_location:
        query_string += " AND from_location LIKE %s"
        query_params.append('%' + from_location + '%')
    if to_location:
        query_string += " AND to_location LIKE %s"
        query_params.append('%' + to_location + '%')
    if date:
        query_string += " AND date LIKE %s"
        query_params.append('%' + date + '%')

    cursor.execute(query_string, query_params)
    trains = cursor.fetchall()

    cursor.close()

    if not trains:
        # If no trains are found for the given search criteria, render an appropriate message
        return render_template('error.html', message='No trains found for the given search criteria.')

    # Render the template with the search results
    return render_template('search_results.html', trains=trains)

def calculate_total_price(num_passengers):
    # Implement your logic to calculate the total price based on the number of passengers
    # Replace this with your actual calculation logic
    return num_passengers * 50.00 

@app.route('/booking', methods=['POST'])
def booking():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    # Process the form data and save booking to the database
    num_passengers = int(request.form['num_passengers'])
    selected_seats = request.form.getlist('seat')  # Get the manually selected seats
    train_id = request.form['train_id']  # Get the train_id from the form
    userid = session['userid']  # Get the user_id from the session

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Check if selected seats are already booked for the same train and date
        for seat in selected_seats:
            cursor.execute("SELECT * FROM booking WHERE train_id = %s AND FIND_IN_SET(%s, seat_numbers)", (train_id, seat))
            if cursor.fetchone():
                # Seat is already booked, so redirect back with an error message
                return render_template('error.html', message=f'Seat {seat} is already booked for this train. Please choose another seat.')

        # Save booking details to the database
        cursor.execute("INSERT INTO booking (user_id, train_id, num_passengers, total_price, seat_numbers) VALUES (%s, %s, %s, %s, %s)",
                       (session['userid'], train_id, num_passengers, calculate_total_price(num_passengers), ','.join(selected_seats)))
        mysql.connection.commit()
        cursor.close()

        # After successful booking, redirect to booking confirmation page
        return redirect(url_for('booking_confirmation', train_id=train_id, num_passengers=num_passengers,
                                total_price=calculate_total_price(num_passengers), selected_seats=selected_seats))
    except Exception as e:
        print("Error occurred while saving booking:", e)
        return render_template('error.html', message='Failed to book. Please try again later.')

@app.route('/booking_confirmation')
def booking_confirmation():
    # Retrieve booking details from the URL parameters
    train_id = request.args.get('train_id')
    num_passengers = request.args.get('num_passengers')
    total_price = request.args.get('total_price')
    selected_seats = request.args.get('selected_seats')

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Fetch train name based on train_id
        cursor.execute("SELECT name FROM trains WHERE train_id = %s", (train_id,))
        train_name = cursor.fetchone()['name']

        # Fetch booking ID for the logged-in user
        cursor.execute("SELECT booking_id FROM booking WHERE user_id = %s ORDER BY booking_id DESC LIMIT 1", (session['userid'],))
        booking_id = cursor.fetchone()['booking_id']
        
        cursor.close()

        return render_template('booking_confirmation.html', train_id=train_id, train_name=train_name,
                               num_passengers=num_passengers, total_price=total_price,
                               selected_seats=selected_seats, booking_id=booking_id)
    except Exception as e:
        print("Error occurred while retrieving booking information:", e)
        return render_template('error.html', message='Failed to retrieve booking information.')



if __name__ == "__main__":
    app.run(debug=True)