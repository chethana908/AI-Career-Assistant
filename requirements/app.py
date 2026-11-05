from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os, re, io, json
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///career_assistant.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

SKILLS = [
    "Python", "Java", "C", "C++", "C#", "SQL", "HTML", "CSS", "JavaScript",
    "Bootstrap", "Flask", "Django", "React", "Node.js", "Express",
    "Spring", "Git", "GitHub", "MongoDB", "MySQL", "SQLite",
    "Machine Learning", "Deep Learning", "Data Science", "Pandas",
    "NumPy", "TensorFlow", "Power BI", "Excel", "AWS", "Azure",
    "Docker", "REST API", "PHP", "Android", "Kotlin"
]

# Career Gap Analyzer: role requirements are editable project data, not live job-market claims.
ROLE_REQUIREMENTS = {
    "Java Developer": ["Java", "OOP", "Data Structures", "Algorithms", "SQL", "Spring", "REST API", "Git"],
    "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "SQL", "REST API", "Git"],
    "Data Analyst": ["Python", "SQL", "Excel", "Power BI", "Pandas", "Statistics", "Data Visualization"],
    "Python Developer": ["Python", "OOP", "Data Structures", "SQL", "Flask", "REST API", "Git", "Testing"],
}

# Convert common abbreviations and spelling variants to one canonical skill name.
SKILL_ALIASES = {
    "js": "JavaScript", "javascript": "JavaScript",
    "html5": "HTML", "css3": "CSS",
    "node": "Node.js", "nodejs": "Node.js",
    "reactjs": "React", "react.js": "React",
    "postgresql": "SQL", "structured query language": "SQL",
    "restful api": "REST API", "apis": "REST API", "api": "REST API",
    "oops": "OOP", "object oriented programming": "OOP",
    "ds": "Data Structures", "dsa": "Data Structures",
    "powerbi": "Power BI",
    "scikit-learn": "Machine Learning",
}

def canonical_skill(skill):
    value = skill.strip().lower()
    if value in SKILL_ALIASES:
        return SKILL_ALIASES[value]
    for known in SKILLS + ["OOP", "Data Structures", "Algorithms", "Statistics", "Data Visualization", "Testing"]:
        if value == known.lower():
            return known
    return skill.strip()

def analyze_career_gap(user_skills, target_role):
    """Return transparent rule-based skill coverage for a selected target role."""
    required = ROLE_REQUIREMENTS.get(target_role, [])
    normalized_user = {canonical_skill(skill).lower() for skill in user_skills}
    matched = [skill for skill in required if canonical_skill(skill).lower() in normalized_user]
    missing = [skill for skill in required if canonical_skill(skill).lower() not in normalized_user]
    score = round((len(matched) / len(required)) * 100) if required else 0

    learning_steps = {
        "Java": "Revise Java fundamentals, classes, inheritance and collections.",
        "OOP": "Practice encapsulation, inheritance, polymorphism and abstraction.",
        "Data Structures": "Practice arrays, strings, linked lists, stacks, queues and trees.",
        "Algorithms": "Study searching, sorting, recursion and complexity analysis.",
        "SQL": "Practice joins, grouping, subqueries and database design.",
        "Spring": "Build a small REST service using Spring Boot.",
        "REST API": "Build and test CRUD endpoints; learn HTTP methods and status codes.",
        "Git": "Practice branching, commits, merging and GitHub collaboration.",
        "HTML": "Build accessible semantic page structures.",
        "CSS": "Practice responsive layouts, Flexbox and Grid.",
        "JavaScript": "Practice DOM manipulation, async/await and fetch.",
        "React": "Build components, forms, state and API-driven pages.",
        "Node.js": "Build a small server and understand modules and npm.",
        "Python": "Practice functions, collections, modules and file handling.",
        "Flask": "Build routes, templates, forms and database-backed features.",
        "Excel": "Practice formulas, pivot tables and data cleaning.",
        "Power BI": "Create a dashboard with measures and visual filters.",
        "Pandas": "Practice loading, cleaning, grouping and analyzing datasets.",
        "Statistics": "Revise averages, distributions, correlation and sampling.",
        "Data Visualization": "Choose clear charts and explain insights from data.",
        "Testing": "Write unit tests and validate edge cases.",
    }
    roadmap = [{"skill": skill, "action": learning_steps.get(skill, f"Study {skill} and build a small practical exercise.")} for skill in missing]
    return {"role": target_role, "required": required, "matched": matched, "missing": missing,
            "score": score, "roadmap": roadmap}

