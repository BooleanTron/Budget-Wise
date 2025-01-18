from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'Budget-Wise'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    occupation = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    income = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_first_login = db.Column(db.Boolean, default=True)  # Add the is_first_login attribute

class Necessities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    housing = db.Column(db.Float, nullable=False, default=0.0)
    transport = db.Column(db.Float, nullable=False, default=0.0)
    food = db.Column(db.Float, nullable=False, default=0.0)
    stationery = db.Column(db.Float, nullable=False, default=0.0)
    medicine = db.Column(db.Float, nullable=False, default=0.0)
    phone_bills = db.Column(db.Float, nullable=False, default=0.0)
    toiletries = db.Column(db.Float, nullable=False, default=0.0)

class Additional_Expenses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    eating_out = db.Column(db.Float, nullable=False, default=0.0)
    snacks = db.Column(db.Float, nullable=False, default=0.0)
    clothes = db.Column(db.Float, nullable=False, default=0.0)
    outings = db.Column(db.Float, nullable=False, default=0.0)
    travel = db.Column(db.Float, nullable=False, default=0.0)
    subscriptions = db.Column(db.Float, nullable=False, default=0.0)

class Miscellaneous_Expenses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)

with app.app_context():
    db.create_all()

def calculate_totals(user_id):
    necessities_total = db.session.query(
        func.sum(
            Necessities.housing + 
            Necessities.transport + 
            Necessities.food + 
            Necessities.stationery + 
            Necessities.medicine + 
            Necessities.phone_bills + 
            Necessities.toiletries
        )
    ).filter(Necessities.user_id == user_id).scalar() or 0  

    additional_expenses_total = db.session.query(
        func.sum(
            Additional_Expenses.eating_out + 
            Additional_Expenses.snacks + 
            Additional_Expenses.clothes + 
            Additional_Expenses.outings + 
            Additional_Expenses.travel + 
            Additional_Expenses.subscriptions
        )
    ).filter(Additional_Expenses.user_id == user_id).scalar() or 0  

    miscellaneous_expenses_total = db.session.query(
        func.sum(Miscellaneous_Expenses.amount)
    ).filter(Miscellaneous_Expenses.user_id == user_id).scalar() or 0  

    user = User.query.get(user_id)
    funds_remaining = user.income - necessities_total
    total_expense = necessities_total + additional_expenses_total + miscellaneous_expenses_total
    savings = user.income - total_expense

    necessities_percent = (necessities_total * 100) / user.income
    additional_expenses_percent = (additional_expenses_total * 100) / funds_remaining
    miscellaneous_expenses_percent = (miscellaneous_expenses_total * 100) / funds_remaining

    return necessities_total, additional_expenses_total, miscellaneous_expenses_total, total_expense, savings, necessities_percent, additional_expenses_percent, miscellaneous_expenses_percent


# Routes
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            if user.is_first_login:
                return redirect(url_for('survey'))  
            return redirect(url_for('dashboard'))  
        else:
            return "Invalid credentials, please try again."
    return render_template('login.html')


@app.route('/survey', methods=['GET', 'POST'])
def survey():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if request.method == 'POST':
        housing = request.form.get('housing', 0)
        transport = request.form.get('transport', 0)
        food = request.form.get('food', 0)
        stationary = request.form.get('stationary', 0)
        medicine = request.form.get('medicine', 0)
        phone_bills = request.form.get('phone_bills', 0)
        toiletries = request.form.get('toiletries', 0)

        new_entry = Necessities(
            user_id=user_id,
            housing=housing,
            transport=transport,
            food=food,
            stationery=stationary,
            medicine=medicine,
            phone_bills=phone_bills,
            toiletries=toiletries
        )
        db.session.add(new_entry)
        user.is_first_login = False
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('survey.html')


