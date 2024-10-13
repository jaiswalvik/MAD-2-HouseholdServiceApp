import os
from flask import Flask, jsonify, render_template, redirect, url_for, request, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func, or_
from flask_jwt_extended import JWTManager, create_access_token, jwt_required , get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CustomerProfileForm, CustomerSearchForm, ProfessionalProfileForm, ProfessionalSearchForm, RegisterForm, SearchForm, ServiceForm, ServiceRemarksForm
from models import CustomerProfile, db , User, Service, ProfessionalProfile, ServiceRequest
from werkzeug.utils import secure_filename   
from flask_cors import CORS 
from flasgger import Swagger

app = Flask(__name__)

# Configure file upload settings
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to save files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}  # Allowed file extensions

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
@app.route('/download/<string:filename>')
def download_file(filename):
    """
    Download a file from the server.
    ---
    tags:
      - Files
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: The name of the file to download.
    responses:
      200:
        description: File downloaded successfully.
      404:
        description: File not found.
    """
    # Set the directory where your files are located
    file_directory = os.path.join(app.root_path, 'uploads')
    
    # Serve the file from the directory as an attachment
    return send_from_directory(file_directory, filename, as_attachment=True)

# Home Route
@app.route('/')
def index():
    """
    Home page endpoint.
    ---
    tags:
      - Home
    responses:
      200:
        description: Successfully rendered the home page.
    """
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration endpoint.
    ---
    tags:
      - User
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: "john_doe"
            password:
              type: string
              example: "secure_password"
            role:
              type: string
              enum: ["customer", "professional"]
              example: "customer"
    responses:
      200:
        description: Registration successful, redirecting to login.
      400:
        description: Username already exists.
    """
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password, role=form.role.data, approve=False, blocked=True)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.
    ---
    tags:
      - User
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: "john_doe"
            password:
              type: string
              example: "secure_password"
    responses:
      200:
        description: Successfully logged in and redirected based on role.
      401:
        description: Invalid credentials.
    """
    if request.method == 'POST':
      username = request.json.get('username')
      password = request.json.get('password')
      user = User.query.filter(User.username==username).filter(User.role.in_(['customer','professional'])).first()
      if user and check_password_hash(user.password, password):
          if user.role == 'customer':
              #Check if customer profile is approved
              if not user.approve:
                return jsonify({"error": "Your account is not approved yet! Please wait for the admin to approve."}), 401
              # Check if customer profile is blocked
              if user.blocked:
                return jsonify({"error": "Your account is blocked! Please contact the admin."}), 401
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
                return jsonify({"error": "Your account is not approved yet! Please wait for the admin to approve."}), 401
              # Check if professional profile is blocked
              if user.blocked:
                return jsonify({"error": "Your account is blocked! Please contact the admin."}), 401
              additional_claims = {"user_id": user.id, "role": user.role, "redirect" : "professional_dashboard"}
              access_token = create_access_token(username, additional_claims=additional_claims)
              return jsonify(access_token=access_token)            
      return jsonify({"error": "Bad username or password"}), 401
    
# Logout route for admin
@app.route('/logout')
def logout():
    """
    User logout endpoint.
    ---
    tags:
      - User
    responses:
      200:
        description: Successfully logged out and redirected to the login page.
      401:
        description: User not logged in.
    """
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# Admin Login Route
@app.route('/admin/login', methods=['POST'])
def admin_login():
  if request.method == 'POST':
    username = request.json.get('username')
    password = request.json.get('password')
    user = User.query.filter_by(username=username, role='admin').first()
    if user and check_password_hash(user.password, password):
      additional_claims = {"admin_user_id": user.id, "role": user.role}
      access_token = create_access_token(username, additional_claims=additional_claims)
      return jsonify(access_token=access_token)
    return jsonify({"error": "Bad username or password"}), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
  claims = get_jwt()
  if claims['role'] == 'admin':
    return jsonify(admin_user_id=claims['admin_user_id'],role=claims['role']), 200
  else:
    return jsonify(user_id=claims['user_id'],role=claims['role'],redirect=claims['redirect']), 200
  