PROJECT_SUGGESTIONS = {
    "Java": "Build a Student Management System",
    "OOP": "Build a Library Management System",
    "Data Structures": "Build a Contact Search Application",
    "Algorithms": "Build a Sorting Visualizer",
    "SQL": "Build a Student Database Application",
    "Spring": "Build a REST API using Spring Boot",
    "REST API": "Build a CRUD REST API",
    "Git": "Create a collaborative GitHub project",
    "HTML": "Build a responsive portfolio website",
    "CSS": "Build a responsive dashboard",
    "JavaScript": "Build an interactive task manager",
    "React": "Build a React job portal frontend",
    "Node.js": "Build a Node.js backend API",
    "Python": "Build a Python automation tool",
    "Flask": "Build a Flask web application",
    "Excel": "Build an Excel sales report",
    "Power BI": "Build an interactive business dashboard",
    "Pandas": "Build a data cleaning application",
    "Statistics": "Build a statistical data analysis report",
    "Data Visualization": "Build a data visualization dashboard",
    "Testing": "Write automated tests for a web application"
}


def build_personalized_roadmap(analysis):
    roadmap = []

    missing_skills = analysis["missing"]

    for index, item in enumerate(analysis["roadmap"]):

        skill = item["skill"]

        if index < 2:
            priority = "High"
        elif index < 5:
            priority = "Medium"
        else:
            priority = "Low"

        week = (index // 2) + 1

        project = PROJECT_SUGGESTIONS.get(
            skill,
            f"Build a practical project using {skill}"
        )

        roadmap.append({
            "skill": skill,
            "action": item["action"],
            "priority": priority,
            "week": week,
            "project": project
        })

    return roadmap

INTERVIEW_BANK = {
    "Python": [
        ("technical", "What is the difference between a list and a tuple in Python?", ["list", "tuple", "mutable", "immutable"]),
        ("technical", "What is a dictionary in Python?", ["key", "value", "mapping"]),
        ("technical", "What is exception handling in Python?", ["try", "except", "exception"]),
        ("technical", "What is Flask?", ["python", "web", "framework"]),
    ],
    "Java": [
        ("technical", "What is the difference between JDK, JRE and JVM?", ["jdk", "jre", "jvm"]),
        ("technical", "Explain inheritance in Java.", ["inheritance", "class", "parent", "child"]),
        ("technical", "What is an interface in Java?", ["interface", "abstract", "method"]),
    ],
    "SQL": [
        ("technical", "What is a primary key?", ["primary", "unique", "row"]),
        ("technical", "What is the difference between WHERE and HAVING?", ["where", "having", "group"]),
        ("technical", "What is a JOIN?", ["join", "table", "match"]),
    ],
    "HTML": [
        ("technical", "What is the purpose of semantic HTML?", ["semantic", "structure", "html"]),
    ],
    "JavaScript": [
        ("technical", "What is the difference between let, const and var?", ["let", "const", "var"]),
    ],
}

GENERAL_QUESTIONS = [
    ("hr", "Tell me about yourself.", ["education", "skills", "project", "experience"]),
    ("hr", "Why should we hire you?", ["skills", "strength", "value", "learn"]),
    ("hr", "What are your strengths?", ["strength", "skill", "example"]),
    ("hr", "Where do you see yourself in five years?", ["career", "goal", "growth"]),
]

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(255))
    score = db.Column(db.Integer, default=0)
    skills = db.Column(db.Text, default="[]")
    education = db.Column(db.Text, default="")
    experience = db.Column(db.Text, default="")
    suggestions = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    company = db.Column(db.String(120))
    skill = db.Column(db.String(120))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    score = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    location = db.Column(db.String(120))
    skills = db.Column(db.Text, nullable=False)
    experience = db.Column(db.String(80), default="Fresher")
    url = db.Column(db.String(500), default="#")
class LearningTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    role = db.Column(db.String(120), nullable=False)
    skill = db.Column(db.String(120), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    priority = db.Column(db.String(30), nullable=False)
    action = db.Column(db.Text, nullable=False)
    project = db.Column(db.String(255), nullable=False)

    completed = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def extract_pdf_text(path):
    text = ""
    reader = PdfReader(path)
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text

def detect_skills(text):
    # Use word boundaries where possible to avoid false positives such as C in "career".
    found = []
    for skill in SKILLS:
        pattern = r"(?<![A-Za-z0-9+#.])" + re.escape(skill) + r"(?![A-Za-z0-9+#.])"
        if re.search(pattern, text, re.I):
            found.append(skill)
    low = text.lower()
    for alias, canonical in SKILL_ALIASES.items():
        pattern = r"(?<![A-Za-z0-9+#.])" + re.escape(alias) + r"(?![A-Za-z0-9+#.])"
        if re.search(pattern, low, re.I):
            found.append(canonical)
    return sorted(set(found), key=str.lower)

def extract_section(text, keywords):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    matches = []
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in keywords):
            matches.extend(lines[i:i+4])
    return " ".join(dict.fromkeys(matches))[:800]

def calculate_resume_score(text, skills):
    score = 0
    if skills:
        score += min(40, len(skills) * 5)
    if re.search(r"\b(education|b\.?e\.?|bachelor|degree|college|university)\b", text, re.I):
        score += 20
    if re.search(r"\b(experience|internship|work experience)\b", text, re.I):
        score += 15
    if re.search(r"\b(project|projects)\b", text, re.I):
        score += 15
    if re.search(r"\b(email|phone|contact)\b", text, re.I):
        score += 5
    if re.search(r"\b(linkedin|github)\b", text, re.I):
        score += 5
    return min(100, score)

def suggestions_for(text, skills):
    suggestions = []
    checks = [
        (not skills, "Add a clear technical skills section."),
        (not re.search(r"\b(project|projects)\b", text, re.I), "Add academic or personal projects with measurable results."),
        (not re.search(r"\b(experience|internship)\b", text, re.I), "Add internship, training, or relevant experience if available."),
        (not re.search(r"\b(linkedin|github)\b", text, re.I), "Add LinkedIn and GitHub links."),
        (len(text.split()) < 180, "Add more relevant detail while keeping the resume concise."),
    ]
    for condition, message in checks:
        if condition:
            suggestions.append(message)
    return suggestions or ["Your resume covers the main sections. Keep updating skills and project achievements."]

