from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "able_kids_secret_key"

# 1. Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///able_kids.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 2. Database Models


class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    students = db.relationship('Student', backref='batch_group', lazy=True)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True)
    gender = db.Column(db.String(10))
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=True)
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


class BehavioralCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(50))


class AppConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True)
    value = db.Column(db.Integer)

# 3. Global Context


@app.context_processor
def inject_global_vars():
    config = AppConfig.query.filter_by(key='total_stages').first()
    stages = config.value if config else 20
    all_batches = Batch.query.order_by(Batch.name).all()
    all_cats = BehavioralCategory.query.all()
    return dict(total_stages=stages, batches_list=all_batches, cat_count=len(all_cats))

# 4. Routes


@app.route('/')
def index():
    # Get student_id from the URL if it exists (e.g., /?student_id=20)
    prefilled_student_id = request.args.get('student_id', type=int)

    students = Student.query.all()
    batches = Batch.query.all()

    # Get config for stages
    config = AppConfig.query.filter_by(key='total_stages').first()
    total_stages = config.value if config else 20

    return render_template('index.html',
                           students=students,
                           batches_list=batches,
                           total_stages=total_stages,
                           prefilled_student_id=prefilled_student_id)


@app.route('/add_activity', methods=['POST'])
def add_activity():
    try:
        # CRITICAL: Convert to int so the Database recognizes the Foreign Key
        s_id = int(request.form.get('student_id'))
        cat = request.form.get('category')
        stg = int(request.form.get('stage'))
        nts = request.form.get('notes')

        new_activity = DailyActivity(
            student_id=s_id,
            category=cat,
            stage=stg,
            notes=nts,
            date_logged=datetime.now()
        )
        db.session.add(new_activity)
        db.session.commit()
        flash("Progress recorded successfully!", "success")
        return redirect(url_for('view_student', student_id=s_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('index'))

# --- Activity Record Management (Edit/Update/Delete) ---


@app.route('/edit/<int:record_id>')
def edit_record(record_id):
    record = DailyActivity.query.get_or_404(record_id)
    # total_stages is handled by your inject_global_vars context processor
    return render_template('edit_record.html', record=record)


@app.route('/update/<int:record_id>', methods=['POST'])
def update_record(record_id):
    try:
        record = DailyActivity.query.get_or_404(record_id)
        # Category is usually read-only, but we update stage and notes
        record.stage = int(request.form.get('stage'))
        record.notes = request.form.get('notes')

        db.session.commit()
        flash("Activity record updated successfully!", "info")
        return redirect(url_for('view_student', student_id=record.student_id))
    except Exception as e:
        db.session.rollback()
        flash(f"Update failed: {str(e)}", "danger")
        return redirect(url_for('dashboard'))


@app.route('/delete_record/<int:id>')
def delete_record(id):
    record = DailyActivity.query.get_or_404(id)
    s_id = record.student_id  # Save ID to redirect back to the correct student
    db.session.delete(record)
    db.session.commit()
    flash("Record deleted.", "warning")
    # Redirect back to the page the user came from (Dashboard or Student View)
    return redirect(request.referrer or url_for('view_student', student_id=s_id))


@app.route('/student/<int:student_id>')
def view_student(student_id):
    student = Student.query.get_or_404(student_id)
    # Fetch activities and name the variable 'records' to match your HTML
    student_records = DailyActivity.query.filter_by(
        student_id=student_id).order_by(DailyActivity.date_logged.desc()).all()

    # Also fetch the total stages for the progress bar calculation
    config = AppConfig.query.filter_by(key='total_stages').first()
    total_stages = int(config.value) if config else 20

    return render_template('student_view.html',
                           student=student,
                           records=student_records,
                           total_stages=total_stages)


@app.route('/students')
def manage_students():
    all_students = Student.query.order_by(Student.name).all()
    return render_template('manage_students.html', students=all_students)


@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form.get('name')
    roll_no = request.form.get('roll_no')
    gender = request.form.get('gender')
    batch_id = request.form.get('batch_id')

    if name and roll_no:
        new_student = Student(name=name, roll_no=roll_no,
                              gender=gender, batch_id=batch_id)
        db.session.add(new_student)
        db.session.commit()
        flash(f"Student {name} registered!", "success")
    return redirect(url_for('manage_students'))


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        new_stages = request.form.get('total_stages')
        config = AppConfig.query.filter_by(key='total_stages').first()
        if config:
            config.value = int(new_stages)
        else:
            db.session.add(
                AppConfig(key='total_stages', value=int(new_stages)))
        db.session.commit()
        flash("Configuration updated!", "success")

    categories = BehavioralCategory.query.all()
    return render_template('settings.html', categories=categories)


@app.route('/settings/add_batch', methods=['POST'])
def add_batch():
    name = request.form.get('batch_name')
    if name:
        if not Batch.query.filter_by(name=name).first():
            db.session.add(Batch(name=name))
            db.session.commit()
            flash(f"Batch '{name}' added!", "success")
    return redirect(url_for('settings'))


@app.route('/settings/delete_batch/<int:id>')
def delete_batch(id):
    batch = Batch.query.get_or_404(id)
    if batch.students:
        flash("Cannot delete batch with active students!", "danger")
    else:
        db.session.delete(batch)
        db.session.commit()
        flash("Batch deleted.", "info")
    return redirect(url_for('settings'))


@app.route('/dashboard')
def dashboard():
    activities = DailyActivity.query.order_by(
        DailyActivity.date_logged.desc()).all()
    return render_template('dashboard.html', activities=activities)


@app.route('/delete_student/<int:id>')
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("Student record removed.", "warning")
    return redirect(url_for('manage_students'))


@app.route('/edit_student/<int:id>')
def edit_student(id):
    student = Student.query.get_or_404(id)
    return render_template('edit_student.html', student=student)


@app.route('/update_student/<int:id>', methods=['POST'])
def update_student(id):
    student = Student.query.get_or_404(id)
    student.name = request.form.get('name')
    student.roll_no = request.form.get('roll_no')
    student.gender = request.form.get('gender')
    student.batch_id = request.form.get('batch_id')
    db.session.commit()
    flash("Profile Updated Successfully!", "success")
    return redirect(url_for('manage_students'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