@app.route('/admin/profile', methods=['GET', 'POST'])
def admin_profile():
    """
    Render the admin profile page. No profile changes can be made.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Renders the admin profile page.
      401:
        description: Admin user is not authorized to access this page.
    """
    if not session.get('admin_user_id'):
        flash('Admin! Please log in..', 'danger')
        return redirect(url_for('admin_login'))
    else:
        user_id = session['admin_user_id']
        username = User.query.get(user_id).username
        flash("Admin! You can't make changes to your profile", 'danger')
    return render_template('admin_profile.html')

# Admin Dashboard
@app.route('/admin/dashboard', methods=['POST'])
@jwt_required()
def admin_dashboard():
  claims = get_jwt()
  if claims['role'] == 'admin':
    user_dict={}
    prof_dict ={}
    service_type={}
    services = Service.query.all()
    professional_profile = ProfessionalProfile.query.all()
    for profile in professional_profile:
      user_dict[profile.user_id] = User.query.filter_by(id=profile.user_id).first()
      service_type[profile.user_id] = Service.query.filter_by(id=profile.service_type).first()
      prof_dict[profile.user_id] = profile
    service_requests = ServiceRequest.query.all()
    users = User.query.filter(User.role=='customer').all()
    return jsonify(
      services=[service.as_dict() for service in services],
      professional_profile=[professional.as_dict() for professional in professional_profile],
      service_requests=[service_request.as_dict() for service_request in service_requests],
      user_dict= [user.as_dict() for user in user_dict.values()],
      service_type=[service.as_dict() for service in service_type.values()],
      prof_dict=[professional.as_dict() for professional in prof_dict.values()],
      customer=[user.as_dict() for user in users]
    ), 200 
  else:
    return jsonify({"error": "Bad username or password"}), 401

@app.route('/admin/search', methods=['GET', 'POST'])
def admin_search():
    """
    Search for customers, professionals, services, or service requests.
    ---
    tags:
      - Admin
    parameters:
      - name: search_type
        in: query
        required: true
        type: string
        enum: [customer, professional, service, service_request]
        description: Type of entity to search for.
      - name: search_text
        in: query
        required: true
        type: string
        description: Text to search for within the specified entity type.
    responses:
      200:
        description: Renders the admin search results page.
      401:
        description: Admin user is not authorized to access this page.
    """
    if not session.get('admin_user_id'):
        flash('Admin! Please log in..', 'danger')
        return redirect(url_for('admin_login'))
    else:
        form = SearchForm()
        customers, professionals, services, service_requests = [], [], [], []
        service_type={}
        prof_dict ={}
        service_dict = {}
        cust_dict = {}   
        for profile in ProfessionalProfile.query.all():
            service_type[profile.user_id] = Service.query.filter_by(id=profile.service_type).first()
            prof_dict[profile.user_id] = profile
            
        if form.validate_on_submit():
            search_type = form.search_type.data
            search_term = form.search_text.data.strip()
            
            # Perform the appropriate search based on the selection in the dropdown
            if search_type == 'customer':
                for service in Service.query.all():
                    service_dict[service.id] = service
                for cust in CustomerProfile.query.all():
                    cust_dict[cust.user_id] = cust
                service_requests = (ServiceRequest.query.select_from(ServiceRequest).join(CustomerProfile, ServiceRequest.customer_id == CustomerProfile.user_id).filter(or_(CustomerProfile.full_name.ilike(f"%{search_term}%"),CustomerProfile.address.ilike(f"%{search_term}%"),CustomerProfile.pin_code.ilike(f"%{search_term}%"))).all())
                customers = service_requests

            elif search_type == 'professional':
                professionals = ProfessionalProfile.query.filter(
                    (ProfessionalProfile.full_name.ilike(f"%{search_term}%")) |
                    (ProfessionalProfile.address.ilike(f"%{search_term}%")) 
                ).all()      
            elif search_type == 'service':
                services = Service.query.filter(
                    Service.name.ilike(f"%{search_term}%") |
                    Service.description.ilike(f"%{search_term}%") |
                    Service.service_type.ilike(f"%{search_term}%")
                ).all()
            elif search_type == 'service_request':
                service_requests = ServiceRequest.query.filter(
                    (ServiceRequest.service_status.ilike(f"%{search_term}%")) | 
                    (ServiceRequest.remarks.ilike(f"%{search_term}%"))
                ).all()
        
            if not (customers or professionals or services or service_requests):
                flash("No results found for your search.", "info")

        return render_template('admin_search.html', form=form, 
                customers=customers, professionals=professionals, 
                services=services, service_requests=service_requests,service_type=service_type,prof_dict=prof_dict,cust_dict=cust_dict,service_dict=service_dict) 
                                   
