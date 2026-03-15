from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "able_kids_secret_key"  # Required for flash messages

# 1. Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///able_kids.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. Database Models


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True)
    gender = db.Column(db.String(10))  # New Column: Male, Female, Other
    records = db.relationship(
        'DailyActivity', backref='student', cascade="all, delete-orphan", lazy=True)


class DailyActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey(
        'student.id'), nullable=False)
    category = db.Column(db.String(100))
    stage = db.Column(db.Integer)
    notes = db.Column(db.Text)
    date_logged = db.Column(db.DateTime, default=datetime.utcnow)


# 3. Initialize Database
with app.app_context():
    db.create_all()

# Add this so the navbar dropdown works on every page


@app.context_processor
def inject_students():
    all_students = Student.query.order_by(Student.name).all()
    return dict(students_list=all_students)


@app.context_processor
def inject_global_data():
    all_students = Student.query.order_by(Student.name).all()

    # Fetch stages from DB
    stages_config = AppConfig.query.filter_by(key='total_stages').first()
    max_stages = stages_config.value if stages_config else 20

    return dict(
        students_list=all_students,
        # Now {{ total_stages }} works in ANY html file
        total_stages=max_stages
    )


@app.route('/')
def index():
    # 1. Get all categories from DB
    categories = BehavioralCategory.query.all()

    # 2. Get the actual count (e.g., if Niru added a 19th one, it shows 19)
    category_count = len(categories)

    # 3. Get the Max Stages from settings
    stages_config = AppConfig.query.filter_by(key='total_stages').first()
    max_val = stages_config.value if stages_config else 20

    # Send students, categories, count, and max_val to the HTML
    students = Student.query.all()
    return render_template('index.html',
                           students=students,
                           categories_list=categories,
                           cat_count=category_count,
                           total_stages=max_val)


@app.context_processor
def inject_global_vars():
    # This makes {{ total_stages }} available in base.html, dashboard.html, etc.
    config = AppConfig.query.filter_by(key='total_stages').first()
    return dict(total_stages=config.value if config else 20)


@app.route('/add_activity', methods=['POST'])
def add_activity():
    try:
        s_id = request.form.get('student_id')
        new_entry = DailyActivity(
            student_id=int(s_id),
            category=request.form.get('category'),
            stage=int(request.form.get('stage')),
            notes=request.form.get('notes')
        )
        db.session.add(new_entry)
        db.session.commit()
        flash("Activity recorded successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    return redirect(url_for('view_student', student_id=s_id))


@app.route('/student/<int:student_id>')
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    records = DailyActivity.query.filter_by(student_id=student_id).order_by(
        DailyActivity.date_logged.desc()).all()
    return render_template('student_view.html', student=student, records=records)


@app.route('/dashboard')
def dashboard():
    # Filter by category if requested
    cat_filter = request.args.get('category', '')
    query = DailyActivity.query
    if cat_filter:
        query = query.filter_by(category=cat_filter)

    activities = query.order_by(DailyActivity.date_logged.desc()).all()
    return render_template('dashboard.html', activities=activities)

# New Models


class BehavioralCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    group = db.Column(db.String(50))  # e.g., "Physical", "Social"


class AppConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True)
    value = db.Column(db.Integer)

# --- Settings Route ---


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Update Total Stages logic...
        new_stages = request.form.get('total_stages')
        config = AppConfig.query.filter_by(key='total_stages').first()
        if config:
            config.value = int(new_stages)
            db.session.commit()
            flash(f"Maximum stages updated to {new_stages}!", "success")

    # UPDATE: Order by group then name so the Serial Numbers (1-18)
    # follow a logical category order (Physical, then Self-Help, etc.)
    categories = BehavioralCategory.query.order_by(
        BehavioralCategory.group, BehavioralCategory.name).all()

    stages_config = AppConfig.query.filter_by(key='total_stages').first()
    current_stages = stages_config.value if stages_config else 20

    return render_template('settings.html',
                           categories=categories,
                           stages=current_stages)


@app.route('/settings/add_category', methods=['POST'])
def add_category():
    name = request.form.get('cat_name')
    group = request.form.get('cat_group')
    if name:
        new_cat = BehavioralCategory(name=name, group=group)
        db.session.add(new_cat)
        db.session.commit()
        flash(f"Category '{name}' added!", "success")
    return redirect(url_for('settings'))


@app.route('/delete_record/<int:id>')
def delete_record(id):
    record = DailyActivity.query.get_or_404(id)
    s_id = record.student_id
    db.session.delete(record)
    db.session.commit()
    flash("Record deleted.", "warning")
    return redirect(url_for('view_student', student_id=s_id))


@app.route('/students')
def manage_students():
    students = Student.query.all()
    return render_template('manage_students.html', students=students)


@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form.get('name')
    roll_no = request.form.get('roll_no')
    gender = request.form.get('gender')  # Get gender from form

    new_student = Student(name=name, roll_no=roll_no, gender=gender)
    db.session.add(new_student)
    db.session.commit()
    return redirect(url_for('manage_students'))


@app.route('/delete_student/<int:id>')
def delete_student(id):
    student = Student.query.get_or_404(id)
    name = student.name
    db.session.delete(student)
    db.session.commit()
    flash(f"Profile and all records for {name} deleted.", "danger")
    return redirect(url_for('manage_students'))


@app.route('/edit_student/<int:id>')
def edit_student_page(id):
    student = Student.query.get_or_404(id)
    return render_template('edit_student.html', student=student)


@app.route('/settings/delete_category/<int:id>')
def delete_category(id):
    cat = BehavioralCategory.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    flash(f"Category '{cat.name}' removed.", "warning")
    return redirect(url_for('settings'))


@app.route('/update_student/<int:id>', methods=['POST'])
def update_student(id):
    student = Student.query.get_or_404(id)
    student.name = request.form.get('name')
    student.gender = request.form.get('gender') # Add this line
    student.roll_no = request.form.get('roll_no')
    db.session.commit()
    flash("Student profile updated!", "info")
    return redirect(url_for('manage_students'))


@app.route('/edit/<int:record_id>')
def edit_record(record_id):
    record = DailyActivity.query.get_or_404(record_id)
    return render_template('edit_record.html', record=record)


@app.route('/update/<int:record_id>', methods=['POST'])
def update_record(record_id):
    record = DailyActivity.query.get_or_404(record_id)
    record.stage = int(request.form.get('stage'))
    record.notes = request.form.get('notes')
    db.session.commit()
    flash("Activity record updated!", "info")
    return redirect(url_for('view_student', student_id=record.student_id))


if __name__ == '__main__':
    app.run(debug=True)

with app.app_context():
    db.create_all()

    # Seed Default Categories only if the table is empty
    if not BehavioralCategory.query.first():
        default_categories = [
            ("Gross Motor", "Physical"), ("Fine Motor", "Physical"),
            ("Locomotion", "Physical"), ("Occupation", "Physical"),
            ("Eating/Drinking", "Self-Help"), ("Dressing", "Self-Help"),
            ("Grooming", "Self-Help"), ("Toileting", "Self-Help"),
            ("Self-Help General", "Self-Help"), ("Communication", "Social"),
            ("Social Interaction", "Social"), ("Self-Direction", "Social"),
            ("Socialization", "Social"), ("Reading", "Academic"),
            ("Writing", "Academic"), ("Numbers", "Academic"),
            ("Money", "Academic"), ("Time", "Academic")
        ]
        for name, gp in default_categories:
            db.session.add(BehavioralCategory(name=name, group=gp))
        db.session.commit()
        print("Database Seeded with 18 Categories!")
