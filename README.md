# Household Services App

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)

## Introduction
The Household Services App is designed to connect customers with professional service providers. Users can create service requests, and professionals can manage and respond to these requests. This app aims to streamline the process of finding and offering household services.

## Features
- User registration and role selection (Customer/Professional)
- Dashboard for customers to create service requests
- Dashboard for professionals to manage requests
- Search functionality for Admin to find Customers and Professionals
- Responsive design for mobile and desktop

## Technologies Used
- **Backend:** Flask, SQLAlchemy, Redis, Celery
- **Frontend:** HTML, CSS, Bootstrap, VueJS
- **Database:** SQLite
- **Libraries:** JWT for security, Flasgger for API documentation, ChartJS for data visualization

## Installation
1. Clone the repository:
   - git clone https://github.com/jaiswalvik/MAD-2-HouseholdServiceApp.git
   - cd MAD-2-HouseholdServiceApp
2. Create a virtual environment:
   - python -m venv env
   - source env/bin/activate
4. Install the required packages:
   - pip install -r requirements.txt
5. Run the application
   - flask run
6. Install Redis:
   - https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/
7. Run Redis:
   - sudo service redis-server start
8. Run Celery worker in another window:
   - celery -A app.celery worker --loglevel=info
9. Run Celery beat in another window:
   - celery -A app.celery beat --loglevel=info

## Usage
 - video presentation link: [Project Presentation](<https://drive.google.com/file/d/1iW0_ZA0qrEmAAvfudgKp77NKzaiqKk_4/view?usp=sharing>)