@app.route('/admin/summary')
def admin_summary():
    """
    Render the admin summary page.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Renders the admin summary page.
      401:
        description: User is not authorized to access this page.
    """
    if 'admin_user_id' in session:
        return render_template('admin_summary.html')
    return redirect(url_for('admin_login'))

# Manage User Route
@app.route('/admin/manage_user/<int:user_id>/<string:field>/<string:value>', methods=['GET', 'POST'])
def manage_user(user_id,field,value):
    """
    Approve/Reject or Block/Unblock a user.
    ---
    tags:
      - Admin
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID of the user to manage.
      - name: field
        in: path
        type: string
        required: true
        description: Field to update (approve or blocked).
      - name: value
        in: path
        type: string
        required: true
        description: Value to set for the field ('True' or 'False').
    responses:
      302:
        description: Redirects to the admin dashboard after managing the user.
      401:
        description: User is not authorized to perform this action.
    """
    if not session.get('admin_user_id'):
        return redirect(url_for('admin_login'))
    user = User.query.filter_by(id=user_id).first()
    # Approve/Reject & Block/Unblock professional
    if user and  field == 'approve':
        if value == 'False':
            user.approve = True
            flash('Professional/Customer approved successfully', 'success')
        elif value == 'True':
            user.approve = False
            flash('Professional/Customer rejected successfully', 'danger')

    if user and field == 'blocked' :
        if value == 'False':
            user.blocked = True
            flash('User blocked successfully', 'danger')
        elif value == 'True':
            user.blocked = False
            flash('User unblocked successfully', 'success')

    # Save changes to the database
    db.session.commit()

    return redirect(url_for('admin_dashboard'))

# Manage Services Route (CRUD operations)
@app.route('/admin/services/create_services', methods=['GET', 'POST'])
def create_services():
    """
    Create a new service.
    ---
    tags:
      - Admin
    parameters:
      - name: service_type
        in: formData
        type: string
        required: true
        description: Type of the service.
      - name: name
        in: formData
        type: string
        required: true
        description: Name of the service.
      - name: price
        in: formData
        type: number
        required: true
        description: Price of the service.
      - name: description
        in: formData
        type: string
        required: true
        description: Description of the service.
    responses:
      200:
        description: Successfully created a new service.
      302:
        description: Redirects to the admin dashboard after creating the service.
    """
    if not session.get('admin_user_id'):
        flash('Please log in to complete your profile.', 'danger')
        return redirect(url_for('admin_login'))
    
    form = ServiceForm()
    
    # Create Service
    if form.validate_on_submit():
        new_service = Service(
            service_type=form.service_type.data,
            name=form.name.data,
            price=form.price.data,
            description=form.description.data
        )
        db.session.add(new_service)
        flash('Service created successfully', 'success')
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('create_services.html', form=form)

# Update Services Route (CRUD operations)
@app.route('/admin/services/update_service/<int:service_id>', methods=['GET', 'POST'])
def update_services(service_id):
    """
    Update an existing service by ID.
    ---
    tags:
      - Admin
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: ID of the service to be updated.
      - name: service_type
        in: formData
        type: string
        required: true
        description: Type of the service.
      - name: name
        in: formData
        type: string
        required: true
        description: Name of the service.
      - name: price
        in: formData
        type: number
        required: true
        description: Price of the service.
      - name: description
        in: formData
        type: string
        required: true
        description: Description of the service.
    responses:
      200:
        description: Successfully updated the service.
      404:
        description: Service not found.
      302:
        description: Redirects to the admin dashboard after updating the service.
    """
    if not session.get('admin_user_id'):
        flash('Please log in to complete your profile.', 'danger')
        return redirect(url_for('admin_login'))
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    
    # Update Service
    if form.validate_on_submit():
        service.id = service_id
        service.service_type = form.service_type.data
        service.name = form.name.data
        service.price = form.price.data
        service.description = form.description.data
        flash('Service updated successfully', 'success')
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('create_services.html', form=form,service=service,editing=True)

