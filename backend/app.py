import os
import csv
from io import StringIO
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func, or_
from flask_jwt_extended import JWTManager, create_access_token, jwt_required , get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from models import CustomerProfile, db , User, Service, ProfessionalProfile, ServiceRequest
from werkzeug.utils import secure_filename   
from flask_cors import CORS 
from flasgger import Swagger
from flask_caching import Cache
from datetime import datetime as DateTime
from celery import Celery
import requests
from celery.schedules import crontab
from flask_mail import Mail, Message

app = Flask(__name__,template_folder='../frontend', static_folder='../frontend', static_url_path='/static')

#Configure Celery and Redis
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['result_backend'],
        broker=app.config['broker_url'] 
    )
    celery.conf.update(app.config)
    # Attach Flask application context to Celery
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():  # Push the Flask app context here
                return super().__call__(*args, **kwargs)
    celery.Task = ContextTask
    return celery

app.config['broker_url'] = 'redis://localhost:6379/0'
app.config['result_backend'] = 'redis://localhost:6379/0'

celery = make_celery(app)

#Configure mail
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587  # Use 587 for TLS
app.config['MAIL_USE_TLS'] = True  # TLS is required
app.config['MAIL_USERNAME'] = 'apikey'  # Use 'apikey' as the username (this is required by SendGrid)
app.config['MAIL_PASSWORD'] = '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'  # Your SendGrid API key (replace with your actual API key)
app.config['MAIL_DEFAULT_SENDER'] = '21f1006140@ds.study.iitm.ac.in'  # Your email address to send from
mail = Mail(app)

# Configure file upload settings
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to save files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}  # Allowed file extensions

# Configure Cache
cache = Cache(app, config={'CACHE_TYPE': 'RedisCache','CACHE_DEFAULT_TIMEOUT': 30,'CACHE_REDIS_HOST': 'localhost','CACHE_REDIS_PORT': 6379,'CACHE_REDIS_DB': 0})

#CORS Configuration
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

#Swagger Configuration
swagger = Swagger(app)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_secret_key'

jwt = JWTManager(app)

# Check if file extension is allowed
def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

db.init_app(app)

first_request = True
# Initialize the database
@app.before_request
def create_tables():
  global first_request
  if first_request:
    db.create_all()
    first_request = False

# Serve downloadable files from a 'files' directory
@app.route('/download/<string:filename>', methods=['GET'])
@jwt_required()
def download_file(filename):
  """
    Update an existing service by an admin.
    This endpoint allows an admin to update an existing service with details like name, type, price, and description.
    ---
    tags:
      - File Management
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: The ID of the service to be updated.
        example: 1
      - name: service
        in: body
        description: Service details to be updated
        required: true
        schema:
          type: object
          properties:
            service_type:
              type: string
              description: The type of service (e.g., 'plumbing', 'cleaning')
              example: 'plumbing'
            name:
              type: string
              description: The name of the service
              example: 'Water Leak Repair'
            price:
              type: number
              description: The price of the service
              example: 100.50
            description:
              type: string
              description: A brief description of the service
              example: 'Fixes water leaks in pipes and faucets.'
    responses:
      200:
        description: Service updated successfully.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "success"
            message:
              type: string
              example: "Service updated successfully"
      400:
        description: Missing required field or invalid input data.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "Invalid input data"
      401:
        description: Unauthorized access (not an admin).
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "Please login as admin to update service"
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "An error occurred while updating the service"
    """
  # Set the directory where your files are located
  file_directory = os.path.join(app.root_path, 'uploads')
  
  # Serve the file from the directory as an attachment
  return send_from_directory(file_directory, filename, as_attachment=True)

#Celery Reminders 
@celery.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    # Fetch pending service requests and pre-load related professionals
    pending_requests = (
        ServiceRequest.query.filter_by(service_status='requested')
        .join(ProfessionalProfile, ServiceRequest.professional_id == ProfessionalProfile.user_id)
        .add_columns(ProfessionalProfile.full_name)
        .all()
      )

    for service_request in pending_requests:
      professional_name = service_request.full_name
      #hardcoded chat_hook for demo
      chat_hook_url = 'https://chat.googleapis.com/v1/spaces/AAAAWYwxXr0/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=8Vdtgp_lHZv0jKlnwNqnD57byXmMAPR1obmSlZiLUTc'
      
      # Prepare and send the reminder message
      message = {
          "text": f"Reminder: {professional_name}! You have pending service requests. Please visit or take action."
      }

      try:
          response = requests.post(chat_hook_url, json=message, timeout=10)
          response.raise_for_status()  # Raise HTTPError for bad responses
      except requests.RequestException as e:
          # Log the error for monitoring/debugging
          print(f"Failed to send reminder to {professional_name}: {e}")
          continue
    return "Daily reminders sent successfully!"

#Celery Monthly Activity Report
@celery.task(name="tasks.send_monthly_activity_report")
def send_monthly_activity_report():
    # Generate the report
    customers = CustomerProfile.query.all()
    for customer in customers:
      report = generate_customer_report(customer.user_id)  
      html_content = render_report_as_html(report)
      try:
        # Send email
        msg = Message(
            f"Monthly Activity Report - {DateTime.now().strftime('%B')}",
            #hardcoded email_id for demo
            recipients=['21f1006140@ds.study.iitm.ac.in'],
            html=html_content
        )
        mail.send(msg)
      except Exception as e:
        print(f"Error sending email: {e}")
    return "Monthly activity reports sent successfully!"

def generate_customer_report(customer_id):
    # Query to get customer profile
    customer = CustomerProfile.query.filter_by(user_id=customer_id).first()

    if not customer:
        return {"error": "Customer not found"}

    # Query to calculate services used and total spent
    report_data = (
        db.session.query(
            func.count(ServiceRequest.id).label("services_used"),       # Total completed services
            func.sum(Service.price).label("total_spent")                # Sum of service prices
        )
        .join(Service, ServiceRequest.service_id == Service.id)         # Join with Service table
        .filter(ServiceRequest.customer_id == customer_id)             # Filter by customer ID
        .filter(ServiceRequest.service_status == "completed")          # Include only completed services
        .one()  # Fetch a single row
    )

    # Prepare the report
    return {
        "customer_name": customer.full_name,
        "services_used": report_data.services_used or 0,
        "total_spent": report_data.total_spent or 0.0,
        "address": customer.address,
        "pin_code": customer.pin_code,
        "date_range": "Till Date"
    }