def seed_jobs():
    if Job.query.count():
        return
    jobs = [
        ("TCS", "Python Developer", "Bangalore", "Python, SQL, Flask", "Fresher"),
        ("Infosys", "Java Developer", "Bangalore", "Java, SQL, Spring", "Fresher"),
        ("Accenture", "Full Stack Developer", "Bangalore", "HTML, CSS, JavaScript, React, SQL", "Fresher"),
        ("Wipro", "Software Engineer", "Bangalore", "Java, Python, SQL, Git", "Fresher"),
        ("Deloitte", "Data Analyst", "Bangalore", "Python, SQL, Excel, Power BI", "0-2 years"),
        ("Cognizant", "Web Developer", "Bangalore", "HTML, CSS, JavaScript, Bootstrap", "Fresher"),
        ("Capgemini", "Cloud/Software Engineer", "Bangalore", "Python, Java, AWS, Git", "Fresher"),
    ]
    for c, t, l, s, e in jobs:
        db.session.add(Job(company=c, title=t, location=l, skills=s, experience=e, url="#"))
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_jobs()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if not name or not email or not password:
            flash("All fields are required.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
        else:
            user = User(name=name, email=email, password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).first()
    interviews = Interview.query.filter_by(user_id=current_user.id).order_by(Interview.created_at.desc()).all()
    avg = round(sum(i.score for i in interviews) / len(interviews)) if interviews else 0
    skills = json.loads(resume.skills) if resume else []
    jobs = recommend_jobs(skills)[:3]
    return render_template("dashboard.html", resume=resume, interviews=interviews, avg=avg, skills=skills, jobs=jobs)

@app.route("/resume", methods=["GET", "POST"])
@login_required
def resume_analyzer():
    if request.method == "POST":
        file = request.files.get("resume")
        if not file or not file.filename.lower().endswith(".pdf"):
            flash("Please upload a PDF resume.", "danger")
            return redirect(url_for("resume_analyzer"))
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        try:
            text = extract_pdf_text(path)
        except Exception as e:
            flash("Could not read the PDF. Make sure it is a valid text-based PDF.", "danger")
            return redirect(url_for("resume_analyzer"))

        skills = detect_skills(text)
        score = calculate_resume_score(text, skills)
        education = extract_section(text, ["education", "academic", "degree", "college", "university"])
        experience = extract_section(text, ["experience", "internship", "work experience"])
        suggestions = suggestions_for(text, skills)

        resume = Resume(
            user_id=current_user.id, filename=filename, score=score,
            skills=json.dumps(skills), education=education,
            experience=experience, suggestions=json.dumps(suggestions)
        )
        db.session.add(resume)
        db.session.commit()
        return redirect(url_for("resume_result", resume_id=resume.id))
    return render_template("resume.html")

@app.route("/resume/result/<int:resume_id>")
@login_required
def resume_result(resume_id):
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()
    return render_template(
        "resume_result.html",
        resume=resume,
        skills=json.loads(resume.skills),
        suggestions=json.loads(resume.suggestions)
    )

def recommend_jobs(user_skills):
    user_set = {s.lower().strip() for s in user_skills}
    result = []
    for job in Job.query.all():
        required = [x.strip() for x in job.skills.split(",")]
        required_set = {x.lower() for x in required}
        matched = sorted(user_set.intersection(required_set))
        score = round((len(matched) / len(required_set)) * 100) if required_set else 0
        result.append((job, score, matched))
    return sorted(result, key=lambda x: x[1], reverse=True)

@app.route("/career-gap", methods=["GET", "POST"])
@login_required
def career_gap():
    resume = Resume.query.filter_by(
        user_id=current_user.id
    ).order_by(Resume.created_at.desc()).first()

    skills = json.loads(resume.skills) if resume else []

    selected_role = (
        request.form.get("target_role", "")
        if request.method == "POST"
        else request.args.get("role", "")
    )

    analysis = None
    roadmap_tasks=[]

    if request.method == "POST":
        if not resume:
            flash(
                "Please upload your resume before analyzing your career gap.",
                "warning"
            )
        elif selected_role not in ROLE_REQUIREMENTS:
            flash(
                "Please select a valid target role.",
                "danger"
            )
        else:
            analysis = analyze_career_gap(skills, selected_role)
            roadmap = build_personalized_roadmap(analysis)

            # Replace the previous roadmap for this user and selected role.
            LearningTask.query.filter_by(
                user_id=current_user.id,
                role=selected_role
            ).delete()

            # Save the newly generated roadmap.
            for item in roadmap:
                new_task = LearningTask(
                    user_id=current_user.id,
                    role=selected_role,
                    skill=item["skill"],
                    week=item["week"],
                    priority=item["priority"],
                    action=item["action"],
                    project=item["project"]
                )
                db.session.add(new_task)

            db.session.commit()
            # Recalculate analysis when the page loads or refreshes
    if resume and selected_role in ROLE_REQUIREMENTS:
        analysis = analyze_career_gap(skills, selected_role)

        # Load saved tasks for the selected role.
        if selected_role in ROLE_REQUIREMENTS:
            roadmap_tasks = LearningTask.query.filter_by(
                user_id=current_user.id,
                role=selected_role
            ).order_by(LearningTask.week.asc(), LearningTask.id.asc()).all()
        else:
            roadmap_tasks = []

    total_tasks = len(roadmap_tasks)
    completed_tasks = sum(
        1 for task in roadmap_tasks if task.completed
    )

    roadmap_progress = (
        round((completed_tasks / total_tasks) * 100)
        if total_tasks > 0 else 0
    )

    return render_template(
        "career_gap.html",
        skills=skills,
        roles=list(ROLE_REQUIREMENTS.keys()),
        selected_role=selected_role,
        analysis=analysis,
        has_resume=bool(resume),
        latest_resume=resume,
        roadmap_tasks=roadmap_tasks,
        roadmap_progress=roadmap_progress
)


@app.route("/career-gap/toggle-task/<int:task_id>", methods=["POST"])
@login_required
def toggle_roadmap_task(task_id):
    task = LearningTask.query.filter_by(
        id=task_id,
        user_id=current_user.id
    ).first_or_404()

    task.completed = not task.completed
    db.session.commit()

    flash("Roadmap progress updated!", "success")
    return redirect(url_for("career_gap", role=task.role))


@app.route("/career-gap/delete-resume", methods=["POST"])
@login_required
def career_gap_delete_resume():

    resume = Resume.query.filter_by(
        user_id=current_user.id
    ).order_by(Resume.created_at.desc()).first()

    if not resume:
        flash("No saved resume was found.", "warning")
        return redirect(url_for("career_gap"))

    filename = resume.filename

    # Delete the database record belonging to this user.
    db.session.delete(resume)
    db.session.commit()

    # Delete the physical file only if no other record uses it.
    if filename:
        other_record = Resume.query.filter_by(
            filename=filename
        ).first()

        if not other_record:
            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            if os.path.isfile(filepath):
                os.remove(filepath)

    flash("Your latest saved resume has been deleted.", "success")
    return redirect(url_for("career_gap"))

@app.route("/jobs")
@login_required
def jobs():
    resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).first()
    skills = json.loads(resume.skills) if resume else []
    recommendations = recommend_jobs(skills)
    return render_template("jobs.html", skills=skills, recommendations=recommendations)

