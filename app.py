from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_mysqldb import MySQL
import os
from datetime import datetime
import random
import MySQLdb
import logging
from tmdb_utils import search_movie, get_poster_url
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'your_secret_key')  # Required for session management

# MySQL Configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'Saksham@2005')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'moviemitra')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL()
mysql.init_app(app)

def connect_db():
    try:
        connection = MySQLdb.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            passwd=os.getenv('MYSQL_PASSWORD', 'Saksham@2005'),
            db=os.getenv('MYSQL_DB', 'moviemitra')
        )
        return connection
    except MySQLdb.Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    connection = connect_db()
    if connection is None:
        logger.error("Failed to connect to database")
        return False
        
    try:
        with connection.cursor() as cur:
            # Drop existing tables
            cur.execute('DROP TABLE IF EXISTS BookingDetails')
            cur.execute('DROP TABLE IF EXISTS Users')
            cur.execute('DROP TABLE IF EXISTS Movies')
            
            # Create Users table
            cur.execute('''
                CREATE TABLE Users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(15) NOT NULL,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            logger.debug("Users table created successfully")
            
            # Create Movies table
            cur.execute('''
                CREATE TABLE Movies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    duration VARCHAR(50) NOT NULL,
                    language VARCHAR(50) NOT NULL,
                    poster_url VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            logger.debug("Movies table created successfully")
            
            # Create BookingDetails table
            cur.execute('''
                CREATE TABLE BookingDetails (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    movie_id INT,
                    theatre_name VARCHAR(50) NOT NULL,
                    show_date DATE NOT NULL,
                    show_time VARCHAR(10) NOT NULL,
                    seats_selected VARCHAR(255) NOT NULL,
                    snack_items VARCHAR(255),
                    snack_quantity INT,
                    total_amount DECIMAL(10,2) NOT NULL,
                    booking_id VARCHAR(20) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE,
                    FOREIGN KEY (movie_id) REFERENCES Movies(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            logger.debug("BookingDetails table created successfully")
            
            # Sample movies with local image paths
            sample_movies = [
                ('Inception', '2h 28min', 'English', '/static/movieposter/inception.jpg'),
                ('Deadpool', '1h 48min', 'English', '/static/movieposter/deadpool.jpg'),
                ('The Revenant', '2h 36min', 'English', '/static/movieposter/revenant.jpg')
            ]
            
            # Insert movies with local poster paths
            for movie in sample_movies:
                cur.execute('''
                    INSERT INTO Movies (name, duration, language, poster_url)
                    VALUES (%s, %s, %s, %s)
                ''', (movie[0], movie[1], movie[2], movie[3]))
            
            connection.commit()
            logger.debug("All database tables created and initialized successfully!")
            return True
            
    except MySQLdb.Error as e:
        logger.error(f"Error creating tables: {e}")
        return False
    finally:
        connection.close()

# Initialize database on startup
if not init_db():
    logger.error("Failed to initialize database. Please check the MySQL connection and try again.")

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        logger.debug(f"Login attempt for username: {username}")
        
        connection = connect_db()
        if connection:
            try:
                cur = connection.cursor()
                cur.execute('SELECT id, username FROM Users WHERE username = %s AND password = %s', (username, password))
                user = cur.fetchone()
                
                if user:
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    logger.debug(f"Login successful for user_id: {user[0]}")
                    flash('Login successful!')
                    return redirect(url_for('home'))
                else:
                    logger.debug(f"Login failed for username: {username}")
                    flash('Invalid username or password')
            except MySQLdb.Error as e:
                logger.error(f"Database error during login: {e}")
                flash('Database error occurred')
            finally:
                cur.close()
                connection.close()
        else:
            flash('Database connection error')
    
    return render_template('login.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        username = request.form['username']
        password = request.form['password']
        
        logger.debug(f"Creating account for username: {username}, email: {email}")
        
        connection = connect_db()
        if connection:
            try:
                cur = connection.cursor()
                # First check if username or email already exists
                cur.execute('SELECT id FROM Users WHERE username = %s OR email = %s', (username, email))
                existing_user = cur.fetchone()
                
                if existing_user:
                    flash('Username or email already exists')
                    return redirect(url_for('create_account'))
                
                # Insert new user
                cur.execute('''
                    INSERT INTO Users (name, email, phone, username, password) 
                    VALUES (%s, %s, %s, %s, %s)
                ''', (name, email, phone, username, password))
                connection.commit()
                
                logger.debug(f"Account created successfully for {username}")
                flash('Account created successfully! Please login.')
                return redirect(url_for('login'))
            except MySQLdb.Error as e:
                logger.error(f"Database error while creating account: {e}")
                connection.rollback()
                flash(f'Error creating account: {str(e)}')
            finally:
                cur.close()
                connection.close()
        else:
            flash('Database connection error')
    
    return render_template('create_account.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    connection = connect_db()
    if connection:
        try:
            cur = connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT * FROM Movies')
            movies = cur.fetchall()
            
            # Log movie data for debugging
            logger.debug(f"Found {len(movies)} movies")
            for movie in movies:
                logger.debug(f"Movie: {movie['name']}, Poster URL: {movie['poster_url']}")
            
            return render_template('home.html', movies=movies)
        finally:
            cur.close()
            connection.close()
    else:
        flash('Database connection error')
        return redirect(url_for('login'))

@app.route('/booking/<int:movie_id>', methods=['GET', 'POST'])
def booking(movie_id):
    if 'user_id' not in session:
        logger.debug("User not logged in, redirecting to login")
        flash('Please login first')
        return redirect(url_for('login'))
    
    connection = connect_db()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('home'))
        
    try:
        if request.method == 'POST':
            if 'confirm_booking' in request.form:
                logger.debug(f"Processing booking for user_id: {session['user_id']}, movie_id: {movie_id}")
                
                # Verify user exists
                cur = connection.cursor()
                cur.execute('SELECT id FROM Users WHERE id = %s', (session['user_id'],))
                user = cur.fetchone()
                
                if not user:
                    logger.error(f"User {session['user_id']} not found in database")
                    flash('User session is invalid. Please login again.')
                    session.clear()
                    return redirect(url_for('login'))
                
                # Get form data
                theatre_name = request.form['theatre_name']
                show_date = request.form['show_date']
                show_time = request.form['show_time']
                seats_selected = request.form['seats_selected']
                snack_items = request.form.getlist('snack_items')
                snack_quantity = request.form.get('snack_quantity', 0)
                total_amount = request.form['total_amount']
                
                # Generate unique booking ID
                booking_id = f"BK{random.randint(10000, 99999)}"
                
                # Convert snack_items list to string
                snack_items_str = ', '.join(snack_items) if snack_items else ''
                
                logger.debug(f"Booking details - Theatre: {theatre_name}, Date: {show_date}, Time: {show_time}, Seats: {seats_selected}")
                
                try:
                    cur.execute('''
                        INSERT INTO BookingDetails 
                        (user_id, movie_id, theatre_name, show_date, show_time, seats_selected, 
                        snack_items, snack_quantity, total_amount, booking_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (session['user_id'], movie_id, theatre_name, show_date, show_time,
                         seats_selected, snack_items_str, snack_quantity, total_amount, booking_id))
                    connection.commit()
                    logger.debug(f"Booking confirmed with ID: {booking_id}")
                    flash(f'Booking confirmed successfully! Your booking ID is: {booking_id}')
                    return redirect(url_for('home'))
                except MySQLdb.Error as e:
                    logger.error(f"Error processing booking: {e}")
                    connection.rollback()
                    flash(f'Error processing booking: {str(e)}')
                    return redirect(url_for('booking', movie_id=movie_id))
            
            elif 'cancel_booking' in request.form:
                flash('Booking cancelled')
                return redirect(url_for('home'))
        
        # GET request - show booking form
        cur = connection.cursor()
        cur.execute('SELECT * FROM Movies WHERE id = %s', (movie_id,))
        movie = cur.fetchone()
        
        if not movie:
            logger.error(f"Movie with ID {movie_id} not found")
            flash('Movie not found')
            return redirect(url_for('home'))

        # Generate seat layout
        seat_layout = []
        for row in range(5):  # 5 rows
            row_seats = []
            row_letter = chr(65 + row)  # A, B, C, D, E
            for col in range(8):  # 8 seats per row
                seat = {
                    'label': f'{row_letter}{col + 1}',
                    'price': 50 if row < 2 else (70 if row < 4 else 90)
                }
                row_seats.append(seat)
            seat_layout.append(row_seats)

        return render_template('booking.html', movie=movie, seat_layout=seat_layout)
        
    except MySQLdb.Error as e:
        logger.error(f"Database error: {e}")
        flash(f'Database error: {str(e)}')
        return redirect(url_for('home'))
    finally:
        if 'cur' in locals():
            cur.close()
        connection.close()

# Add a route to check booking status
@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
        
    connection = connect_db()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('home'))
        
    try:
        cur = connection.cursor(MySQLdb.cursors.DictCursor)  # Use DictCursor
        cur.execute('''
            SELECT b.*, m.name as movie_name 
            FROM BookingDetails b 
            JOIN Movies m ON b.movie_id = m.id 
            WHERE b.user_id = %s 
            ORDER BY b.created_at DESC
        ''', (session['user_id'],))
        bookings = cur.fetchall()
        return render_template('my_bookings.html', bookings=bookings)
    except MySQLdb.Error as e:
        flash(f'Error retrieving bookings: {str(e)}')
        return redirect(url_for('home'))
    finally:
        if 'cur' in locals():
            cur.close()
        connection.close()

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

# Add a route to serve static files directly
@app.route('/static/movieposter/<path:filename>')
def serve_movie_poster(filename):
    logger.debug(f"Attempting to serve movie poster: {filename}")
    try:
        return send_from_directory('static/movieposter', filename)
    except Exception as e:
        logger.error(f"Error serving movie poster {filename}: {str(e)}")
        return None

@app.route('/cancel_booking/<booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        flash('Please login first')
        return redirect(url_for('login'))
        
    connection = connect_db()
    if not connection:
        flash('Database connection error')
        return redirect(url_for('my_bookings'))
        
    try:
        cur = connection.cursor()
        # First verify that the booking belongs to the current user
        cur.execute('''
            SELECT id FROM BookingDetails 
            WHERE booking_id = %s AND user_id = %s
        ''', (booking_id, session['user_id']))
        booking = cur.fetchone()
        
        if not booking:
            flash('Booking not found or you do not have permission to cancel it')
            return redirect(url_for('my_bookings'))
            
        # Delete the booking
        cur.execute('DELETE FROM BookingDetails WHERE booking_id = %s', (booking_id,))
        connection.commit()
        
        flash('Booking cancelled successfully')
        return redirect(url_for('my_bookings'))
        
    except MySQLdb.Error as e:
        logger.error(f"Error cancelling booking: {e}")
        connection.rollback()
        flash(f'Error cancelling booking: {str(e)}')
        return redirect(url_for('my_bookings'))
    finally:
        if 'cur' in locals():
            cur.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)