@app.route('/dashboard', methods=['GET'])
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    necessities_total, additional_expenses_total, miscellaneous_expenses_total, total_expense, savings, necessities_percent, additional_expenses_percent, miscellaneous_expenses_percent = calculate_totals(user_id)

    necessities_color = 'red' if necessities_percent > 50 else 'green' if necessities_percent < 30 else 'yellow'
    additional_color = 'red' if additional_expenses_percent > 40 else 'green' if additional_expenses_percent < 20 else 'yellow'
    miscellaneous_color = 'red' if miscellaneous_expenses_percent > 10 else 'green'

    labels = ['Necessities', 'Additional Expenses', 'Miscellaneous Expenses', 'Savings']
    values = [necessities_total, additional_expenses_total, miscellaneous_expenses_total, savings]

    return render_template('dashboard.html', 
        user=user,
        necessities_color=necessities_color,
        additional_color=additional_color,
        miscellaneous_color=miscellaneous_color,
        total_expense=total_expense,
        labels=labels, values=values, name=user.name)

@app.route('/update_income', methods=['GET', 'POST'])
def update_income():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    if request.method == 'POST':
        new_income = request.form['income']
        user.income = new_income
        db.session.commit()
        flash('Income updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('update_income.html', income=user.income)



@app.route('/necessities')
def necessities():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    necessities = Necessities.query.filter_by(user_id=user_id).all()

    return render_template('necessities.html', necessities=necessities)

@app.route('/update_necessity/<int:id>/<expense>', methods=['GET', 'POST'])
def update_necessity(id, expense):
    necessity = Necessities.query.get_or_404(id)

    expense_value = getattr(necessity, expense, None)  

    if request.method == 'POST':
        new_amount = request.form['amount']
        setattr(necessity, expense, float(new_amount))
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('necessities'))  


    return render_template('update_necessity.html', necessity=necessity, expense=expense, expense_value=expense_value)


@app.route('/additional_expenditure')
def additional_expenditure():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    necessities_total = db.session.query(
        func.sum(
            Necessities.housing + 
            Necessities.transport + 
            Necessities.food + 
            Necessities.stationery + 
            Necessities.medicine + 
            Necessities.phone_bills + 
            Necessities.toiletries
        )
    ).filter(Necessities.user_id == user_id).scalar() or 0

    additional_expenses = Additional_Expenses.query.filter_by(user_id=user_id).first()
    
    if not additional_expenses:
        additional_expenses = Additional_Expenses(
            user_id=user_id,
            eating_out=0.0,
            snacks=0.0,
            clothes=0.0,
            outings=0.0,
            travel=0.0,
            subscriptions=0.0
        )
        db.session.add(additional_expenses)
        db.session.commit()

    remaining_funds = user.income - necessities_total
    if remaining_funds <= 0:
        remaining_funds = 1  

    additional_expenses_data = [
        {
            "category": "Eating Out",
            "amount": additional_expenses.eating_out,
            "percentage": round((additional_expenses.eating_out / remaining_funds) * 100, 2),
            "color": "green" if (additional_expenses.eating_out / remaining_funds) * 100 < 10 else "red",
            "update_url": url_for('update_additional', category="eating_out")
        },
        {
            "category": "Snacks",
            "amount": additional_expenses.snacks,
            "percentage": round((additional_expenses.snacks / remaining_funds) * 100, 2),
            "color": "green" if (additional_expenses.snacks / remaining_funds) * 100 < 5 else "red",
            "update_url": url_for('update_additional', category="snacks")
        },
        {
            "category": "Clothes",
            "amount": additional_expenses.clothes,
            "percentage": round((additional_expenses.clothes / remaining_funds) * 100, 2),
            "color": "green" if (additional_expenses.clothes / remaining_funds) * 100 < 10 else "red",
            "update_url": url_for('update_additional', category="clothes")
        },
        {
            "category": "Outings",
            "amount": additional_expenses.outings,
            "percentage": round((additional_expenses.outings / remaining_funds) * 100, 2),
            "color": "green" if (additional_expenses.outings / remaining_funds) * 100 < 8 else "red",
            "update_url": url_for('update_additional', category="outings")
        },
        {
            "category": "Travel",
            "amount": additional_expenses.travel,
            "percentage": round((additional_expenses.travel / remaining_funds) * 100, 2),
            "color": "green" if (additional_expenses.travel / remaining_funds) * 100 < 15 else "red",
            "update_url": url_for('update_additional', category="travel")
        },
        {
            "category": "Subscriptions",
            "amount": additional_expenses.subscriptions,
            "percentage": round((additional_expenses.subscriptions / remaining_funds) * 100, 2),
            "color": "green" if (additional_expenses.subscriptions / remaining_funds) * 100 < 5 else "red",
            "update_url": url_for('update_additional', category="subscriptions")
        }
    ]

    return render_template(
        'additional_expenditure.html',
        additional_expenses=additional_expenses_data,
        remaining_funds=remaining_funds
    )

