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
    # Cascade delete: Deleting a student removes all their activity records
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


@app.route('/')
def index():
    # Look for the 'search' ID sent by the dropdown
    search_id = request.args.get('search')

    if search_id:
        # If an ID was sent, filter the list to show ONLY that student
        students = Student.query.filter_by(id=search_id).all()
    else:
        # Otherwise, show all students as usual
        students = Student.query.all()

    return render_template('index.html', students=students)


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
    group = db.Column(db.String(50)) # e.g., "Physical", "Social"

class AppConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True)
    value = db.Column(db.Integer)

# --- Settings Route ---
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # Update Total Stages
        new_stages = request.form.get('total_stages')
        config = AppConfig.query.filter_by(key='total_stages').first()
        if config:
            config.value = int(new_stages)
            db.session.commit()
            flash("Settings Updated!", "success")
            
    categories = BehavioralCategory.query.all()
    stages_config = AppConfig.query.filter_by(key='total_stages').first()
    return render_template('settings.html', categories=categories, stages=stages_config.value if stages_config else 20)

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
    roll = request.form.get('roll_no')
    if Student.query.filter_by(roll_no=roll).first():
        flash("Roll number already exists!", "danger")
    else:
        new_student = Student(name=name, roll_no=roll)
        db.session.add(new_student)
        db.session.commit()
        flash(f"Student {name} registered!", "success")
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


@app.route('/update_student/<int:id>', methods=['POST'])
def update_student(id):
    student = Student.query.get_or_404(id)
    student.name = request.form.get('name')
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