def render_report_as_html(report):
    # Generate HTML string from JSON data
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Customer Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }}
            .report-container {{
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                max-width: 600px;
                margin: auto;
            }}
            .report-container h1 {{
                text-align: center;
                color: #333;
            }}
            .report-item {{
                margin-bottom: 10px;
            }}
            .report-item span {{
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="report-container">
            <h1>Customer Report</h1>
            <div class="report-item">
                <span>Name:</span> {report['customer_name']}
            </div>
            <div class="report-item">
                <span>Address:</span> {report['address']}
            </div>
            <div class="report-item">
                <span>Pin Code:</span> {report['pin_code']}
            </div>
            <div class="report-item">
                <span>Services Used:</span> {report['services_used']}
            </div>
            <div class="report-item">
                <span>Total Spent:</span> ${report['total_spent']}
            </div>
            <div class="report-item">
                <span>Date Range:</span> {report['date_range']}
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

#Celery generate csv
@celery.task(name="export_service_requests")
def export_service_requests(professional_id):
    # Fetch closed requests
    closed_requests = ServiceRequest.query.filter(
        ServiceRequest.professional_id == professional_id,
        ServiceRequest.service_status.in_(['completed'])
    ).all()
    closed_requests_dict = [closed_request.as_dict() for closed_request in closed_requests]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=closed_requests_dict[0].keys())
    writer.writeheader()
    writer.writerows(closed_requests_dict)

    # Save or email the CSV file
    save_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'reports/', professional_id+'_closed_requests.csv')
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as f:
        f.write(output.getvalue())
    notify_admin(f"CSV export complete for Professional ID: {professional_id}. File saved at {save_path}.")    
    return save_path

#Trigger job from admin dashboard
@app.route('/admin/export/<string:professional_id>', methods=['GET'])
@jwt_required()
def export_requests(professional_id):
    """
    Initiate a background task to export service requests for a professional.
    ---
    tags:
      - Celery
    parameters:
      - name: professional_id
        in: path
        type: string
        required: true
        description: The ID of the professional whose service requests are to be exported.
    responses:
      202:
        description: Task accepted, export process started.
      401:
        description: Unauthorized (Admin role required).
      403:
        description: Forbidden (Insufficient permissions).
    """
    task = export_service_requests.delay(professional_id)
    return jsonify({'task_id': task.id}), 202

# Notify admin
def notify_admin(message):
    admin_email = "21f1006140@ds.study.iitm.ac.in"  
    msg = Message(
        subject="Admin Notification",
        recipients=[admin_email],
        body=message
    )
    mail.send(msg)

@app.route('/admin/reports/list', methods=['GET'])
@jwt_required()
def list_downloads():
    """
    List all downloadable CSV files in the 'reports' directory.
    ---
    tags:
      - File Management
    responses:
      200:
        description: List of downloadable files retrieved successfully.
      401:
        description: Unauthorized access.
      500:
        description: Error while fetching the file list.
    """
    # List all CSV files in the upload directory
    files = [f for f in os.listdir('reports') if f.endswith('.csv')]
    return jsonify({'downloads': files})

@app.route('/admin/reports/download/<string:filename>', methods=['GET'])
@jwt_required()
def download_reports_file(filename):
  """
    Download a report file from the 'reports' directory.
    ---
    tags:
      - File Management
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: The name of the file to download.
    responses:
      200:
        description: File successfully downloaded.
      401:
        description: Unauthorized access.
      404:
        description: File not found.
      500:
        description: An error occurred while processing the request.
    """
  # Set the directory where your files are located
  file_directory = os.path.join(app.root_path, 'reports')
  
  # Serve the file from the directory as an attachment
  return send_from_directory(file_directory, filename, as_attachment=True)

#Schedule task using celery
celery.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'tasks.send_daily_reminders',
        'schedule': crontab(hour=18, minute=0),  # 6 PM daily
        #'schedule': crontab(minute='*/1'),
    }
}
celery.conf.beat_schedule['send-monthly-report'] = {
    'task': 'tasks.send_monthly_activity_report',
    'schedule': crontab(hour=8, minute=0, day_of_month=1),  # 8 AM on the 1st
    #'schedule': crontab(minute='*/1'),
}

# Home Route
@app.route('/')
def index():
  """
  Home Page
  ---
  tags:
    - Home
  responses:
    200:
      description: Returns the rendered HTML for the homepage
  """
  return render_template('index.html') 

@app.route('/register', methods=['POST'])
def register():
  """
  User Registration
  ---
  tags:
    - Authentication
  parameters:
    - in: body
      name: body
      required: true
      schema:
        type: object
        properties:
          username:
            type: string
            description: Username for the new user
            example: john_doe
          password:
            type: string
            description: Password for the new user
            example: StrongPassword123
          role:
            type: string
            description: Role of the user (customer or professional)
            example: customer
  responses:
    200:
      description: User registration successful
      content:
        application/json:
          schema:
            type: object
            properties:
              category:
                type: string
                example: success
              message:
                type: string
                example: Registration successful!
    401:
      description: User already exists or invalid role
      content:
        application/json:
          schema:
            type: object
            properties:
              category:
                type: string
                example: danger
              message:
                type: string
                example: User already exists!
    400:
      description: Bad request
      content:
        application/json:
          schema:
            type: object
            properties:
              category:
                type: string
                example: danger
              message:
                type: string
                example: Bad request
  """  
  if request.method == 'POST':
    username = request.json.get('username')
    password = request.json.get('password')
    role = request.json.get('role')
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
      return jsonify({"category": "danger","message":"User already exists!"}), 401
    if role not in ['customer', 'professional']:
      return jsonify({"category": "danger","message":"Invalid role!"}), 401
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, password=hashed_password, role=role, approve=False, blocked=True)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"category": "success","message":"Registration successful!"}), 200
  return jsonify({"category": "danger","message":"Bad request"}), 400

@app.route('/login', methods=['POST'])
def login():
  """
  User Login
  ---
  tags:
    - Authentication
  parameters:
    - in: body
      name: body
      required: true
      schema:
        type: object
        properties:
          username:
            type: string
            description: Username of the user
            example: john_doe
          password:
            type: string
            description: Password of the user
            example: StrongPassword123
  responses:
    200:
      description: Successful login with access token
      content:
        application/json:
          schema:
            type: object
            properties:
              access_token:
                type: string
                description: JWT access token
                example: eyJhbGciOiJIUzI1NiIsInR5...
    401:
      description: Unauthorized due to invalid credentials or user restrictions
      content:
        application/json:
          schema:
            type: object
            properties:
              category:
                type: string
                example: danger
              message:
                type: string
                example: Your account is blocked! Please contact the admin.
    400:
      description: Bad request
      content:
        application/json:
          schema:
            type: object
            properties:
              category:
                type: string
                example: danger
              message:
                type: string
                example: Bad request
  """
  if request.method == 'POST':
    username = request.json.get('username')
    password = request.json.get('password')
    user = User.query.filter(User.username==username).filter(User.role.in_(['customer','professional'])).first()
    if user and check_password_hash(user.password, password):
      if user.role == 'customer':
        #Check if customer profile is approved
        if not user.approve:
          return jsonify({"category": "danger","message": "Your account is not approved yet! Please wait for the admin to approve."}), 401
        # Check if customer profile is blocked
        if user.blocked:
          return jsonify({"category": "danger","message": "Your account is blocked! Please contact the admin."}), 401
        # Check if the customer profile is incomplete
        customer_profile = CustomerProfile.query.filter_by(user_id = user.id).first()
        if not customer_profile:
          additional_claims = {"user_id": user.id, "role": user.role,"redirect" : "customer_profile"}
          access_token = create_access_token(username, additional_claims=additional_claims)
          return jsonify(access_token=access_token)
        additional_claims = {"user_id": user.id, "role": user.role,"redirect" : "customer_dashboard"}
        access_token = create_access_token(username, additional_claims=additional_claims)
        return jsonify(access_token=access_token)  
      elif user.role == 'professional':
        # Check if the professional profile is incomplete
        professional_profile = ProfessionalProfile.query.filter_by(user_id = user.id).first()
        if not professional_profile:
          additional_claims = {"user_id": user.id, "role": user.role, "redirect" : "professional_profile"}
          access_token = create_access_token(username, additional_claims=additional_claims)
          return jsonify(access_token=access_token)
        # Check if professional profile is approved
        if not user.approve:
          return jsonify({"category": "danger","message": "Your account is not approved yet! Please wait for the admin to approve."}), 401
        # Check if professional profile is blocked
        if user.blocked:
          return jsonify({"category": "danger","message": "Your account is blocked! Please contact the admin."}), 401
        additional_claims = {"user_id": user.id, "role": user.role, "redirect" : "professional_dashboard"}
        access_token = create_access_token(username, additional_claims=additional_claims)
        return jsonify(access_token=access_token)            
    return jsonify({"category": "danger","message": "Bad username or password"}), 401
  return jsonify({"category": "danger","message": "Bad request"}), 400
    

