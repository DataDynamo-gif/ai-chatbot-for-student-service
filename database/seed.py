import json
from datetime import date, datetime
import os
import sys

# Ensure project root is in path at priority 0
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import SessionLocal, init_db, engine
from database.models import (
    Student, Subject, Attendance, Timetable, Result, Fee,
    Notice, Placement, LibraryBook, Complaint, FAQ
)


def seed_database():
    """
    Initializes database tables and seeds realistic data for all modules.
    Safe to re-run: checks existence before seeding.
    """
    init_db()
    db = SessionLocal()

    try:
        # 1. Seed Students & Admin
        if not db.query(Student).first():
            students_data = [
                Student(
                    student_id="S101",
                    password="password123",
                    name="Aarav Sharma",
                    roll_number="CS2023001",
                    department="Computer Science",
                    semester=6,
                    section="A",
                    email="aarav.sharma@college.edu",
                    phone="+91-9876543210",
                    is_admin=False
                ),
                Student(
                    student_id="S102",
                    password="password123",
                    name="Diya Patel",
                    roll_number="CS2023002",
                    department="Computer Science",
                    semester=6,
                    section="A",
                    email="diya.patel@college.edu",
                    phone="+91-9876543211",
                    is_admin=False
                ),
                Student(
                    student_id="S103",
                    password="password123",
                    name="Rohan Verma",
                    roll_number="CS2023003",
                    department="Computer Science",
                    semester=6,
                    section="A",
                    email="rohan.verma@college.edu",
                    phone="+91-9876543212",
                    is_admin=False
                ),
                Student(
                    student_id="admin",
                    password="admin123",
                    name="System Administrator",
                    roll_number="ADM001",
                    department="Administration",
                    semester=0,
                    section="N/A",
                    email="admin@college.edu",
                    phone="+91-0000000000",
                    is_admin=True
                )
            ]
            db.add_all(students_data)
            db.commit()
            print("Successfully seeded Students and Admin account.")

        # 2. Seed Subjects
        if not db.query(Subject).first():
            subjects_data = [
                Subject(code="CS601", name="Database Management Systems (DBMS)", department="Computer Science", semester=6),
                Subject(code="CS602", name="Artificial Intelligence & ML", department="Computer Science", semester=6),
                Subject(code="CS603", name="Computer Networks", department="Computer Science", semester=6),
                Subject(code="CS604", name="Operating Systems", department="Computer Science", semester=6),
                Subject(code="CS605", name="Cloud Computing & DevOps", department="Computer Science", semester=6),
            ]
            db.add_all(subjects_data)
            db.commit()
            print("Successfully seeded Subjects.")

        # 3. Seed Attendance (including below 75% for testing highlight)
        if not db.query(Attendance).first():
            dbms = db.query(Subject).filter_by(code="CS601").first()
            ai = db.query(Subject).filter_by(code="CS602").first()
            cn = db.query(Subject).filter_by(code="CS603").first()
            os_sub = db.query(Subject).filter_by(code="CS604").first()
            cloud = db.query(Subject).filter_by(code="CS605").first()

            attendance_data = [
                # Aarav Sharma (S101)
                Attendance(student_id="S101", subject_id=dbms.id, classes_attended=38, total_classes=42),   # 90.48%
                Attendance(student_id="S101", subject_id=ai.id, classes_attended=28, total_classes=40),     # 70.00% (BELOW 75%)
                Attendance(student_id="S101", subject_id=cn.id, classes_attended=35, total_classes=40),     # 87.50%
                Attendance(student_id="S101", subject_id=os_sub.id, classes_attended=26, total_classes=38), # 68.42% (BELOW 75%)
                Attendance(student_id="S101", subject_id=cloud.id, classes_attended=40, total_classes=42),  # 95.24%

                # Diya Patel (S102)
                Attendance(student_id="S102", subject_id=dbms.id, classes_attended=40, total_classes=42),
                Attendance(student_id="S102", subject_id=ai.id, classes_attended=38, total_classes=40),
                Attendance(student_id="S102", subject_id=cn.id, classes_attended=39, total_classes=40),
                Attendance(student_id="S102", subject_id=os_sub.id, classes_attended=36, total_classes=38),
                Attendance(student_id="S102", subject_id=cloud.id, classes_attended=41, total_classes=42),
            ]
            db.add_all(attendance_data)
            db.commit()
            print("Successfully seeded Attendance records.")

        # 4. Seed Timetable
        if not db.query(Timetable).first():
            dbms = db.query(Subject).filter_by(code="CS601").first()
            ai = db.query(Subject).filter_by(code="CS602").first()
            cn = db.query(Subject).filter_by(code="CS603").first()
            os_sub = db.query(Subject).filter_by(code="CS604").first()
            cloud = db.query(Subject).filter_by(code="CS605").first()

            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            timetable_data = [
                # Monday
                Timetable(department="Computer Science", semester=6, day_of_week="Monday", period_number=1, start_time="09:00 AM", end_time="10:00 AM", subject_id=dbms.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Monday", period_number=2, start_time="10:00 AM", end_time="11:00 AM", subject_id=ai.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Monday", period_number=3, start_time="11:15 AM", end_time="12:15 PM", subject_id=None, room_number="Library (Free Period)"),
                Timetable(department="Computer Science", semester=6, day_of_week="Monday", period_number=4, start_time="01:30 PM", end_time="02:30 PM", subject_id=cn.id, room_number="LT-102"),

                # Tuesday
                Timetable(department="Computer Science", semester=6, day_of_week="Tuesday", period_number=1, start_time="09:00 AM", end_time="10:00 AM", subject_id=os_sub.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Tuesday", period_number=2, start_time="10:00 AM", end_time="11:00 AM", subject_id=cloud.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Tuesday", period_number=3, start_time="11:15 AM", end_time="12:15 PM", subject_id=dbms.id, room_number="Lab-1 (Practical)"),
                Timetable(department="Computer Science", semester=6, day_of_week="Tuesday", period_number=4, start_time="01:30 PM", end_time="02:30 PM", subject_id=None, room_number="Free Period"),

                # Wednesday
                Timetable(department="Computer Science", semester=6, day_of_week="Wednesday", period_number=1, start_time="09:00 AM", end_time="10:00 AM", subject_id=ai.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Wednesday", period_number=2, start_time="10:00 AM", end_time="11:00 AM", subject_id=cn.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Wednesday", period_number=3, start_time="11:15 AM", end_time="12:15 PM", subject_id=os_sub.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Wednesday", period_number=4, start_time="01:30 PM", end_time="02:30 PM", subject_id=cloud.id, room_number="LT-103"),

                # Thursday
                Timetable(department="Computer Science", semester=6, day_of_week="Thursday", period_number=1, start_time="09:00 AM", end_time="10:00 AM", subject_id=dbms.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Thursday", period_number=2, start_time="10:00 AM", end_time="11:00 AM", subject_id=None, room_number="Free Period"),
                Timetable(department="Computer Science", semester=6, day_of_week="Thursday", period_number=3, start_time="11:15 AM", end_time="12:15 PM", subject_id=ai.id, room_number="LT-102"),
                Timetable(department="Computer Science", semester=6, day_of_week="Thursday", period_number=4, start_time="01:30 PM", end_time="02:30 PM", subject_id=cn.id, room_number="LT-102"),

                # Friday
                Timetable(department="Computer Science", semester=6, day_of_week="Friday", period_number=1, start_time="09:00 AM", end_time="10:00 AM", subject_id=os_sub.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Friday", period_number=2, start_time="10:00 AM", end_time="11:00 AM", subject_id=cloud.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Friday", period_number=3, start_time="11:15 AM", end_time="12:15 PM", subject_id=dbms.id, room_number="LT-101"),
                Timetable(department="Computer Science", semester=6, day_of_week="Friday", period_number=4, start_time="01:30 PM", end_time="02:30 PM", subject_id=None, room_number="Free Period"),
            ]
            db.add_all(timetable_data)
            db.commit()
            print("Successfully seeded Timetable.")

        # 5. Seed Results
        if not db.query(Result).first():
            s101_marks = [
                {"subject": "DBMS", "code": "CS601", "marks": 88, "grade": "A"},
                {"subject": "AI & ML", "code": "CS602", "marks": 74, "grade": "B+"},
                {"subject": "Computer Networks", "code": "CS603", "marks": 82, "grade": "A-"},
                {"subject": "Operating Systems", "code": "CS604", "marks": 68, "grade": "B"},
                {"subject": "Cloud Computing", "code": "CS605", "marks": 91, "grade": "O"}
            ]
            s102_marks = [
                {"subject": "DBMS", "code": "CS601", "marks": 94, "grade": "O"},
                {"subject": "AI & ML", "code": "CS602", "marks": 89, "grade": "A"},
                {"subject": "Computer Networks", "code": "CS603", "marks": 90, "grade": "O"},
                {"subject": "Operating Systems", "code": "CS604", "marks": 85, "grade": "A"},
                {"subject": "Cloud Computing", "code": "CS605", "marks": 92, "grade": "O"}
            ]
            results_data = [
                Result(student_id="S101", semester=6, sgpa=8.45, cgpa=8.20, backlogs=0, subject_marks_json=json.dumps(s101_marks)),
                Result(student_id="S102", semester=6, sgpa=9.60, cgpa=9.45, backlogs=0, subject_marks_json=json.dumps(s102_marks)),
            ]
            db.add_all(results_data)
            db.commit()
            print("Successfully seeded Results.")

        # 6. Seed Fees
        if not db.query(Fee).first():
            fees_data = [
                Fee(student_id="S101", semester=6, paid_amount=75000.0, pending_amount=15000.0, due_date="2026-08-15", receipt_number="REC-2026-8941"),
                Fee(student_id="S102", semester=6, paid_amount=90000.0, pending_amount=0.0, due_date="Paid in Full", receipt_number="REC-2026-8942"),
                Fee(student_id="S103", semester=6, paid_amount=45000.0, pending_amount=45000.0, due_date="2026-08-15", receipt_number="REC-2026-8943"),
            ]
            db.add_all(fees_data)
            db.commit()
            print("Successfully seeded Fees.")

        # 7. Seed Notices
        if not db.query(Notice).first():
            notices_data = [
                Notice(title="Mid-Semester Exam Schedule Announced", content="Mid-semester examinations for Semester 6 will commence on October 12th. Check timetable on student portal.", date_posted=date(2026, 7, 10), category="Exam"),
                Notice(title="Annual Tech Symposium 'Srijan 2026'", content="Registration is now open for campus hackathon and robotics competition. Attractive prize pool up to INR 1,50,000.", date_posted=date(2026, 7, 14), category="Event"),
                Notice(title="Library Card Renewal Notice", content="All students must get their barcoded library ID cards verified and stamped before July 31st at the central counter.", date_posted=date(2026, 7, 15), category="Academic"),
                Notice(title="Hostel Night Gate Curfew Update", content="Effective immediately, main hostel gates will close strictly at 10:00 PM on weekdays and 10:30 PM on weekends.", date_posted=date(2026, 7, 16), category="General"),
            ]
            db.add_all(notices_data)
            db.commit()
            print("Successfully seeded Notices.")

        # 8. Seed Placements
        if not db.query(Placement).first():
            placements_data = [
                Placement(company="Google India", role="Software Engineer (Full Stack)", package_lpa=32.5, eligibility_criteria="CGPA >= 8.0, No backlogs, CS/IT branch", deadline="2026-08-10", description="Full-time software engineering role in Bengaluru/Hyderabad offices. Selection includes coding assessments and 3 technical rounds."),
                Placement(company="Microsoft", role="Cloud AI Developer", package_lpa=28.0, eligibility_criteria="CGPA >= 7.5, No active backlogs", deadline="2026-08-14", description="Work on Azure AI and Copilot integration teams. Excellent programming fundamentals in Python/C++ required."),
                Placement(company="TCS Digital", role="Systems Engineer", package_lpa=7.5, eligibility_criteria="CGPA >= 6.5, Max 1 backlog allowed", deadline="2026-08-25", description="Pan-India digital technology projects. Online aptitude test followed by technical interview."),
                Placement(company="Atlassian", role="Backend Engineer Intern + PPO", package_lpa=42.0, eligibility_criteria="CGPA >= 8.5, CS/IT/ECE branches", deadline="2026-08-05", description="High-impact backend engineering role working on Jira/Confluence core architecture."),
            ]
            db.add_all(placements_data)
            db.commit()
            print("Successfully seeded Placements.")

        # 9. Seed Library
        if not db.query(LibraryBook).first():
            library_data = [
                LibraryBook(title="Database System Concepts", author="Abraham Silberschatz, Henry F. Korth", isbn="9780073523323", is_available=False, issued_to_student_id="S101", due_date="2026-07-28", fine_amount=0.0),
                LibraryBook(title="Artificial Intelligence: A Modern Approach", author="Stuart Russell, Peter Norvig", isbn="9780134610993", is_available=False, issued_to_student_id="S101", due_date="2026-07-10", fine_amount=35.0), # Overdue with fine
                LibraryBook(title="Clean Code: A Handbook of Agile Software Craftsmanship", author="Robert C. Martin", isbn="9780132350884", is_available=True, issued_to_student_id=None, due_date=None, fine_amount=0.0),
                LibraryBook(title="Introduction to Algorithms (CLRS)", author="Thomas H. Cormen, Charles E. Leiserson", isbn="9780262033848", is_available=True, issued_to_student_id=None, due_date=None, fine_amount=0.0),
                LibraryBook(title="Computer Networking: A Top-Down Approach", author="James F. Kurose, Keith W. Ross", isbn="9780133594140", is_available=True, issued_to_student_id=None, due_date=None, fine_amount=0.0),
            ]
            db.add_all(library_data)
            db.commit()
            print("Successfully seeded Library Books.")

        # 10. Seed Complaints
        if not db.query(Complaint).first():
            complaints_data = [
                Complaint(complaint_id="CMP-2026-0001", student_id="S101", category="Infrastructure", description="Projector in Lecture Theatre 101 has flickering display issues during DBMS class.", priority="High", status="In Progress", date_submitted=date(2026, 7, 12)),
                Complaint(complaint_id="CMP-2026-0002", student_id="S101", category="Hostel", description="Wi-Fi connectivity on the 3rd floor of Boys Hostel B is very slow after 9 PM.", priority="Normal", status="Open", date_submitted=date(2026, 7, 15)),
            ]
            db.add_all(complaints_data)
            db.commit()
            print("Successfully seeded Complaints.")

        # 11. Seed FAQ
        if not db.query(FAQ).first():
            faqs_data = [
                FAQ(question="What are the library timings during regular days and exam weeks?", answer="The Central Library is open from 8:00 AM to 8:00 PM on regular weekdays. During exam months, the reading halls remain open 24x7 for student access.", category="Library"),
                FAQ(question="What is the minimum attendance policy required to sit for semester exams?", answer="As per university guidelines, students must maintain at least 75% attendance in every individual theory and practical course. Medical leaves may allow condonation up to 65% with valid documentation submitted to the HOD.", category="Attendance"),
                FAQ(question="What rules apply during end-semester examinations?", answer="Students must carry their valid barcoded Student ID card and Hall Ticket. Mobile phones, smartwatches, and programmable calculators are strictly prohibited inside the examination hall. Entry after 15 minutes of exam commencement is disallowed.", category="Exam"),
                FAQ(question="What are the hostel entry and exit timings?", answer="Regular hostel gates close at 10:00 PM. For late entry due to academic projects or lab work, prior written permission signed by your faculty guide or warden must be shown at the gate.", category="Hostel"),
                FAQ(question="How can I apply for merit-cum-means campus scholarships?", answer="Scholarship application portals open every August on the university website. Students with CGPA >= 8.5 and family annual income below INR 5,00,000 can submit their income certificates and marksheets online.", category="Scholarship"),
            ]
            db.add_all(faqs_data)
            db.commit()
            print("Successfully seeded FAQs.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing and seeding database...")
    seed_database()
    print("Database initialization complete!")