@app.route("/interview", methods=["GET", "POST"])
@login_required
def interview():
    resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).first()
    resume_skills = json.loads(resume.skills) if resume else []
    if request.method == "POST":
        company = request.form["company"]
        skill = request.form["skill"]
        category = request.form["category"]
        if skill in INTERVIEW_BANK:
            pool = [q for q in INTERVIEW_BANK[skill] if q[0] == category]
            if not pool:
                pool = INTERVIEW_BANK[skill]
        else:
            pool = GENERAL_QUESTIONS
        qtype, question, keywords = pool[0]
        return render_template("interview_question.html", company=company, skill=skill,
                               question=question, keywords=keywords)
    skills = resume_skills or ["Python", "Java", "SQL", "HTML", "JavaScript"]
    return render_template("interview.html", skills=skills)

@app.route("/interview/submit", methods=["POST"])
@login_required
def submit_interview():
    company = request.form["company"]
    skill = request.form["skill"]
    question = request.form["question"]
    answer = request.form["answer"].strip()
    keywords = json.loads(request.form["keywords"])
    low = answer.lower()
    matched = [k for k in keywords if k.lower() in low]
    score = min(10, round((len(matched) / max(1, len(keywords))) * 10))
    if not answer:
        score = 0
        feedback = "No answer was submitted. Try answering the question in your own words."
    elif score >= 8:
        feedback = "Excellent answer. You covered the important concepts."
    elif score >= 5:
        feedback = "Good attempt. Add more technical details and an example."
    else:
        feedback = "Keep practicing. Explain the core concept, terminology, and a small example."

    record = Interview(user_id=current_user.id, company=company, skill=skill,
                      question=question, answer=answer, score=score, feedback=feedback)
    db.session.add(record)
    db.session.commit()
    return render_template("interview_result.html", record=record, matched=matched)

@app.route("/report/<int:resume_id>")
@login_required
def report(resume_id):
    resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first_or_404()
    skills = json.loads(resume.skills)
    suggestions = json.loads(resume.suggestions)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("AI Career Assistant - Resume Analysis Report", styles["Title"]),
        Spacer(1, 15),
        Paragraph(f"<b>Candidate:</b> {current_user.name}", styles["Normal"]),
        Paragraph(f"<b>Resume Score:</b> {resume.score}%", styles["Heading2"]),
        Spacer(1, 10),
        Paragraph("Detected Skills", styles["Heading2"]),
        Paragraph(", ".join(skills) if skills else "No skills detected", styles["Normal"]),
        Spacer(1, 10),
        Paragraph("Education", styles["Heading2"]),
        Paragraph(resume.education or "Not detected", styles["Normal"]),
        Spacer(1, 10),
        Paragraph("Experience", styles["Heading2"]),
        Paragraph(resume.experience or "Not detected", styles["Normal"]),
        Spacer(1, 10),
        Paragraph("Suggestions", styles["Heading2"]),
    ]
    for s in suggestions:
        story.append(Paragraph("• " + s, styles["Normal"]))
    story += [Spacer(1, 12), Paragraph("Recommended Jobs", styles["Heading2"])]
    data = [["Company", "Role", "Location", "Match"]]
    for job, score, matched in recommend_jobs(skills)[:5]:
        data.append([job.company, job.title, job.location, f"{score}%"])
    table = Table(data, colWidths=[90, 150, 90, 60])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story += [table]
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="resume_analysis_report.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