@app.route('/get-claims', methods=['GET'])
@jwt_required()
def get_claims():
    """
    Get JWT Claims
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successfully retrieved JWT claims
        content:
          application/json:
            schema:
              type: object
              properties:
                claims:
                  type: object
                  description: JWT claims containing user-specific data
                  example:
                    user_id: 123
                    role: customer
                    redirect: customer_dashboard
      401:
        description: Unauthorized, token missing or invalid
        content:
          application/json:
            schema:
              type: object
              properties:
                msg:
                  type: string
                  example: Missing Authorization Header
    """
    # Get the claims from the JWT
    claims = get_jwt()

    # Return claims (such as role and permissions) in JSON format
    return jsonify(claims=claims), 200

# Admin Login Route
@app.route('/admin/login', methods=['POST'])
def admin_login():
  """
    Admin Login
    ---
    tags:
      - Admin
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              username:
                type: string
                example: admin
              password:
                type: string
                example: admin123
    responses:
      200:
        description: Successfully authenticated
        content:
          application/json:
            schema:
              type: object
              properties:
                access_token:
                  type: string
                  example: "jwt_access_token_here"
      401:
        description: Invalid credentials
    """
  if request.method == 'POST':
    username = request.json.get('username')
    password = request.json.get('password')
    user = User.query.filter_by(username=username, role='admin').first()
    if user and check_password_hash(user.password, password):
      additional_claims = {"admin_user_id": user.id, "role": user.role}
      access_token = create_access_token(username, additional_claims=additional_claims)
      return jsonify(access_token=access_token)
    return jsonify({"category": "danger","message": "Bad username or password"}), 401
  return jsonify({"category": "danger","message": "Bad request"}), 400
  
@app.route('/admin/profile', methods=['POST'])
@jwt_required()
def admin_profile():
  """
  Admin Profile Access
  ---
  tags:
    - Admin
  security:
    - BearerAuth: []
  responses:
    200:
      description: Profile access denied for admin
      content:
        application/json:
          schema:
            type: object
            properties:
              message:
                type: string
                example: "Admin! You can't make changes to your profile"
              category:
                type: string
                example: "danger"
  """
  return jsonify({"message":"Admin! You can't make changes to your profile","category": "danger"}), 200

# Admin Dashboard
@app.route('/admin/dashboard', methods=['POST'])
@jwt_required()
def admin_dashboard():
  """
    Admin Dashboard
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successfully retrieved admin dashboard data
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Admin dashboard data retrieved successfully."
                category:
                  type: string
                  example: "success"
                services:
                  type: array
                  items:
                    type: object
                professional_profiles:
                  type: array
                  items:
                    type: object
                service_requests:
                  type: array
                  items:
                    type: object
                customers:
                  type: array
                  items:
                    type: object
    """
  # Verify admin role
  claims = get_jwt()
  if claims['role'] != 'admin':
    return jsonify({"message": "Not an Admin!", "category": "danger"}), 401
  
  # Initialize dictionaries for collecting related data
  user_dict = {}
  prof_dict = {}
  service_type = {}

  # Query required data
  services = Service.query.all()
  professional_profiles = ProfessionalProfile.query.all()
  service_requests = ServiceRequest.query.all()
  customers = User.query.filter(User.role == 'customer').all()

  # Map user and service details for professional profiles
  for profile in professional_profiles:
    user = User.query.filter_by(id=profile.user_id).first()
    service = Service.query.filter_by(id=profile.service_type).first()
    user_dict[profile.user_id] = user
    service_type[profile.user_id] = service
    prof_dict[profile.user_id] = profile

  # Construct response data in JSON format, adding success message and category
  return jsonify(
    message="Admin dashboard data retrieved successfully.",
    category="success",
    services=[service.as_dict() for service in services],
    professional_profiles=[profile.as_dict() for profile in professional_profiles],
    service_requests=[service_request.as_dict() for service_request in service_requests],
    user_dict={key: user.as_dict() for key, user in user_dict.items()},
    service_type={key: service.as_dict() for key, service in service_type.items()},
    prof_dict={key: profile.as_dict() for key, profile in prof_dict.items()},
    customers=[customer.as_dict() for customer in customers]
  ), 200

