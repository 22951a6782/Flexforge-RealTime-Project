
# Flex Forge - Your One-Stop Solution for Fitness and Wellness

Welcome to **Flex Forge!** This platform offers a range of fitness services, including customized workout plans, personal training, and nutrition guidance. Our goal is to make managing your fitness journey easy and accessible through a seamless, user-friendly interface.

## Project Overview
**Flex Forge** is a web application designed to enhance the gym experience for both members and trainers. It allows gyms to showcase their services, helping potential members find the right fit and access key information. The platform simplifies gym membership management, workout planning, and nutrition guidance for a smooth fitness journey.

## Purpose
1. Attract potential members by showcasing gym facilities and services.
2. Offer comprehensive features and workout plans to improve member experience.
3. Facilitate effective communication between members and trainers.

## Goals
- **Visibility:** Increase the online presence of gyms to attract more members.
- **Member Engagement:** Provide valuable features that boost member satisfaction and retention.
- **Streamlined Operations:** Ensure efficient management of memberships and trainer assignments.



## Demo
You can view the static version of the FlexForge project here - Website

## Project Structure
Here is an overview of the project structure with links to key files and directories:

##### `static/`
Contains static assets such as images used throughout the website.
- ##### `images/`  
  This folder holds images for various services, such as workout types, feedback emojis, and home page images, etc.

##### `templates/`
Contains the HTML templates for different pages of the web application.
- ##### `home.html`  
  The main landing page highlights key sections such as **Contact**, **Blog**, **About**, **Trainer/Member**, and **Membership Plans**, providing a seamless way to explore services and connect with the FlexForge community.

##### `flaskCode.py`
The main Python script is responsible for handling **membership requests**, **trainer sessions**, and the **routing logic** for managing trainers, members, and membership plans on the FlexForge gym portal.

##### `Code Documentation.pdf`
Documentation covering the routing and Flask backend implementation.

##### `Database MySQL Queries.pdf`
A PDF containing the MySQL queries used to set up and manage the database for **members**, **trainers**, **progress reports**, and **membership plans**.

##### `Libraries and Modules.pdf`
A PDF containing detailed descriptions and the purpose of libraries and modules used during the course of the project.

##### `requirements.txt`
A list of the Python dependencies needed to run the project locally.

##### `LICENSE`
The license under which this project is released.

##### `README.md`
The current project documentation.



## Forms & Routing

### 1. Member Registration Form
The Member Registration Form collects essential details from gym members for registration. The form includes:
- Full Name
- Email (must be unique)
- Password
- Confirm Password  
This information is stored securely in the `user` table of the MySQL database.

#### Backend Logic:
1. **Password Hashing**: User passwords are hashed using the `sha256` method before being stored.
2. **Email Uniqueness**: Duplicate email addresses are checked to ensure uniqueness.
3. **Data Insertion**: After validation, user details are saved in the database.

#### Trainer Assignment:
- The `trainer_id` in the `user` table is allocated after the user takes a membership plan and is assigned a personal trainer based on their membership tier.

#### User Flow:
1. User fills out the form with required details.
2. Password is hashed, and email uniqueness is validated.
3. User data is stored in the `user` table, and they are redirected to the login page.
4. The `trainer_id` will be assigned once the user completes membership registration.

---

### 2. Membership Payment Form
The Membership Payment Form is used to complete the purchase of a membership plan. It includes the following details:
- UPI ID
- Email (must match the registered email)  
The **Training Type** and **Tier** are pre-selected on the previous page. Payment information is stored securely in the `payments` table.

#### Database Table: `payments`
- `id`: Auto-incremented unique identifier for each payment.
- `training_type`: The type of training the member selected.
- `tier`: Membership tier (Basic, Advanced, Premium).
- `amount`: The amount paid for the membership.
- `upi_id`: The UPI ID used for the transaction.
- `email`: User's email for payment verification.
- `payment_date`: Timestamp of the payment.
- `validation`: Status of the payment (default is 'no').

#### Backend Logic:
1. **Payment Information**: The form submits the UPI ID and email, while the training type and tier are pre-selected.
2. **Data Insertion**: After payment, this information is stored in the `payments` table.
3. **Validation**: The `validation` column is set to 'no' by default. The admin reviews the payment and updates the validation to 'yes' upon approval.

#### User Flow:
1. User selects a membership plan and training type on the previous page.
2. User fills out the UPI ID and email and clicks the "Pay Now" button.
3. After payment, the user is directed to a Thank You page.
4. The admin reviews the payment details, updates the validation to 'yes', allowing the member to access the member dashboard.

---

### 3. Member Login Page
The Member Login Page allows gym members to securely log in to their accounts. It collects:
- Email
- Password

#### Login Process:
1. **Email and Password Verification**: The system checks if the email exists in the `user` table. The entered password is hashed and compared with the stored hashed password.
2. **Trainer ID Check**:  
   - If `trainer_id` is null, the system checks the `payments` table to verify if the member has paid for their membership.
   - If `validation` is set to 'yes', a personal trainer is assigned.
   - If `validation` is not 'yes', the member is redirected to the Membership Plans page.
3. **Subsequent Logins**: If a trainer is already assigned, the member can log in without reassignment.

#### User Flow:
1. Member enters email and password and submits the form.
2. The system verifies credentials and checks for trainer assignment and payment status.
3. If valid, the member is logged in and a trainer is assigned.
4. If payment validation is not confirmed, the member is redirected to the Membership Plans page.

---

### 4. Trainer Registration Page
The Trainer Registration Page allows trainers to register and provide details for inclusion in the gym's trainer database. It collects:
- Full Name
- Email
- Password
- Confirm Password
- Expertise (Select from predefined options)
- Certifications

#### User Flow:
1. Trainer fills out the registration form.
2. The system validates the inputs and checks for duplicate emails.
3. If validated, the trainer's information is securely stored.
4. After registration, the trainer is redirected to the Trainer Login Page.

---

### 5. Trainer Login Page
The Trainer Login Page allows registered trainers to access their accounts by providing:
- Email
- Password

#### Login Process:
1. Trainers enter their email and password.
2. The system verifies the credentials against the `trainers` table.
3. Upon successful login, trainers are directed to their dashboard.
4. If the credentials are invalid, trainers are redirected to the Trainer Registration Page.

---

### 6. Member Progress Tracking Page
The Member Progress Tracking Page allows members to self-report their progress by providing:
- Date
- Workout Details
- Any Issues

#### Data Storage:
Information is stored in the `progress_tracking` table with the following fields:
- `id` (int, AI, PK)
- `user_id` (int)
- `trainer_id` (int)
- `progress_date` (date)
- `workout_details` (text)
- `issues` (text)
- `created_at` (timestamp)

#### Submission Process:
1. Members fill out the form with progress details.
2. Upon successful submission, they are redirected to the Member Dashboard Page.

#### Trainer Access:
Trainers can log in to view member progress via the `progress_tracking` table.

---

### 7. Feedback Form
The Feedback Form allows members to provide their feedback, which includes:
- Rating (1 to 5, represented through images)
- Category (Options: Suggestion, Issue, Compliment)
- Feedback Text

#### Data Storage:
Submitted feedback is stored in the `feedback` table with the following fields:
- `id` (int, AI, PK)
- `user_id` (int)
- `rating` (tinyint)
- `category` (varchar)
- `feedback` (text)
- `created_at` (timestamp)

#### Submission Process:
1. Members complete the feedback form.
2. The feedback is saved to the database for review.

#### Utilizing Feedback:
- Feedback is analyzed to calculate the average rating.
- This helps identify areas for improvement and boosts member satisfaction.