# Handle delete operation
@app.route('/admin/services/delete_service/<int:service_id>', methods=['GET', 'POST'])
def delete_services(service_id):
    """
    Delete a specific service by ID.
    ---
    tags:
      - Admin
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: ID of the service to be deleted.
    responses:
      200:
        description: Successfully deleted the service.
      404:
        description: Service not found.
      302:
        description: Redirects to the admin dashboard after deletion.
    """
    service_to_delete = Service.query.get(service_id)
    if service_to_delete:
        db.session.delete(service_to_delete)
        db.session.commit()
        flash('Service deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

# Logout route for admin
@app.route('/admin/logout')
def admin_logout():
    """
    Log out the admin user.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Successfully logged out the admin user.
      302:
        description: Redirects to the admin login page.
    """
    session.pop('admin_user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/customer/profile', methods=['GET', 'POST'])
def customer_profile():
    """
    Retrieve and update the customer's profile.
    ---
    tags:
      - Customer
    parameters:
      - name: user_id
        in: session
        type: integer
        required: true
        description: "ID of the logged-in customer."
    responses:
      200:
        description: Renders the customer profile form.
      302:
        description: Redirects to the login page if the user is not logged in.
      201:
        description: Customer profile updated successfully.
    """
    if not session.get('user_id'):
        flash('Please log in to complete your profile.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    customer = CustomerProfile.query.filter_by(user_id=user_id).first()
    form = CustomerProfileForm(obj=customer)
    form.user_id.data = user_id
    form.user_name.data = User.query.get(user_id).username
    
    if form.validate_on_submit():
        if customer:
            customer.full_name = form.full_name.data
            customer.address = form.address.data
            customer.pin_code = form.pin_code.data
        else:
            new_customer_profile = CustomerProfile(
                user_id = form.user_id.data,
                full_name = form.full_name.data,
                address = form.address.data,
                pin_code = form.pin_code.data
            )            
            db.session.add(new_customer_profile)
        db.session.commit()
        flash('Customer Profile updated successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    return render_template('customer_profile.html', form=form)


# Customer Dashboard
@app.route('/customer/dashboard', methods=['GET', 'POST'])
def customer_dashboard():
    """
    Retrieve the customer dashboard with available services and service requests.
    ---
    tags:
      - Customer
    parameters:
      - name: service_type
        in: query
        type: string
        required: false
        description: "Filter services by service type."
    responses:
      200:
        description: Renders the customer dashboard with available services and service requests.
      302:
        description: Redirects to the login page if the user is not logged in.
    """
    if 'user_id' in session:
        if request.args.get("service_type"):
            services = Service.query.filter_by(service_type=request.args.get("service_type")).all()
        else:
            services = []
        service_requests = ServiceRequest.query.filter_by(customer_id=session['user_id']).all()
        professional_profile = ProfessionalProfile.query.all()
        service_dict = {}  # Define service_dict here
        prof_dict = {}  # Define user_dict here
        for professional in professional_profile:
            prof_dict[professional.user_id] = professional
        for service in Service.query.all():
            service_dict[service.id] = service
        return render_template('customer_dashboard.html', services=services, service_requests=service_requests,prof_dict=prof_dict,service_dict=service_dict)
    return redirect(url_for('login'))

@app.route('/customer/search', methods=['GET', 'POST'])
def customer_search():
    """
    Search for service professionals based on address, pin code, or service name.
    ---
    tags:
      - Customer
    parameters:
      - name: search_type
        in: formData
        type: string
        required: true
        description: "The type of search to perform (e.g., address, pin code, service name)."
      - name: search_text
        in: formData
        type: string
        required: true
        description: "The text to search for based on the selected search type."
    responses:
      200:
        description: Renders the customer search results page with the professionals found.
      302:
        description: Redirects to the login page if the user is not logged in.
      400:
        description: A flash message indicating no results were found for the search.
    """
    if not session.get('user_id'):
        flash('Please log in..', 'danger')
        return redirect(url_for('logn'))
    else:
        form = CustomerSearchForm()
        service_professional = []
        if form.validate_on_submit():
            search_type = form.search_type.data
            search_term = form.search_text.data.strip()

            service_professional =ProfessionalProfile.query.select_from(ProfessionalProfile).join(Service, ProfessionalProfile.service_type == Service.id).filter(
                or_(
                    ProfessionalProfile.address.ilike(f"%{search_term}%"),  # Search by address
                    ProfessionalProfile.pin_code.ilike(f"%{search_term}%"),  # Search by pin code
                    Service.name.ilike(f"%{search_term}%")  # Search by service name
                )
            ).with_entities(
                ProfessionalProfile.pin_code,  # Professional's name
                ProfessionalProfile.address,  # Professional's address
                Service.name,  # Service name
                Service.description, # Service description
                Service.price  # Service base price
            ).all()

            if not (service_professional):
                flash("No results found for your search.", "info")
        return render_template('customer_search.html', form=form,service_professional=service_professional)      

@app.route('/customer/summary')
def customer_summary():
    """
    Get the customer summary page.
    ---
    tags:
      - Customer
    responses:
      200:
        description: Renders the customer summary page.
      302:
        description: Redirects to the login page if the user is not logged in.
    """
    if 'user_id' in session:
        return render_template('customer_summary.html')
    return redirect(url_for('login'))


@app.route('/customer/create_service_request/<int:service_id>', methods=['GET', 'POST'])
def create_service_request(service_id):
    """
    Create a service request for a specified service.
    ---
    tags:
      - Customer
    parameters:
      - name: service_id
        in: path
        type: integer
        required: true
        description: "The ID of the service for which the request is being created."
    responses:
      200:
        description: Redirects to the customer dashboard upon successful creation of the service request.
      302:
        description: Redirects to the login page if the user is not logged in.
      400:
        description: A flash message indicating that no professional is available for the service or the professional is blocked/unapproved.
    """
    if 'user_id' in session:
        customer_id = session['user_id']
        professional = ProfessionalProfile.query.filter_by(service_type=service_id).first()
        if professional == None:
            flash('No professional offering this service yet! Please choose another service.', 'danger')
            return redirect(url_for('customer_dashboard'))
        else:
            user = User.query.filter_by(id=professional.user_id).first()
            if user.approve == False:
                flash('Professional offering this service is still not approved! Please choose another service.', 'danger')
                return redirect(url_for('customer_dashboard'))
            if user.blocked:
                flash('Professional offering this service is blocked! Please choose another service.', 'danger')
                return redirect(url_for('customer_dashboard'))
        professional_service_request = ServiceRequest.query.filter_by(professional_id=professional.user_id, service_id=service_id).order_by(desc(ServiceRequest.date_of_request)).first()
        if professional_service_request and (professional_service_request.service_status == 'requested' or professional_service_request.service_status == 'accepted'):
            flash('Service request already exists! Please wait for the professional to respond or choose another service.', 'danger')
            return redirect(url_for('customer_dashboard'))
        service_request = ServiceRequest(service_id=service_id, customer_id=customer_id, professional_id= professional.user_id, service_status='requested')
        db.session.add(service_request)
        db.session.commit()
        flash('Service request created successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    return redirect(url_for('login'))

@app.route('/customer/close_service_request/<int:request_id>', methods=['GET', 'POST'])
def close_service_request(request_id):
    """
    Close a service request and provide remarks or rating for the service.
    ---
    tags:
      - Customer
    parameters:
      - name: request_id
        in: path
        type: integer
        required: true
        description: "The ID of the service request to close."
    responses:
      200:
        description: Renders the service remarks page for closing the service request.
        schema:
          type: object
          properties:
            form:
              type: object
              description: The form for providing remarks and rating for the service.
      302:
        description: Redirects to the login page if the user is not logged in.
      201:
        description: Service request closed successfully.
    """
    if not session.get('user_id'):
        flash('Please log in to close this request.', 'danger')
        return redirect(url_for('login'))
    service_request = ServiceRequest.query.get_or_404(request_id)
    professional = ProfessionalProfile.query.filter_by(user_id=service_request.professional_id).first()
    service = Service.query.filter_by(id=service_request.service_id).first()
    form = ServiceRemarksForm()
    form.request_id.data = request_id
    form.service_name.data = service.name
    form.service_description.data = service.description
    form.full_name.data = professional.full_name
            
    # Give remarks for the service request
    if form.validate_on_submit():
        service_request.service_status = 'completed'
        service_request.date_of_completion = db.func.current_timestamp()
        service_request.remarks = form.remarks.data
        professional.reviews = (professional.reviews + form.rating.data)/2
        flash('Service request closed successfully', 'success')
        db.session.commit()
        return redirect(url_for('customer_dashboard'))
    return render_template('service_remarks.html',form=form)

@app.route('/professional/profile', methods=['GET', 'POST'])
def professional_profile():
    """
    View and update professional profile information.
    ---
    tags:
      - Professional
    parameters:
      - name: user_id
        in: formData
        type: integer
        required: true
        description: "The ID of the user accessing the profile."
      - name: full_name
        in: formData
        type: string
        required: true
        description: "The full name of the professional."
      - name: service_type
        in: formData
        type: string
        required: true
        description: "The type of service provided by the professional."
      - name: experience
        in: formData
        type: integer
        required: true
        description: "Years of experience in the service industry."
      - name: address
        in: formData
        type: string
        required: true
        description: "The address of the professional."
      - name: pin_code
        in: formData
        type: string
        required: true
        description: "The pin code for the professional's address."
      - name: file
        in: formData
        type: file
        required: false
        description: "An optional profile image or document (image or PDF) to upload."
    responses:
      200:
        description: Renders the professional profile update page.
        schema:
          type: object
          properties:
            form:
              type: object
              description: The form for updating the professional profile.
      302:
        description: Redirects to the login page if the user is not logged in.
      201:
        description: Profile updated successfully.
      400:
        description: Invalid file format or other validation errors.
    """
    if not session.get('user_id'):
        flash('Please log in to complete your profile.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    professional = ProfessionalProfile.query.filter_by(user_id=user_id).first()
    form = ProfessionalProfileForm(obj=professional)
    form.user_id.data = user_id
    form.user_name.data = User.query.get(user_id).username

    if form.validate_on_submit():
        if professional:
            professional.full_name = form.full_name.data
            professional.service_type = form.service_type.data
            professional.experience = form.experience.data
            professional.address = form.address.data
            professional.pin_code = form.pin_code.data
            file = form.file.data
            if file and allowed_file(file.filename):
                # Secure the filename and save it to the UPLOAD_FOLDER
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                professional.filename = file.filename
                professional.uploaded_at = db.func.current_timestamp() 
            else:
                flash('Invalid file format! Please upload only images and PDFs.', 'danger')
                return redirect(url_for('professional_profile',form=form))
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        else:
            # Handle file upload
            file = form.file.data
            if file and allowed_file(file.filename):
                # Secure the filename and save it to the UPLOAD_FOLDER
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Save file metadata and other form data to the database
                
                new_professional_profile = ProfessionalProfile(
                    user_id = form.user_id.data,
                    full_name = form.full_name.data,
                    filename = filename,
                    service_type = form.service_type.data,
                    experience = form.experience.data,
                    address = form.address.data,
                    pin_code = form.pin_code.data
                )            
                db.session.add(new_professional_profile)
                db.session.commit()
                flash('Profile updated successfully!', 'success')
                user = User.query.filter_by(id=user_id).first()
                if user.blocked or not user.approve:
                    return redirect(url_for('login'))
                return redirect(url_for('professional_dashboard'))
            else:
                flash('Invalid file format! Please upload only images and PDFs.', 'danger')
                return redirect(url_for('professional_profile'))
        return redirect(url_for('professional_dashboard'))    
    return render_template('professional_profile.html', form=form)

@app.route('/professional/dashboard')
def professional_dashboard():
    """
    Render the professional dashboard with active service requests and services.
    ---
    tags:
      - Professional
    responses:
      200:
        description: Renders the professional dashboard page with active service requests and services.
        schema:
          type: object
          properties:
            service_requests:
              type: array
              items:
                type: object
                description: List of active service requests for the professional.
            services:
              type: array
              items:
                type: object
                description: List of services related to the professional's requests.
            cust_dict:
              type: object
              description: Dictionary of customer profiles keyed by user ID.
            service_dict:
              type: object
              description: Dictionary of services keyed by service ID.
            service_requests_closed:
              type: array
              items:
                type: object
                description: List of closed service requests for the professional.
      302:
        description: Redirects to the login page if the user is not logged in.
    """
    if 'user_id' in session:
        professional_id = session['user_id']
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
        return render_template('professional_dashboard.html', service_requests=service_requests, services=services,cust_dict=cust_dict,service_dict=service_dict,service_requests_closed=service_requests_closed)
    return redirect(url_for('login'))

@app.route('/professional/search',methods=['GET', 'POST'])
def professional_search():
    """
    Search for service requests as a professional.
    ---
    tags:
      - Professional
    parameters:
      - name: search_type
        in: formData
        type: string
        required: true
        description: "The type of search to perform (date, location, or pin)."
        enum: ['date', 'location', 'pin']
      - name: search_text
        in: formData
        type: string
        required: true
        description: "The search term to filter service requests."
    responses:
      200:
        description: Renders the professional search results page with service requests.
        schema:
          type: object
          properties:
            form:
              type: object
              description: The search form used for filtering.
            service_requests:
              type: array
              items:
                type: object
                description: List of service requests matching the search criteria.
            cust_dict:
              type: object
              description: Dictionary of customer profiles keyed by user ID.
            service_dict:
              type: object
              description: Dictionary of services keyed by service ID.
      302:
        description: Redirects to the login page if the user is not logged in.
      404:
        description: If no results are found for the search query.
    """
    if not session.get('user_id'):
        flash('Please log in..', 'danger')
        return redirect(url_for('login'))
    else:
        form = ProfessionalSearchForm()
        professional_id = session['user_id']
        service_requests = []
        cust_dict = {}
        service_dict = {}
        
        if form.validate_on_submit():
            search_type = form.search_type.data
            search_term = form.search_text.data.strip()
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
                flash("No results found for your search.", "info")
        return render_template('professional_search.html', form=form,service_requests=service_requests,cust_dict=cust_dict,service_dict=service_dict)  
    
@app.route('/professional/summary')
def professional_summary():
    """
    Render the professional summary page.
    ---
    tags:
      - Professional

    responses:
      200:
        description: Renders the professional summary HTML page.
      302:
        description: Redirects to the login page if the user is not logged in.
    """
    if 'user_id' in session:
        return render_template('professional_summary.html')
    return redirect(url_for('login'))

@app.route('/professional/update_request_status/<string:status>/<int:request_id>')
def update_request_status(status,request_id):
    """
    Update the status of a service request.
    ---
    tags:
      - Professional
    
    parameters:
      - name: status
        in: path
        type: string
        required: true
        description: "The new status of the service request (accept or reject)"
        enum: ['accept', 'reject']
      - name: request_id
        in: path
        type: integer
        required: true
        description: "ID of the service request to be updated"
    responses:
      302:
        description: Redirects to the professional dashboard if successful, or to the login page if the user is not logged in.
      404:
        description: Service request not found.
    """
    if 'user_id' in session:
        service_request = ServiceRequest.query.get_or_404(request_id)
        if status == 'accept':
            service_request.service_status = 'accepted'
            service_request.date_of_accept_reject = db.func.current_timestamp()
        elif status == 'reject':
            service_request.service_status = 'rejected'
            service_request.date_of_accept_reject = db.func.current_timestamp()
        db.session.commit()
        flash('Service request updated successfully!', 'success')
        return redirect(url_for('professional_dashboard'))
    return redirect(url_for('login'))

# Define an API endpoint to return the reviews data
@app.route('/admin/summary/reviews', methods=['GET'])
def get_reviews():
    """
    Get reviews for all professionals.
    ---
    tags:
      - Admin
    
    responses:
      200:
        description: A list of professionals and their reviews.
        schema:
          type: array
          items:
            type: object
            properties:
              full_name:
                type: string
              reviews:
                type: string
    """
    professionals = ProfessionalProfile.query.with_entities(ProfessionalProfile.full_name,ProfessionalProfile.reviews).all()
    reviews_data = [{"full_name": p.full_name, "reviews": p.reviews} for p in professionals]
    return jsonify(reviews_data)

@app.route('/admin/summary/service_requests', methods=['GET'])
def get_service_requests():
    """
    Get summary of service requests grouped by completion date.
    ---
    tags:
      - Admin
    
    responses:
      200:
        description: A list of date-wise service request counts.
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
              count:
                type: integer
    """
    service_requests = (db.session.query(func.date(ServiceRequest.date_of_completion), func.count(ServiceRequest.id)).filter(ServiceRequest.date_of_completion!=None).group_by(func.date(ServiceRequest.date_of_completion)).all())
    datewise_requests =[{"date": str(sr[0]), "count": sr[1]} for sr in service_requests]   
    return jsonify(datewise_requests)

@app.route('/customer/summary/service_requests/<int:customer_id>', methods=['GET'])
def get_service_requests_customer(customer_id):
    """
    Get summary of service requests for a specific customer grouped by completion date.
    ---

    tags:
      - Customer
    
    parameters:
      - name: customer_id
        in: path
        type: integer
        required: true
        description: The ID of the customer
    responses:
      200:
        description: A list of date-wise service request counts for the customer.
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
              count:
                type: integer
    """
    service_requests_customer = (db.session.query(func.date(ServiceRequest.date_of_completion), func.count(ServiceRequest.id)).filter(ServiceRequest.date_of_completion!=None,ServiceRequest.customer_id==customer_id).group_by(func.date(ServiceRequest.date_of_completion)).all())
    datewise_requests =[{"date": str(sr[0]), "count": sr[1]} for sr in service_requests_customer]   
    return jsonify(datewise_requests)

@app.route('/professional/summary/reviews/<int:professional_id>', methods=['GET'])
def get_reviews_professional(professional_id):
    """
    Get reviews for a specific professional.
    ---
    tags:
        - Professional

    parameters:
      - name: professional_id
        in: path
        type: integer
        required: true
        description: The ID of the professional
    responses:
      200:
        description: A list of the professional's reviews.
        schema:
          type: array
          items:
            type: object
            properties:
              full_name:
                type: string
              reviews:
                type: string
    """
    professionals = ProfessionalProfile.query.with_entities(ProfessionalProfile.full_name,ProfessionalProfile.reviews).filter(ProfessionalProfile.user_id==professional_id).all()
    reviews_data = [{"full_name": p.full_name, "reviews": p.reviews} for p in professionals]
    return jsonify(reviews_data)

@app.route('/professional/summary/service_requests/<int:professional_id>', methods=['GET'])
def get_service_requests_professional(professional_id):
    """
    Get summary of service requests for a specific professional grouped by completion date.
    ---
    tags:
        - Professional
    
    parameters:
      - name: professional_id
        in: path
        type: integer
        required: true
        description: The ID of the professional
    responses:
      200:
        description: A list of date-wise service request counts for the professional.
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
              count:
                type: integer
    """
    service_requests = (db.session.query(func.date(ServiceRequest.date_of_completion), func.count(ServiceRequest.id)).join(ProfessionalProfile,ServiceRequest.professional_id==ProfessionalProfile.user_id).filter(ServiceRequest.date_of_completion!=None,ProfessionalProfile.user_id==professional_id).group_by(func.date(ServiceRequest.date_of_completion)).all())
    datewise_requests =[{"date": str(sr[0]), "count": sr[1]} for sr in service_requests]   
    return jsonify(datewise_requests)

@app.route('/app/test', methods=['GET'])
def get_test():
  return jsonify('Welcome to A-Z Household Services!')

CORS(app)
swagger = Swagger(app)

if __name__ == '__main__':
    app.run(debug=True)