@app.route('/admin/search', methods=['POST'])
@jwt_required()
def admin_search():
  """
    Admin Search
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              search_type:
                type: string
                enum: [customer, professional, service, service_request]
                example: customer
              search_text:
                type: string
                example: "John Doe"
    responses:
      200:
        description: Successfully retrieved search results
        content:
          application/json:
            schema:
              type: object
              properties:
                category:
                  type: string
                  example: "success"
                message:
                  type: string
                  example: "Search completed successfully"
                data:
                  type: object
      401:
        description: Admin access required
      404:
        description: No results found
    """
  # Verify if the user is an admin
  claims = get_jwt()
  if claims['role'] != 'admin':
      return jsonify({"category": "danger", "message": "Admin access required for this search"}), 401 

  data = request.get_json()
  search_type = data.get('search_type')
  search_term = data.get('search_text', '').strip()

  customers, professionals, services, service_requests = [], [], [], []
  service_type = {}
  prof_dict = {}
  service_dict = {}
  cust_dict = {}

  # Prepare dictionary of services for professional profiles
  for profile in ProfessionalProfile.query.all():
      service_type[profile.user_id] = Service.query.filter_by(id=profile.service_type).first()
      prof_dict[profile.user_id] = profile

  # Perform the search based on the search_type
  if search_type == 'customer':
      for service in Service.query.all():
          service_dict[service.id] = service
      for cust in CustomerProfile.query.all():
          cust_dict[cust.user_id] = cust
      service_requests = (
          ServiceRequest.query
          .join(CustomerProfile, ServiceRequest.customer_id == CustomerProfile.user_id)
          .filter(
              or_(
                  CustomerProfile.full_name.ilike(f"%{search_term}%"),
                  CustomerProfile.address.ilike(f"%{search_term}%"),
                  CustomerProfile.pin_code.ilike(f"%{search_term}%")
              )
          )
          .all()
      )
      customers = service_requests

  elif search_type == 'professional':
      professionals = ProfessionalProfile.query.filter(
          or_(
              ProfessionalProfile.full_name.ilike(f"%{search_term}%"),
              ProfessionalProfile.address.ilike(f"%{search_term}%")
          )
      ).all()

  elif search_type == 'service':
      services = Service.query.filter(
          or_(
              Service.name.ilike(f"%{search_term}%"),
              Service.description.ilike(f"%{search_term}%"),
              Service.service_type.ilike(f"%{search_term}%")
          )
      ).all()

  elif search_type == 'service_request':
      service_requests = ServiceRequest.query.filter(
          or_(
              ServiceRequest.service_status.ilike(f"%{search_term}%"),
              ServiceRequest.remarks.ilike(f"%{search_term}%")
          )
      ).all()

  # Check if results were found
  if not (customers or professionals or services or service_requests):
      return jsonify({"category": "info", "message": "No results found for your search"}), 404

  # Return the search results as JSON
  return jsonify({
      "category": "success",
      "message": "Search completed successfully",
      "data": {
          "customers": [customer.as_dict() for customer in customers],
          "professionals": [professional.as_dict() for professional in professionals],
          "services": [service.as_dict() for service in services],
          "service_requests": [request.as_dict() for request in service_requests],
          "service_type": {key: service.as_dict() for key, service in service_type.items()},
          "prof_dict": {key: prof.as_dict() for key, prof in prof_dict.items()},
          "cust_dict": {key: cust.as_dict() for key, cust in cust_dict.items()},
          "service_dict": {key: service.as_dict() for key, service in service_dict.items()},
      }
  }), 200

@app.route('/admin/manage_user/<int:user_id>/<string:field>/<string:value>', methods=['POST'])
@jwt_required()
def manage_user(user_id, field, value):
  """
    Manage User (Approve/Block)
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    parameters:
      - name: user_id
        in: path
        required: true
        description: ID of the user to be managed
        schema:
          type: integer
          example: 1
      - name: field
        in: path
        required: true
        description: Field to be updated ('approve' or 'blocked')
        schema:
          type: string
          enum: ['approve', 'blocked']
          example: approve
      - name: value
        in: path
        required: true
        description: New value for the field ('true' or 'false')
        schema:
          type: string
          enum: ['true', 'false']
          example: false
    responses:
      200:
        description: User status updated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Professional/Customer approved successfully"
                category:
                  type: string
                  example: "success"
      400:
        description: Invalid field or value
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Invalid field specified."
                category:
                  type: string
                  example: "danger"
      401:
        description: Unauthorized access
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Unauthorized access. Admins only."
                category:
                  type: string
                  example: "danger"
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User not found."
                category:
                  type: string
                  example: "danger"
    """
  # Check if the user has admin privileges
  claims = get_jwt()
  if claims['role'] != 'admin':
      return jsonify({"message": "Unauthorized access. Admins only.", "category": "danger"}), 401

  # Query for the user by ID
  user = User.query.filter_by(id=user_id).first()
  if not user:
      return jsonify({"message": "User not found.", "category": "danger"}), 404

  # Approve/Reject and Block/Unblock functionality
  if field == 'approve':
      if value.lower() == 'false':
          user.approve = True
          message = 'Professional/Customer approved successfully'
          category = 'success'
      elif value.lower() == 'true':
          user.approve = False
          message = 'Professional/Customer rejected successfully'
          category = 'danger'
      else:
          return jsonify({"message": "Invalid value for 'approve'.", "category": "danger"}), 400

  elif field == 'blocked':
      if value.lower() == 'false':
          user.blocked = True
          message = 'User blocked successfully'
          category = 'danger'
      elif value.lower() == 'true':
          user.blocked = False
          message = 'User unblocked successfully'
          category = 'success'
      else:
          return jsonify({"message": "Invalid value for 'blocked'.", "category": "danger"}), 400
  else:
      return jsonify({"message": "Invalid field specified.", "category": "danger"}), 400

  # Save changes to the database
  db.session.commit()

  return jsonify({"message": message, "category": category}), 200

# Manage Services Route (CRUD operations)
@app.route('/admin/services/get/<int:service_id>', methods=['GET'])
@jwt_required()
def get_services(service_id):
  """
    Get Service by ID
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    parameters:
      - name: service_id
        in: path
        required: true
        description: ID of the service to fetch
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: Service details
        content:
          application/json:
            schema:
              type: object
              properties:
                id:
                  type: integer
                service_type:
                  type: string
                name:
                  type: string
                description:
                  type: string
                price:
                  type: number
      401:
        description: Unauthorized access
      404:
        description: Service not found
    """
  claims = get_jwt()
  if claims['role'] != 'admin':
    return jsonify({"category": "danger", "message": "Please login as admin to update service"}), 401 
  # Fetch the service to be updated
  service = Service.query.get_or_404(service_id)
  service_data = {
        "id": service.id,
        "service_type": service.service_type,
        "name": service.name,
        "description": service.description,
        "price": service.price
    }
  return jsonify(service_data), 200

