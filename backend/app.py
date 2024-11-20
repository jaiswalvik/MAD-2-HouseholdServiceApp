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

app = Flask(__name__,template_folder='../frontend', static_folder='../frontend', static_url_path='/static')

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
  # Set the directory where your files are located
  file_directory = os.path.join(app.root_path, 'uploads')
  
  # Serve the file from the directory as an attachment
  return send_from_directory(file_directory, filename, as_attachment=True)

# Home Route
@app.route('/')
def index():
  return render_template('index.html') 

@app.route('/register', methods=['POST'])
def register():
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
    # Get the claims from the JWT
    claims = get_jwt()

    # Return claims (such as role and permissions) in JSON format
    return jsonify(claims=claims), 200

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
    return jsonify({"category": "danger","message": "Bad username or password"}), 401
  return jsonify({"category": "danger","message": "Bad request"}), 400
  
@app.route('/admin/profile', methods=['POST'])
@jwt_required()
def admin_profile():
  return jsonify({"message":"Admin! You can't make changes to your profile","category": "danger"}), 200

# Admin Dashboard
@app.route('/admin/dashboard', methods=['POST'])
@jwt_required()
def admin_dashboard():
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

@app.route('/admin/summary', methods=['GET'])
@jwt_required()
def admin_summary():
  claims = get_jwt()
  if claims['role'] != 'admin':
    return jsonify({"message": "Unauthorized access. Admins only.", "category": "danger"}), 401
  return jsonify({"message": "Admin summary data retrieved successfully.", "category": "success"}), 200

@app.route('/admin/manage_user/<int:user_id>/<string:field>/<string:value>', methods=['POST'])
@jwt_required()
def manage_user(user_id, field, value):
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
@jwt_required()
def customer_search():
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
@jwt_required()
def professional_profile():
  # Get user_id from JWT
  claims = get_jwt()
  if claims['role'] != 'professional':
    return jsonify({"message": "Not a Professional!", "category": "danger"}), 401
  user_id = claims['user_id']

  # Fetch the professional profile if it exists
  professional = ProfessionalProfile.query.filter_by(user_id=user_id).first()

  if request.method == 'GET':
    # Respond with professional profile data if available, otherwise send empty profile
    profile_data = {
        "user_id": user_id,
        "username": User.query.get(user_id).username,
        "full_name": professional.full_name if professional else "",
        "service_type": professional.service_type if professional else "",
        "experience": professional.experience if professional else "",
        "address": professional.address if professional else "",
        "pin_code": professional.pin_code if professional else "",
        "filename": professional.filename if professional else "",
        "reviews": professional.reviews if professional else 0
    }
    return jsonify(profile_data), 200

  elif request.method == 'POST':
    data = request.json
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
@jwt_required()
def get_reviews():
  claims = get_jwt()
  if claims['role'] != 'admin':
    return jsonify({"message": "Not an Admin!", "category": "danger"}), 401
  professionals = ProfessionalProfile.query.with_entities(ProfessionalProfile.full_name,ProfessionalProfile.reviews).all()
  reviews_data = [{"full_name": p.full_name, "reviews": p.reviews} for p in professionals]
  return jsonify(reviews_data)

@app.route('/admin/summary/service_requests', methods=['GET'])
@jwt_required()
def get_service_requests():
  claims = get_jwt()
  if claims['role'] != 'admin':
    return jsonify({"message": "Not an Admin!", "category": "danger"}), 401
  service_requests = (db.session.query(func.date(ServiceRequest.date_of_completion), func.count(ServiceRequest.id)).filter(ServiceRequest.date_of_completion!=None).group_by(func.date(ServiceRequest.date_of_completion)).all())
  datewise_requests =[{"date": str(sr[0]), "count": sr[1]} for sr in service_requests]   
  return jsonify(datewise_requests)

@app.route('/customer/summary/service_requests/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_service_requests_customer(customer_id):
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
def get_reviews_professional(professional_id):
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
def get_service_requests_professional(professional_id):
  claims = get_jwt()
  if claims['role'] != 'professional':
    return jsonify({"message": "Not a Professional!", "category": "danger"}), 401
  if claims['user_id'] != professional_id:
    return jsonify({"message": "Unauthorized access. Access to own data only.", "category": "danger"}), 401
    
  service_requests = (db.session.query(func.date(ServiceRequest.date_of_completion), func.count(ServiceRequest.id)).join(ProfessionalProfile,ServiceRequest.professional_id==ProfessionalProfile.user_id).filter(ServiceRequest.date_of_completion!=None,ProfessionalProfile.user_id==professional_id).group_by(func.date(ServiceRequest.date_of_completion)).all())
  datewise_requests =[{"date": str(sr[0]), "count": sr[1]} for sr in service_requests]   
  return jsonify(datewise_requests)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
swagger = Swagger(app)

if __name__ == '__main__':
    app.run(debug=True)