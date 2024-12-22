from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Customer, Interaction, User  # Models from models.py
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Load user for authentication
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    customers = Customer.query.all()
    total_customers = len(customers)
    total_interactions = Interaction.query.count()
    print(f"Total Customers: {total_customers}")  # Debugging line
    print(f"Total Interactions: {total_interactions}") 
    return render_template('dashboard.html', customers=customers, total_customers=total_customers, total_interactions=total_interactions)
    # return render_template('dashboard.html', customers=customers)

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash("Username or email already exists.", "danger")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# CRUD for Customers
@app.route('/add_customer', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        customer = Customer(name=name, email=email, phone=phone)
        db.session.add(customer)
        db.session.commit()
        flash("Customer added successfully.", "success")
        return redirect(url_for('index'))
    return render_template('add_customer.html')

@app.route('/edit_customer/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        db.session.commit()
        flash("Customer updated successfully.", "success")
        return redirect(url_for('index'))
    return render_template('edit_customer.html', customer=customer)

@app.route('/delete_customer/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    
    try:
        # Delete interactions associated with the customer
        interactions = Interaction.query.filter_by(customer_id=id).all()
        for interaction in interactions:
            db.session.delete(interaction)
        
        # Delete the customer
        db.session.delete(customer)
        db.session.commit()
        flash("Customer and associated interactions deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("There was an issue deleting the customer.", "error")
    
    return redirect(url_for('index'))


@app.route('/view_customer/<int:id>')
@login_required
def view_customer(id):
    customer = Customer.query.get_or_404(id)
    return render_template('view_customer.html', customer=customer)

@app.route('/add_interaction/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def add_interaction(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Hardcoding options, but you can also pass them dynamically if needed
    interaction_types = ['Call', 'Meeting', 'Feedback', 'Message', 'Email', 'Survey', 'Visit']
    
    if request.method == 'POST':
        interaction_type = request.form['type']
        notes = request.form['notes']
        
        new_interaction = Interaction(
            type=interaction_type, 
            notes=notes, 
            customer_id=customer.id
        )
        
        try:
            db.session.add(new_interaction)
            db.session.commit()
            flash("Interaction added successfully.", "success")
            return redirect(url_for('view_customer', id=customer.id))
        except Exception as e:
            db.session.rollback()
            flash("There was an issue adding the interaction.", "error")
    
    return render_template('add_interaction.html', customer=customer, interaction_types=interaction_types)



@app.route('/edit_interaction/<int:interaction_id>', methods=['GET', 'POST'])
@login_required
def edit_interaction(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)
    
    if request.method == 'POST':
        interaction.type = request.form['type']
        interaction.notes = request.form['notes']
        
        try:
            db.session.commit()
            flash("Interaction updated successfully.", "success")
            return redirect(url_for('view_customer', id=interaction.customer.id))
        except Exception as e:
            db.session.rollback()
            flash("There was an issue updating the interaction.", "error")
    
    return render_template('edit_interaction.html', interaction=interaction)

@app.route('/delete_interaction/<int:interaction_id>', methods=['POST'])
@login_required
def delete_interaction(interaction_id):
    interaction = Interaction.query.get_or_404(interaction_id)

    try:
        customer_id = interaction.customer_id  # Save the customer ID before deleting the interaction
        db.session.delete(interaction)
        db.session.commit()
        flash("Interaction deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"There was an issue deleting the interaction: {str(e)}", "error")

    return redirect(url_for('view_customer', id=customer_id))


@app.route('/dashboard')
@login_required
def dashboard():
    customers = Customer.query.all()
    total_customers = len(customers)
    total_interactions = Interaction.query.count()
    print(f"Total Customers: {total_customers}")  # Debugging line
    print(f"Total Interactions: {total_interactions}") 
    return render_template('dashboard.html', customers=customers, total_customers=total_customers, total_interactions=total_interactions)


@app.route('/search_customer', methods=['GET', 'POST'])
@login_required
def search_customer():
    query = request.form.get('query', '').strip()
    customers = Customer.query.filter(Customer.name.ilike(f"%{query}%")).all()
    return render_template('search_customer.html', customers=customers)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