@app.route('/admin/services/create_services', methods=['POST'])
@jwt_required()
def create_services():
  """
    Create a new service by an admin.
    This endpoint allows an admin to create a new service with details like name, type, price, and description.
    ---
    tags:
      - Admin
    parameters:
      - name: service
        in: body
        description: Service details to be created
        required: true
        schema:
          type: object
          properties:
            service_type:
              type: string
              description: The type of service (e.g., 'plumbing', 'cleaning')
              example: 'plumbing'
            name:
              type: string
              description: The name of the service
              example: 'Water Leak Repair'
            price:
              type: number
              description: The price of the service
              example: 100.50
            description:
              type: string
              description: A brief description of the service
              example: 'Fixes water leaks in pipes and faucets.'
    responses:
      200:
        description: Service created successfully.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "success"
            message:
              type: string
              example: "Service created successfully"
      400:
        description: Missing required field or invalid input data.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "'name' is a required field"
      401:
        description: Unauthorized access (not an admin).
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "Please login as admin to create service"
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "An error occurred while creating the service"
    """
  claims = get_jwt()
  
  if claims['role'] != 'admin':
    return jsonify({"category": "danger","message": "Please login as admin to create service"}), 401 
  data = request.get_json()
  

  if not data:
    return jsonify({"category": "danger", "message": "Invalid input data"}), 401
  
  required_fields = ["service_type", "name", "price", "description"]
  for field in required_fields:
    if field not in data:
      return jsonify({"category": "danger", "message": f"'{field}' is a required field"}), 400
  try:
    new_service = Service(
    service_type=data['service_type'],
      name=data['name'],
      price=data['price'],
      description=data['description']
    )
    db.session.add(new_service)
    db.session.commit()
    return jsonify({"category": "success", "message": "Service created successfully"}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({"category": "danger", "message": "An error occurred while creating the service"}), 500
    
# Update Services Route (REST API for updating a service)
@app.route('/admin/services/update/<int:service_id>', methods=['PUT'])
@jwt_required()
def update_service(service_id):
  """
    Update an existing service by an admin.
    This endpoint allows an admin to update an existing service with details like name, type, price, and description.
    ---
    tags:
      - Admin
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: The ID of the service to be updated.
        example: 1
      - name: service
        in: body
        description: Service details to be updated
        required: true
        schema:
          type: object
          properties:
            service_type:
              type: string
              description: The type of service (e.g., 'plumbing', 'cleaning')
              example: 'plumbing'
            name:
              type: string
              description: The name of the service
              example: 'Water Leak Repair'
            price:
              type: number
              description: The price of the service
              example: 100.50
            description:
              type: string
              description: A brief description of the service
              example: 'Fixes water leaks in pipes and faucets.'
    responses:
      200:
        description: Service updated successfully.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "success"
            message:
              type: string
              example: "Service updated successfully"
      400:
        description: Missing required field or invalid input data.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "Invalid input data"
      401:
        description: Unauthorized access (not an admin).
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "Please login as admin to update service"
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            category:
              type: string
              example: "danger"
            message:
              type: string
              example: "An error occurred while updating the service"
    """
  claims = get_jwt()
  if claims['role'] != 'admin':
    return jsonify({"category": "danger", "message": "Please login as admin to update service"}), 401 

  # Fetch the service to be updated
  service = Service.query.get_or_404(service_id)

  # Extract JSON data from the request
  data = request.get_json()
  if not data:
    return jsonify({"category": "danger", "message": "Invalid input data"}), 400

  # Update the service attributes if present in the JSON data
  try:
    service.service_type = data.get('service_type', service.service_type)
    service.name = data.get('name', service.name)
    service.price = data.get('price', service.price)
    service.description = data.get('description', service.description)

    db.session.commit()
    return jsonify({"category": "success", "message": "Service updated successfully"}), 200
  except Exception as e:
    db.session.rollback()
    return jsonify({"category": "danger", "message": "An error occurred while updating the service"}), 500

# Delete Service Route 
@app.route('/admin/services/delete/<int:service_id>', methods=['DELETE'])
@jwt_required()
def delete_service(service_id):
    """
    Delete Service by ID
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    parameters:
      - name: service_id
        in: path
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Service deleted successfully
      404:
        description: Service not found
    """
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({"category": "danger", "message": "Please login as admin to delete service"}), 401 

    # Fetch the service to delete
    service_to_delete = Service.query.get(service_id)
    if not service_to_delete:
        return jsonify({"category": "danger", "message": "Service not found"}), 404

    try:
        db.session.delete(service_to_delete)
        db.session.commit()
        return jsonify({"category": "success", "message": "Service deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"category": "danger", "message": "An error occurred while deleting the service"}), 500

@app.route('/customer/profile', methods=['GET', 'POST'])
@jwt_required()
def customer_profile():
  """
    Manage Customer Profile
    ---
    tags:
      - Customer
    security:
      - BearerAuth: []
    responses:
      200:
        description: Profile retrieved or updated successfully
      400:
        description: Validation errors or missing fields
      401:
        description: Unauthorized access for non-customer users
    """
  # Get user_id from JWT
  claims = get_jwt()
  if claims['role'] != 'customer':
    return jsonify({"message": "Not a Customer!", "category": "danger"}), 401
  user_id = claims['user_id']

  # Fetch the customer profile if it exists
  customer = CustomerProfile.query.filter_by(user_id=user_id).first()

  if request.method == 'GET':
    # Respond with customer profile data if available, otherwise send empty profile
    profile_data = {
      "user_id": user_id,
      "username": User.query.get(user_id).username,
      "full_name": customer.full_name if customer else "",
      "address": customer.address if customer else "",
      "pin_code": customer.pin_code if customer else ""
    }
    return jsonify(profile_data), 200
  elif request.method == 'POST':
    data = request.json
    # Validate required fields
    if not data.get("full_name") or not data.get("address") or not data.get("pin_code"):
      return jsonify({"message":"Missing required fields: full_name, address, or pin_code.","category":"danger"}), 400
    # Update existing customer profile or create a new one
    if customer:
      customer.full_name = data["full_name"]
      customer.address = data["address"]
      customer.pin_code = data["pin_code"]
    else:
      new_customer_profile = CustomerProfile(
          user_id=user_id,
          full_name=data["full_name"],
          address=data["address"],
          pin_code=data["pin_code"]
      )
      db.session.add(new_customer_profile)
    db.session.commit()
    return jsonify({"message": "Customer Profile updated successfully!","category":"success"}), 200

# Customer Dashboard
@app.route('/customer/dashboard', methods=['GET', 'POST'])
@jwt_required()
def customer_dashboard():
  """
    Customer Dashboard
    ---
    tags:
      - Customer
    security:
      - BearerAuth: []
    responses:
      200:
        description: Dashboard data retrieved successfully
      401:
        description: Unauthorized access for non-customer users
    """
  # Get user_id from JWT
  claims = get_jwt()
  if claims['role'] != 'customer':
    return jsonify({"message": "Not a Customer!", "category": "danger"}), 401
  user_id = claims['user_id']

  if request.args.get("service_type"):
      services = Service.query.filter_by(service_type=request.args.get("service_type")).all()
  else:
      services = []
  service_requests = ServiceRequest.query.filter_by(customer_id=user_id).all()
  professional_profile = ProfessionalProfile.query.all()
  service_dict = {}
  prof_dict = {} 
  for professional in professional_profile:
      prof_dict[professional.user_id] = professional.as_dict()
  for service in Service.query.all():
      service_dict[service.id] = service.as_dict()
  return jsonify({"services":[service.as_dict() for service in services], "service_requests":[request.as_dict() for request in service_requests],"prof_dict":prof_dict,"service_dict":service_dict}),200
  
@app.route('/customer/search', methods=['GET', 'POST'])
@jwt_required()
def customer_search():
  """
    Customer search for professional services.
    This endpoint allows the customer to search for professionals or services by providing search parameters.
    ---
    tags:
      - Customer
    parameters:
      - name: search_type
        in: json
        type: string
        required: true
        description: Type of search ('professional')
      - name: search_text
        in: json
        type: string
        required: true
        description: The search term (e.g. name, address, pin code)
    responses:
      200:
        description: Search results
        schema:
          type: object
          properties:
            category:
              type: string
            message:
              type: string
            data:
              type: object
              properties:
                service_professional:
                  type: array
                  items:
                    type: object
                    properties:
                      pin_code:
                        type: string
                      address:
                        type: string
                      service_name:
                        type: string
                      service_description:
                        type: string
                      service_price:
                        type: string
      400:
        description: Missing or invalid parameters
      401:
        description: Unauthorized access
    """
  claims = get_jwt()
  if claims['role'] != 'customer':
    return jsonify({"message": "Not a Customer!", "category": "danger"}), 401
  data = request.json
  service_professional = []
  search_type = data.get('search_type')
  search_term = data.get('search_text').strip()
  service_professional= ProfessionalProfile.query.select_from(ProfessionalProfile).join(Service, ProfessionalProfile.service_type == Service.id).filter(
  or_(
      ProfessionalProfile.address.ilike(f"%{search_term}%"),  # Search by address
      ProfessionalProfile.pin_code.ilike(f"%{search_term}%"),  # Search by pin code
      Service.name.ilike(f"%{search_term}%")  # Search by service name
      )).with_entities(
                        ProfessionalProfile.pin_code,  # Professional's name
                        ProfessionalProfile.address,  # Professional's address
                        Service.name,  # Service name
                        Service.description, # Service description
                        Service.price  # Service base price
                      ).all()
  if not service_professional:
    return jsonify({"message":"No results found for your search.","category":"danger"}),400
  return jsonify({
      "category": "success",
      "message": "Search completed successfully",
      "data": {
        "service_professional": [
          {
              "pin_code": row[0],
              "address": row[1],
              "service_name": row[2],
              "service_description": row[3],
              "service_price": row[4]
          }
          for row in service_professional
        ]          
      }
  }), 200

@app.route('/customer/create_service_request/<int:service_id>', methods=['GET','POST'])
@jwt_required()
def create_service_request(service_id):
  """
    Create a service request for a customer.
    This endpoint allows the customer to request a service offered by a professional.
    ---
    tags:
      - Customer
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: The ID of the service to request
    responses:
      200:
        description: Service request created successfully
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      401:
        description: Unauthorized or validation errors
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      404:
        description: No professional available for the service
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  # Get claims from JWT
  claims = get_jwt()
  # Ensure the user is a customer
  if claims['role'] != 'customer':
      return jsonify({"message": "Not a Customer!", "category": "danger"}), 401
  customer_id = claims['user_id']
  # Find the professional offering the requested service
  professional = ProfessionalProfile.query.filter_by(service_type=service_id).first()
  if not professional:
      return jsonify({"message": "No professional offering this service yet! Please choose another service.","category": "danger"}), 401
  user = User.query.filter_by(id=professional.user_id).first()
  if not user.approve:
      return jsonify({"message": "Professional offering this service is still not approved! Please choose another service.","category": "danger"}), 401
  if user.blocked:
      return jsonify({"message": "Professional offering this service is blocked! Please choose another service.","category": "danger"}), 401
  
  professional_service_request = ServiceRequest.query.filter_by(professional_id=professional.user_id, service_id=service_id).order_by(desc(ServiceRequest.date_of_request)).first()
  if professional_service_request and (professional_service_request.service_status == 'requested' or professional_service_request.service_status == 'accepted'):
      return jsonify({"message": "Service request already exists! Please wait for the professional to respond or choose another service.", "category": "danger"}),401
  
  service_request = ServiceRequest(service_id=service_id, customer_id=customer_id, professional_id= professional.user_id, service_status='requested')
  
  db.session.add(service_request)
  db.session.commit()
  return jsonify({"message": "Service request created successfully!", "category": "success"}), 200

@app.route('/customer/close_service_request/<int:request_id>', methods=['GET','PUT'])
@jwt_required()
def close_service_request(request_id):
  """
    Close a service request for a customer after the service has been completed.
    The customer can either view the request details (GET) or mark it as completed (PUT).
    ---
    tags:
      - Customer
    parameters:
      - name: request_id
        in: path
        type: integer
        required: true
        description: The ID of the service request to close
    responses:
      200:
        description: Successfully closed the service request or fetched service request details
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
            request_id:
              type: integer
            service_name:
              type: string
            service_description:
              type: string
            full_name:
              type: string
      401:
        description: Unauthorized access (not a customer or other validation errors)
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      404:
        description: Service request not found
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      400:
        description: Invalid request (missing or invalid input)
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  # Get claims from JWT
  claims = get_jwt()
  # Ensure the user is a customer
  if claims['role'] != 'customer':
      return jsonify({"message": "Not a Customer!", "category": "danger"}), 401
  service_request = ServiceRequest.query.get_or_404(request_id)
  professional = ProfessionalProfile.query.filter_by(user_id=service_request.professional_id).first()
  service = Service.query.filter_by(id=service_request.service_id).first()
  if request.method == 'GET':
    return jsonify({
        "request_id": service_request.id,
        "service_name": service.name,
        "service_description": service.description,
        "full_name": professional.full_name
    }), 200   
  elif request.method == 'PUT':
    data = request.json
    service_request.service_status = 'completed'
    service_request.date_of_completion = db.func.current_timestamp()
    service_request.remarks = data.get('remarks')
    professional.reviews = (float(data.get('rating'))+ professional.reviews)/2
    db.session.commit()
    return jsonify({"message": "Service request closed successfully!", "category": "success"}), 200
    
@app.route('/professional/profile', methods=['GET', 'POST'])
@jwt_required()
def professional_profile():
  """
    Get or update the professional profile of a user.
    ---
    tags:
      - Professional
    responses:
      200:
        description: Successfully retrieved or updated the professional profile.
        schema:
          type: object
          properties:
            profile:
              type: object
              properties:
                user_id:
                  type: integer
                username:
                  type: string
                full_name:
                  type: string
                service_type:
                  type: string
                experience:
                  type: string
                address:
                  type: string
                pin_code:
                  type: string
                filename:
                  type: string
                reviews:
                  type: number
            services:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
      400:
        description: Missing required fields or invalid file format.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      401:
        description: Unauthorized access (not a professional).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  # Get user_id from JWT
  claims = get_jwt()
  if claims['role'] != 'professional':
    return jsonify({"message": "Not a Professional!", "category": "danger"}), 401
  user_id = claims['user_id']

  # Fetch the professional profile if it exists
  professional = ProfessionalProfile.query.filter_by(user_id=user_id).first()
  services = Service.query.all()
  service_list = [{"id": service.id, "name": service.name} for service in services]
  if request.method == 'GET':
    # Respond with professional profile data if available, otherwise send empty profile
    profile_data = {
        "user_id": user_id,
        "username": User.query.get(user_id).username,
        "full_name": professional.full_name if professional else "",
        "service_type": Service.query.filter(Service.id == professional.service_type).first().name if professional else "",
        "experience": professional.experience if professional else "",
        "address": professional.address if professional else "",
        "pin_code": professional.pin_code if professional else "",
        "filename": professional.filename if professional else "",
        "reviews": professional.reviews if professional else 0
    }
    return jsonify({"profile": profile_data, "services": service_list}), 200

  elif request.method == 'POST':
    data = request.form
    # Validate required fields
    required_fields = ["full_name", "service_type", "experience", "address", "pin_code"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return jsonify({
            "message": f"Missing required fields: {', '.join(missing_fields)}.",
            "category": "danger"
        }), 400

    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            return jsonify({
                "message": "Invalid file format! Please upload only images and PDFs.",
                "category": "danger"
            }), 400
    else:
        filename = professional.filename if professional else None

    # Update existing professional profile or create a new one
    if professional:
        professional.full_name = data["full_name"]
        professional.service_type = data["service_type"]
        professional.experience = data["experience"]
        professional.address = data["address"]
        professional.pin_code = data["pin_code"]
        professional.filename = filename  # Update file name if uploaded
    else:
        new_professional_profile = ProfessionalProfile(
            user_id=user_id,
            full_name=data["full_name"],
            service_type=data["service_type"],
            experience=data["experience"],
            address=data["address"],
            pin_code=data["pin_code"],
            filename=filename  # Save file name if uploaded
        )
        db.session.add(new_professional_profile)

    db.session.commit()

    return jsonify({"message": "Professional Profile updated successfully!", "category": "success"}), 200


@app.route('/professional/dashboard', methods=['GET','POST'])
@jwt_required()  
def professional_dashboard():
  """
    Retrieve the professional's dashboard data, including service requests and services.
    ---
    tags:
      - Professional
    responses:
      200:
        description: Successfully retrieved the professional dashboard data.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
            services:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  description:
                    type: string
                  price:
                    type: number
            service_requests:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  service_id:
                    type: integer
                  customer_id:
                    type: integer
                  service_status:
                    type: string
                  date_of_request:
                    type: string
                  remarks:
                    type: string
            service_requests_closed:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  service_id:
                    type: integer
                  customer_id:
                    type: integer
                  service_status:
                    type: string
                  date_of_request:
                    type: string
                  remarks:
                    type: string
            cust_dict:
              type: object
              additionalProperties:
                type: object
                properties:
                  user_id:
                    type: integer
                  full_name:
                    type: string
                  address:
                    type: string
                  pin_code:
                    type: string
            service_dict:
              type: object
              additionalProperties:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  description:
                    type: string
                  price:
                    type: number
      401:
        description: Unauthorized access (not a professional).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  claims = get_jwt()
  if claims['role'] == 'professional':
    professional_id = claims['user_id']
    service_requests = ServiceRequest.query.filter_by(professional_id=professional_id,service_status='requested').all()
    service_requests_closed = ServiceRequest.query.filter(ServiceRequest.professional_id==professional_id,ServiceRequest.service_status != 'requested').all()
    serviceIdList = []    
    for request in service_requests:
      serviceIdList.append(request.service_id)
    services = Service.query.filter(Service.id.in_(serviceIdList)).all()
    cust_dict = {}
    service_dict = {}
    for service in Service.query.all():
      service_dict[service.id] = service
    for cust in CustomerProfile.query.all():
      cust_dict[cust.user_id] = cust
    return jsonify(
      message="Admin dashboard data retrieved successfully.",
      category="success",
      services=[service.as_dict() for service in services],
      service_requests=[service_request.as_dict() for service_request in service_requests],  
      cust_dict={key: cust.as_dict() for key, cust in cust_dict.items()},
      service_dict={key: service.as_dict() for key, service in service_dict.items()},
      service_requests_closed=[service_requests_closed.as_dict() for service_requests_closed in service_requests_closed]
    )
  return jsonify({"message": "Not a Professional!", "category": "danger"}), 401

@app.route('/professional/search',methods=['GET', 'POST'])
@jwt_required()
def professional_search():
  """
    Search for service requests based on various criteria (date, location, pin code).
    ---
    tags:
      - Professional
    parameters:
      - name: search_type
        in: body
        type: string
        required: true
        enum: [date, location, pin]
        description: The type of search (date, location, or pin code).
      - name: search_text
        in: body
        type: string
        required: true
        description: The search term to filter the requests (date, location, or pin).
    responses:
      200:
        description: Successfully retrieved the search results.
        schema:
          type: object
          properties:
            category:
              type: string
            message:
              type: string
            data:
              type: object
              properties:
                service_requests:
                  type: array
                  items:
                    type: object
                    properties:
                      customer_name:
                        type: string
                      service_name:
                        type: string
                      service_description:
                        type: string
                      service_price:
                        type: number
                      status:
                        type: string
                      start_date:
                        type: string
                      remarks:
                        type: string
      401:
        description: Unauthorized access (not a professional).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      400:
        description: No results found for the search term.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  claims = get_jwt()
  if claims['role'] != 'professional':
    return jsonify({"message": "Not a Professional!", "category": "danger"}), 401

  professional_id = claims['user_id']
  service_requests = []
  cust_dict = {}
  service_dict = {}
  data = request.json
  search_type = data.get('search_type')
  search_term = data.get('search_text').strip()
  for service in Service.query.all():
    service_dict[service.id] = service
  for cust in CustomerProfile.query.all():
    cust_dict[cust.user_id] = cust        
      
  if search_type == 'date':
    service_requests = ServiceRequest.query.filter(ServiceRequest.date_of_request.ilike(f"%{search_term}%"), ServiceRequest.professional_id == professional_id).all()
  elif search_type == 'location':
    service_requests = ServiceRequest.query.select_from(ServiceRequest).join(CustomerProfile, ServiceRequest.customer_id == CustomerProfile.user_id).filter(CustomerProfile.address.ilike(f"%{search_term}%"),ServiceRequest.professional_id == professional_id).all()    
  elif search_type == 'pin':
    service_requests = ServiceRequest.query.select_from(ServiceRequest).join(CustomerProfile, ServiceRequest.customer_id == CustomerProfile.user_id).filter(CustomerProfile.pin_code.ilike(f"%{search_term}%"),ServiceRequest.professional_id == professional_id).all()
  if not (service_requests):
    return jsonify({"message":"No results found for your search.", "category": "danger"}),400
  # Build the response data
  response_data = []
  for req in service_requests:
    customer = cust_dict.get(req.customer_id)
    service = service_dict.get(req.service_id)
    response_data.append({
        "customer_name": customer.full_name if customer else "Unknown",
        "service_name": service.name if service else "Unknown",
        "service_description": service.description if service else "Unknown",
        "service_price": service.price if service else "N/A",
        "status": req.service_status,
        "start_date": req.date_of_request.strftime('%Y-%m-%d') if req.date_of_request else "N/A",
        "remarks": req.remarks if req.remarks else "No remarks"
    })
  return jsonify({
      "category": "success",
      "message": "Search completed successfully",
      "data": {
          "service_requests": response_data
      }
  }), 200

@app.route('/professional/update_request_status/<string:status>/<int:request_id>',methods=['PUT'])
@jwt_required()
def update_request_status(status,request_id):
  """
    Update the status of a service request.
    Allows professionals to either accept or reject a service request.
    ---
    tags:
      - Professional
    parameters:
      - name: status
        in: path
        type: string
        required: true
        enum: [accept, reject]
        description: The new status of the service request.
      - name: request_id
        in: path
        type: integer
        required: true
        description: The ID of the service request to be updated.
    responses:
      200:
        description: Successfully updated the service request status.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      401:
        description: Unauthorized access (not a professional).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      404:
        description: Service request not found.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  claims = get_jwt()
  if claims['role'] != 'professional':
    return jsonify({"message": "Not a Professional!", "category": "danger"}), 401
  service_request = ServiceRequest.query.get_or_404(request_id)
  if status == 'accept':
    service_request.service_status = 'accepted'
    service_request.date_of_accept_reject = db.func.current_timestamp()
  elif status == 'reject':
    service_request.service_status = 'rejected'
    service_request.date_of_accept_reject = db.func.current_timestamp()
  db.session.commit()
  return jsonify({'message':'Service request updated successfully!','category':'success'}),200

# Define an API endpoint to return the reviews data
@app.route('/admin/summary/reviews', methods=['GET'])
@jwt_required()
@cache.cached()
def get_reviews():
  """
    Retrieve the summary of reviews for all professionals.
    This endpoint returns the list of professionals with their reviews.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Successfully retrieved reviews data.
        schema:
          type: array
          items:
            type: object
            properties:
              full_name:
                type: string
                description: The full name of the professional.
              reviews:
                type: number
                description: The average reviews score for the professional.
      401:
        description: Unauthorized access (not an admin).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  claims = get_jwt()
  if claims['role'] != 'admin':
    return jsonify({"message": "Not an Admin!", "category": "danger"}), 401
  professionals = ProfessionalProfile.query.with_entities(ProfessionalProfile.full_name,ProfessionalProfile.reviews).all()
  reviews_data = [{"full_name": p.full_name, "reviews": p.reviews} for p in professionals]
  return jsonify(reviews_data)

@app.route('/admin/summary/service_requests', methods=['GET'])
@jwt_required()
@cache.cached()
def get_service_requests():
  """
    Retrieve the count of service requests grouped by completion date.
    This endpoint returns a summary of service requests, including the number of requests completed on each date.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Successfully retrieved service request summary.
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                description: The date of completion for service requests.
                example: "2024-12-01"
              count:
                type: integer
                description: The number of service requests completed on that date.
                example: 15
      401:
        description: Unauthorized access (not an admin).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  claims = get_jwt()
  if claims['role'] != 'admin':
    return jsonify({"message": "Not an Admin!", "category": "danger"}), 401
  service_requests = (db.session.query(func.date(ServiceRequest.date_of_completion), func.count(ServiceRequest.id)).filter(ServiceRequest.date_of_completion!=None).group_by(func.date(ServiceRequest.date_of_completion)).all())
  datewise_requests =[{"date": str(sr[0]), "count": sr[1]} for sr in service_requests]   
  return jsonify(datewise_requests)

@app.route('/customer/summary/service_requests/<int:customer_id>', methods=['GET'])
@jwt_required()
@cache.memoize()
def get_service_requests_customer(customer_id):
  """
    Retrieve the count of service requests for a specific customer, grouped by completion date.
    This endpoint returns a summary of service requests completed for the given customer, including the number of requests completed on each date.
    ---
    tags:
      - Customer
    parameters:
      - name: customer_id
        in: path
        type: integer
        required: true
        description: The ID of the customer whose service request summary is being retrieved.
        example: 1
    responses:
      200:
        description: Successfully retrieved service request summary for the customer.
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                description: The date of completion for service requests.
                example: "2024-12-01"
              count:
                type: integer
                description: The number of service requests completed for the customer on that date.
                example: 5
      401:
        description: Unauthorized access (not a customer or trying to access another customer's data).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  claims = get_jwt()
  if claims['role'] != 'customer':
    return jsonify({"message": "Not a Customer!", "category": "danger"}), 401
  if claims['user_id'] != customer_id:
    return jsonify({"message": "Unauthorized access. Access to own data only.", "category": "danger"}), 401
  service_requests_customer = (db.session.query(func.date(ServiceRequest.date_of_completion), func.count(ServiceRequest.id)).filter(ServiceRequest.date_of_completion!=None,ServiceRequest.customer_id==customer_id).group_by(func.date(ServiceRequest.date_of_completion)).all())
  datewise_requests =[{"date": str(sr[0]), "count": sr[1]} for sr in service_requests_customer]   
  return jsonify(datewise_requests)

@app.route('/professional/summary/reviews/<int:professional_id>', methods=['GET'])
@jwt_required()
@cache.memoize()
def get_reviews_professional(professional_id):
  """
    Retrieve the count of service requests for a specific customer, grouped by completion date.
    This endpoint returns a summary of service requests completed for the given customer, including the number of requests completed on each date.
    ---
    tags:
      - Professional
    parameters:
      - name: customer_id
        in: path
        type: integer
        required: true
        description: The ID of the customer whose service request summary is being retrieved.
        example: 1
    responses:
      200:
        description: Successfully retrieved service request summary for the customer.
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                description: The date of completion for service requests.
                example: "2024-12-01"
              count:
                type: integer
                description: The number of service requests completed for the customer on that date.
                example: 5
      401:
        description: Unauthorized access (not a customer or trying to access another customer's data).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  claims = get_jwt()
  if claims['role'] != 'professional':
    return jsonify({"message": "Not a Professional!", "category": "danger"}), 401
  if claims['user_id'] != professional_id:
    return jsonify({"message": "Unauthorized access. Access to own data only.", "category": "danger"}), 401
  professionals = ProfessionalProfile.query.with_entities(ProfessionalProfile.full_name,ProfessionalProfile.reviews).filter(ProfessionalProfile.user_id==professional_id).all()
  reviews_data = [{"full_name": p.full_name, "reviews": p.reviews} for p in professionals]
  return jsonify(reviews_data)

@app.route('/professional/summary/service_requests/<int:professional_id>', methods=['GET'])
@jwt_required()
@cache.memoize()
def get_service_requests_professional(professional_id):
  """
    Retrieve the count of service requests for a specific professional, grouped by completion date.
    This endpoint returns a summary of service requests completed for the given professional, including the number of requests completed on each date.
    ---
    tags:
      - Professional
    parameters:
      - name: professional_id
        in: path
        type: integer
        required: true
        description: The ID of the professional whose service request summary is being retrieved.
        example: 1
    responses:
      200:
        description: Successfully retrieved service request summary for the professional.
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                description: The date of completion for service requests.
                example: "2024-12-01"
              count:
                type: integer
                description: The number of service requests completed for the professional on that date.
                example: 5
      401:
        description: Unauthorized access (not a professional or trying to access another professional's data).
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            message:
              type: string
            category:
              type: string
    """
  claims = get_jwt()
  if claims['role'] != 'professional':
    return jsonify({"message": "Not a Professional!", "category": "danger"}), 401
  if claims['user_id'] != professional_id:
    return jsonify({"message": "Unauthorized access. Access to own data only.", "category": "danger"}), 401
    
  service_requests = (db.session.query(func.date(ServiceRequest.date_of_completion), func.count(ServiceRequest.id)).join(ProfessionalProfile,ServiceRequest.professional_id==ProfessionalProfile.user_id).filter(ServiceRequest.date_of_completion!=None,ProfessionalProfile.user_id==professional_id).group_by(func.date(ServiceRequest.date_of_completion)).all())
  datewise_requests =[{"date": str(sr[0]), "count": sr[1]} for sr in service_requests]   
  return jsonify(datewise_requests)

if __name__ == '__main__':
    app.run(debug=True)