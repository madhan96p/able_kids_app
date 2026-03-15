from app import app, db, Student, BehavioralCategory, AppConfig

with app.app_context():
    print("Rebuilding database...")
    db.drop_all()   # This deletes the old tables
    db.create_all() # This creates new tables with the 'gender' column
    
    # 1. Add Default Stages
    db.session.add(AppConfig(key='total_stages', value=20))

    # 2. Add the 20 Random Students
    students_data = [
        ("Arjun Raghavan", "AK-2026-001", "Male"), ("Diya Sengupta", "AK-2026-002", "Female"),
        ("Ishaan Malhotra", "AK-2026-003", "Male"), ("Kavya Krishnan", "AK-2026-004", "Female"),
        ("Rohan Deshmukh", "AK-2026-005", "Male"), ("Ananya Iyer", "AK-2026-006", "Female"),
        ("Vihaan Kulkarni", "AK-2026-007", "Male"), ("Meera Pillai", "AK-2026-008", "Female"),
        ("Aditya Verma", "AK-2026-009", "Male"), ("Sana Mir", "AK-2026-010", "Female"),
        ("Karthik Nair", "AK-2026-011", "Male"), ("Zara Khan", "AK-2026-012", "Female"),
        ("Pranav Joshi", "AK-2026-013", "Male"), ("Navya Reddy", "AK-2026-014", "Female"),
        ("Aryan Saxena", "AK-2026-015", "Male"), ("Tanvi Hegde", "AK-2026-016", "Female"),
        ("Rishi Chauhan", "AK-2026-017", "Male"), ("Myra Kapoor", "AK-2026-018", "Female"),
        ("Devansh Gupta", "AK-2026-019", "Male"), ("Anika Sharma", "AK-2026-020", "Female")
    ]
    
    for name, roll, gen in students_data:
        db.session.add(Student(name=name, roll_no=roll, gender=gen))

    # 3. Add the 18 Categories
    categories = [
        ("Gross Motor", "Physical"), ("Fine Motor", "Physical"), ("Locomotion", "Physical"), ("Occupation", "Physical"),
        ("Eating/Drinking", "Self-Help"), ("Dressing", "Self-Help"), ("Grooming", "Self-Help"), ("Toileting", "Self-Help"), 
        ("Self-Help General", "Self-Help"), ("Communication", "Social"), ("Social Interaction", "Social"), 
        ("Self-Direction", "Social"), ("Socialization", "Social"), ("Reading", "Academic"), ("Writing", "Academic"), 
        ("Numbers", "Academic"), ("Money", "Academic"), ("Time", "Academic")
    ]
    for name, grp in categories:
        db.session.add(BehavioralCategory(name=name, group=grp))

    db.session.commit()
    print("Success! Database reset with 20 students and 18 categories.")