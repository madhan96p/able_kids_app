from app import app, db, Student, BehavioralCategory, AppConfig, Batch

with app.app_context():
    print("Precision Rebuild: Flushing and recreating tables...")
    db.drop_all()
    db.create_all()

    # 1. Add App Configuration
    db.session.add(AppConfig(key='total_stages', value=20))

    # 2. Add Standard Batches and create a mapping dictionary
    batch_names = ["Pre-Primary I", "Pre-Primary II",
                   "Primary-I", "Primary-II", "Secondary", "Pre-Vocational"]
    batch_map = {}
    for name in batch_names:
        b = Batch(name=name)
        db.session.add(b)
        db.session.flush()  # This generates the ID so we can use it immediately
        batch_map[name] = b.id

    # 3. Add 20 Students with specific Batch assignment
    students_data = [
        ("Arjun Raghavan", "AK-2026-001", "Male", "Pre-Primary I"),
        ("Diya Sengupta", "AK-2026-002", "Female", "Pre-Primary I"),
        ("Ishaan Malhotra", "AK-2026-003", "Male", "Pre-Primary II"),
        ("Kavya Krishnan", "AK-2026-004", "Female", "Pre-Primary II"),
        ("Rohan Deshmukh", "AK-2026-005", "Male", "Primary-I"),
        ("Ananya Iyer", "AK-2026-006", "Female", "Primary-I"),
        ("Vihaan Kulkarni", "AK-2026-007", "Male", "Primary-I"),
        ("Meera Pillai", "AK-2026-008", "Female", "Primary-II"),
        ("Aditya Verma", "AK-2026-009", "Male", "Primary-II"),
        ("Sana Mir", "AK-2026-010", "Female", "Primary-II"),
        ("Karthik Nair", "AK-2026-011", "Male", "Secondary"),
        ("Zara Khan", "AK-2026-012", "Female", "Secondary"),
        ("Pranav Joshi", "AK-2026-013", "Male", "Secondary"),
        ("Navya Reddy", "AK-2026-014", "Female", "Secondary"),
        ("Aryan Saxena", "AK-2026-015", "Male", "Pre-Vocational"),
        ("Tanvi Hegde", "AK-2026-016", "Female", "Pre-Vocational"),
        ("Rishi Chauhan", "AK-2026-017", "Male", "Pre-Vocational"),
        ("Myra Kapoor", "AK-2026-018", "Female", "Pre-Vocational"),
        ("Devansh Gupta", "AK-2026-019", "Male", "Primary-I"),
        ("Anika Sharma", "AK-2026-020", "Female", "Pre-Primary I")
    ]

    for name, roll, gen, b_name in students_data:
        student = Student(
            name=name,
            roll_no=roll,
            gender=gen,
            batch_id=batch_map[b_name]  # Links the student to the Batch ID
        )
        db.session.add(student)

    # 4. Add the 18 Behavioral Categories
    categories = [
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

    for cat_name, cat_group in categories:
        db.session.add(BehavioralCategory(name=cat_name, group=cat_group))

    db.session.commit()
    print("Database Rebuild Complete! Batch relationships established.")