@app.route('/update_additional/<category>', methods=['GET', 'POST'])
def update_additional(category):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    additional_expenses = Additional_Expenses.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        new_value = float(request.form['amount'])
        setattr(additional_expenses, category, new_value)
        db.session.commit()
        flash(f'{category.replace("_", " ").capitalize()} updated successfully!', 'success')
        return redirect(url_for('additional_expenditure'))

    current_value = getattr(additional_expenses, category, 0)
    return render_template('update_additional.html', category=category.replace("_", " ").capitalize(), current_value=current_value)


@app.route('/miscellaneous', methods=['GET', 'POST'])
def miscellaneous():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])

        new_expense = Miscellaneous_Expenses(user_id=user_id, name=name, amount=amount)
        db.session.add(new_expense)
        db.session.commit()
        flash("Expense added successfully!", "success")
        return redirect(url_for('miscellaneous'))

    expenses = Miscellaneous_Expenses.query.filter_by(user_id=user_id).all()
    return render_template('miscellaneous.html', expenses=expenses)

@app.route('/update_expense/<int:id>', methods=['GET', 'POST'])
def update_expense(id):
    expense = Miscellaneous_Expenses.query.get_or_404(id)

    if request.method == 'POST':
        expense.name = request.form['name']
        expense.amount = float(request.form['amount'])
        db.session.commit()
        flash("Expense updated successfully!", "success")
        return redirect(url_for('miscellaneous'))

    return render_template('update_expense.html', expense=expense)


@app.route('/savings')
def savings():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    necessities_total, additional_expenses_total, miscellaneous_expenses_total, total_expense, savings, necessities_percent, additional_expenses_percent, miscellaneous_expenses_percent = calculate_totals(user_id)

    savings_percentage = (savings / user.income) * 100 if user.income > 0 else 0

    recommendations = []
    ranges = {
        'Eating Out': 10,
        'Snacks': 5,
        'Clothes': 10,
        'Outings': 8,
        'Travel': 15,
        'Subscriptions': 5
    }

    additional_expenses = Additional_Expenses.query.filter_by(user_id=user_id).first()

    for category, max_percentage in ranges.items():
        expense_value = getattr(additional_expenses, category.lower().replace(" ", "_"), 0)
        if (expense_value / (user.income - necessities_total)) * 100 > max_percentage:
            recommendations.append({
                'category': category,
                'expense_value': expense_value,
                'percentage': round((expense_value / (user.income - necessities_total)) * 100, 2)
            })

    return render_template('savings.html', 
                           savings=savings, 
                           savings_percentage=savings_percentage, 
                           recommendations=recommendations,
                           total_expense=total_expense, 
                           user=user)




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        occupation = request.form['occupation']
        age = int(request.form['age'])
        income = int(request.form['income'])
        username = request.form['username']
        password = request.form['password']

        new_user = User(name=name, occupation=occupation, age=age, income=income, username=username, password=password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Error: {e}"

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
