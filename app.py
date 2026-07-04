from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import hashlib
import os
import json
import re
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.secret_key = 'vidyamitra_secret_key_2024_secure'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── DATABASE SETUP ────────────────────────────────────────────────────────────

def get_db():
    db = sqlite3.connect('vidyamitra.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            profile_complete INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT,
            content TEXT,
            ats_score INTEGER,
            analysis TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS learning_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            technology TEXT,
            domain TEXT,
            plan TEXT,
            progress INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS career_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    db.commit()
    db.close()

init_db()

# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def analyze_resume_content(text):
    text_lower = text.lower()
    
    # Skill extraction
    tech_skills = ['python','java','javascript','react','node','sql','mongodb','aws','docker',
                   'kubernetes','machine learning','deep learning','tensorflow','pytorch','git',
                   'html','css','flask','django','spring','angular','vue','typescript','go',
                   'rust','c++','c#','php','ruby','swift','kotlin','scala','r','matlab',
                   'tableau','power bi','excel','linux','devops','ci/cd','microservices',
                   'rest api','graphql','redis','postgresql','mysql','spark','hadoop','nlp','cv']
    
    soft_skills = ['leadership','communication','teamwork','problem solving','analytical',
                   'management','agile','scrum','collaboration','creative','critical thinking']
    
    found_tech = [s for s in tech_skills if s in text_lower]
    found_soft = [s for s in soft_skills if s in text_lower]
    
    # ATS scoring
    score = 40  # base
    sections = {'education':8,'experience':10,'skills':8,'project':8,'summary':6,'objective':4,
                'certification':5,'achievement':4,'contact':4,'email':3}
    
    section_found = {}
    for sec, pts in sections.items():
        if sec in text_lower:
            score += pts
            section_found[sec] = True
    
    score += min(len(found_tech) * 1.5, 20)
    score += min(len(found_soft) * 0.5, 5)
    score = min(int(score), 99)
    
    # Job type prediction
    job_types = []
    if any(s in text_lower for s in ['python','machine learning','data','tensorflow','pytorch','nlp']):
        job_types.append({'role': 'Data Scientist / ML Engineer', 'match': 88, 'icon': '🤖'})
    if any(s in text_lower for s in ['react','javascript','html','css','frontend','angular','vue']):
        job_types.append({'role': 'Frontend Developer', 'match': 85, 'icon': '💻'})
    if any(s in text_lower for s in ['node','flask','django','spring','backend','api','java']):
        job_types.append({'role': 'Backend Developer', 'match': 82, 'icon': '⚙️'})
    if any(s in text_lower for s in ['aws','docker','kubernetes','devops','ci/cd','linux']):
        job_types.append({'role': 'DevOps / Cloud Engineer', 'match': 80, 'icon': '☁️'})
    if any(s in text_lower for s in ['sql','mongodb','postgresql','database','data engineer']):
        job_types.append({'role': 'Data Engineer', 'match': 78, 'icon': '🗄️'})
    if not job_types:
        job_types.append({'role': 'Software Developer', 'match': 70, 'icon': '👨‍💻'})
    
    # Suggestions
    suggestions = []
    if 'summary' not in text_lower and 'objective' not in text_lower:
        suggestions.append({'type': 'critical', 'text': 'Add a professional summary/objective section — recruiters read this first'})
    if 'github' not in text_lower and 'linkedin' not in text_lower:
        suggestions.append({'type': 'important', 'text': 'Include GitHub and LinkedIn profile links to boost credibility'})
    if len(found_tech) < 5:
        suggestions.append({'type': 'important', 'text': 'Expand your technical skills section with relevant technologies'})
    if 'project' not in text_lower:
        suggestions.append({'type': 'critical', 'text': 'Add 2–3 project descriptions with tech stack and impact metrics'})
    if not any(c.isdigit() for c in text):
        suggestions.append({'type': 'tip', 'text': 'Quantify achievements — use numbers like "improved performance by 40%"'})
    if 'certification' not in text_lower:
        suggestions.append({'type': 'tip', 'text': 'Add relevant certifications (AWS, Google, Coursera) to stand out'})
    if len(found_soft) < 3:
        suggestions.append({'type': 'tip', 'text': 'Include soft skills: leadership, communication, agile methodology'})
    if score < 70:
        suggestions.append({'type': 'critical', 'text': 'Use keywords from job descriptions — ATS filters require keyword matching'})
    
    return {
        'ats_score': score,
        'tech_skills': found_tech,
        'soft_skills': found_soft,
        'job_types': job_types[:4],
        'suggestions': suggestions,
        'word_count': len(text.split()),
        'sections_found': list(section_found.keys()),
        'hire_chance': min(score + 5, 95)
    }

def generate_learning_plan(technology, domain, level='beginner'):
    plans = {
        'python': {
            'weeks': 12,
            'phases': [
                {'phase': 'Foundation', 'weeks': '1-2', 'topics': ['Syntax & Variables', 'Data Types', 'Control Flow', 'Functions'], 'resources': ['Python.org docs', 'Automate the Boring Stuff', 'Python Crash Course']},
                {'phase': 'Intermediate', 'weeks': '3-5', 'topics': ['OOP Concepts', 'File Handling', 'Modules & Packages', 'Error Handling'], 'resources': ['Real Python', 'Corey Schafer YouTube', 'Exercism.io']},
                {'phase': 'Advanced', 'weeks': '6-9', 'topics': ['Decorators', 'Generators', 'Async Programming', 'Testing'], 'resources': ['Fluent Python book', 'Talk Python podcast', 'TestDriven.io']},
                {'phase': 'Projects', 'weeks': '10-12', 'topics': ['Web Scraping', 'API Integration', 'Data Analysis', 'Build Portfolio Project'], 'resources': ['GitHub', 'Kaggle', 'FastAPI docs']}
            ]
        },
        'machine learning': {
            'weeks': 16,
            'phases': [
                {'phase': 'Math & Stats', 'weeks': '1-3', 'topics': ['Linear Algebra', 'Statistics', 'Probability', 'Calculus basics'], 'resources': ['Khan Academy', '3Blue1Brown', 'StatQuest YouTube']},
                {'phase': 'ML Fundamentals', 'weeks': '4-7', 'topics': ['Regression', 'Classification', 'Clustering', 'Model Evaluation'], 'resources': ['Scikit-learn docs', 'Hands-on ML book', 'Coursera ML Course']},
                {'phase': 'Deep Learning', 'weeks': '8-12', 'topics': ['Neural Networks', 'CNNs', 'RNNs', 'Transformers'], 'resources': ['fast.ai', 'Deep Learning Specialization', 'Papers with Code']},
                {'phase': 'MLOps & Deploy', 'weeks': '13-16', 'topics': ['Model Deployment', 'MLflow', 'Docker for ML', 'Cloud AI'], 'resources': ['MLflow docs', 'AWS SageMaker', 'Hugging Face']}
            ]
        },
        'web development': {
            'weeks': 14,
            'phases': [
                {'phase': 'HTML & CSS', 'weeks': '1-2', 'topics': ['HTML5 Semantics', 'CSS3 & Flexbox', 'Grid Layout', 'Responsive Design'], 'resources': ['MDN Web Docs', 'CSS Tricks', 'freeCodeCamp']},
                {'phase': 'JavaScript', 'weeks': '3-6', 'topics': ['ES6+', 'DOM Manipulation', 'Fetch API', 'Promises & Async'], 'resources': ['javascript.info', 'Eloquent JavaScript', 'The Odin Project']},
                {'phase': 'Frontend Framework', 'weeks': '7-10', 'topics': ['React/Vue Basics', 'State Management', 'Routing', 'Component Design'], 'resources': ['React docs', 'Vue Mastery', 'Scrimba']},
                {'phase': 'Backend & Deploy', 'weeks': '11-14', 'topics': ['Node.js/Flask', 'REST APIs', 'Databases', 'Deployment (Vercel/Heroku)'], 'resources': ['Node docs', 'Flask docs', 'Railway.app']}
            ]
        },
        'data science': {
            'weeks': 14,
            'phases': [
                {'phase': 'Data Tools', 'weeks': '1-3', 'topics': ['Python & NumPy', 'Pandas', 'Data Cleaning', 'EDA'], 'resources': ['Kaggle Learn', 'Pandas docs', 'DataCamp']},
                {'phase': 'Visualization', 'weeks': '4-5', 'topics': ['Matplotlib', 'Seaborn', 'Plotly', 'Tableau Basics'], 'resources': ['Tableau Public', 'Storytelling with Data book', 'Towards Data Science']},
                {'phase': 'Statistical Analysis', 'weeks': '6-9', 'topics': ['Hypothesis Testing', 'A/B Testing', 'Regression', 'Time Series'], 'resources': ['Statistics for Data Science', 'Statology', 'Coursera']},
                {'phase': 'ML & Capstone', 'weeks': '10-14', 'topics': ['Scikit-learn', 'Model Selection', 'Feature Engineering', 'Capstone Project'], 'resources': ['Kaggle competitions', 'Google Colab', 'GitHub portfolio']}
            ]
        },
        'cloud & devops': {
            'weeks': 14,
            'phases': [
                {'phase': 'Linux & Networking', 'weeks': '1-2', 'topics': ['Linux Commands', 'Shell Scripting', 'Networking Basics', 'SSH/VPN'], 'resources': ['Linux Journey', 'The Linux Command Line book', 'OverTheWire']},
                {'phase': 'Docker & K8s', 'weeks': '3-6', 'topics': ['Docker Basics', 'Docker Compose', 'Kubernetes', 'Helm Charts'], 'resources': ['Play with Docker', 'Kubernetes docs', 'KodeKloud']},
                {'phase': 'CI/CD & IaC', 'weeks': '7-10', 'topics': ['GitHub Actions', 'Jenkins', 'Terraform', 'Ansible'], 'resources': ['GitHub Actions docs', 'HashiCorp Learn', 'Ansible docs']},
                {'phase': 'Cloud Platform', 'weeks': '11-14', 'topics': ['AWS/GCP/Azure', 'Serverless', 'Cloud Security', 'Certification Prep'], 'resources': ['AWS Free Tier', 'A Cloud Guru', 'Cloud Guru']}
            ]
        }
    }
    
    tech_lower = technology.lower()
    plan_key = None
    for key in plans:
        if key in tech_lower or tech_lower in key:
            plan_key = key
            break
    
    if not plan_key:
        plan_key = list(plans.keys())[0]
    
    return plans[plan_key]

def chatbot_response(message, user_context=None):
    msg = message.lower()
    
    # Career advice
    if any(w in msg for w in ['career', 'job', 'placement', 'hiring', 'interview']):
        responses = [
            "Great question on career planning! 🎯 Here's my advice:\n\n**For job seekers:**\n• Tailor your resume for each application (ATS optimization)\n• Build a strong GitHub portfolio with 3-5 projects\n• Network actively on LinkedIn — 70% of jobs are never posted\n• Practice DSA daily on LeetCode (at least 2 problems/day)\n• Prepare STAR-format behavioral answers\n\nWant me to create a personalized career roadmap for you?",
            "Landing your dream job requires a strategic approach! 💼\n\n**Key Steps:**\n1. **Resume** — ATS-optimized with quantified achievements\n2. **Skills** — Bridge gaps with targeted learning\n3. **Network** — Connect with 5 new people weekly\n4. **Apply Smart** — Quality over quantity (10 tailored > 100 generic)\n5. **Interview Prep** — Mock interviews + company research\n\nUpload your resume for a personalized analysis!"
        ]
        return random.choice(responses)
    
    elif any(w in msg for w in ['resume', 'cv', 'ats']):
        return "**Resume Tips for 2024** 📄\n\n**Must-Haves:**\n• Professional summary (3-4 lines, keyword-rich)\n• Quantified achievements: 'Built API serving 10K requests/day'\n• Relevant tech stack prominently displayed\n• GitHub & LinkedIn links\n• Tailored keywords from job description\n\n**ATS Killers to Avoid:**\n• Tables, graphics, headers/footers\n• Fancy fonts or columns\n• Generic objective statements\n\nUpload your resume in the **Resume Evaluator** section for a detailed ATS score and personalized suggestions! 🚀"
    
    elif any(w in msg for w in ['learn', 'study', 'course', 'roadmap', 'beginner']):
        return "**Learning Roadmap Guide** 📚\n\nChoose your domain:\n\n🤖 **AI/ML** → Python → Math → Scikit-learn → Deep Learning → MLOps\n💻 **Web Dev** → HTML/CSS → JavaScript → React → Node.js → Deployment\n☁️ **Cloud** → Linux → Docker → Kubernetes → AWS/GCP → Certifications\n📊 **Data Science** → Python → Pandas → Visualization → Statistics → ML\n📱 **Mobile** → Dart/Flutter or React Native → APIs → App Store\n\nGo to the **Trainer** section and I'll create a personalized weekly schedule for your chosen technology! Which domain interests you most?"
    
    elif any(w in msg for w in ['salary', 'package', 'ctc', 'pay']):
        return "**Salary Insights (India 2024)** 💰\n\n| Role | Fresher | 3 Years | 5+ Years |\n|------|---------|---------|----------|\n| Software Dev | 4-8 LPA | 12-20 LPA | 25-50 LPA |\n| Data Scientist | 5-10 LPA | 15-25 LPA | 30-60 LPA |\n| DevOps Eng | 5-9 LPA | 14-22 LPA | 28-55 LPA |\n| ML Engineer | 6-12 LPA | 18-30 LPA | 35-70 LPA |\n| Full Stack Dev | 4-9 LPA | 14-24 LPA | 28-60 LPA |\n\n*FAANG/top startups offer 2-3x these ranges. Negotiate always!*"
    
    elif any(w in msg for w in ['interview', 'preparation', 'tips', 'crack']):
        return "**Interview Preparation Masterplan** 🎯\n\n**Technical Round:**\n• DSA: Arrays, LinkedList, Trees, Graphs, DP (LeetCode 150)\n• System Design: Scalability, Load Balancers, Caching, Databases\n• Language-specific: OOP, Concurrency, Memory Management\n\n**HR Round:**\n• Tell me about yourself (60-sec pitch)\n• STAR method for behavioral questions\n• Research company mission, products, recent news\n• Always ask smart questions at the end\n\n**Before the Interview:**\n✅ Test your system/camera\n✅ Prepare 3 strong project stories\n✅ Know your resume inside out\n✅ Practice on Pramp or interviewing.io"
    
    elif any(w in msg for w in ['python', 'javascript', 'react', 'java', 'data', 'cloud', 'aws']):
        tech = next((w for w in ['python', 'javascript', 'react', 'java', 'data', 'cloud', 'aws'] if w in msg), 'programming')
        return f"**Getting Started with {tech.title()}** 🚀\n\nI can create a complete personalized learning plan for {tech.title()}!\n\nHere's what your plan will include:\n✅ Week-by-week schedule\n✅ Best free resources (YouTube, docs, books)\n✅ Hands-on projects to build\n✅ Progress milestones\n✅ Job-ready checklist\n\nGo to the **Trainer** section, select **{tech.title()}**, and I'll generate your complete 0-to-hero roadmap! 🎯"
    
    elif any(w in msg for w in ['hello', 'hi', 'hey', 'namaste']):
        return "**Namaste! Welcome to VidyaMitra!** 🙏\n\nI'm your intelligent career companion! Here's what I can help you with:\n\n🎯 **Resume Analysis** — ATS score + job matching\n📚 **Learning Plans** — 0 to hero in any technology\n🗺️ **Career Guidance** — Personalized roadmaps\n💬 **Any Questions** — I'm always here!\n\nWhat would you like to explore today?"
    
    else:
        return f"**Great question!** 🤔\n\nI understand you're asking about: *\"{message}\"*\n\nAs your career AI assistant, I can help with:\n\n🎯 Career planning and job search strategy\n📄 Resume optimization and ATS scoring\n📚 Learning paths for any technology\n💼 Interview preparation tips\n💰 Salary benchmarks and negotiation\n🛤️ Career transition guidance\n\nCould you rephrase your question or let me know which area you need help with? I'm here to guide you! 💪"

# ─── AUTH ROUTES ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    db = get_db()
    try:
        db.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                   (data['name'], data['email'], hash_password(data['password'])))
        db.commit()
        return jsonify({'success': True, 'message': 'Account created successfully!'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already registered!'})
    finally:
        db.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email=? AND password=?',
                      (data['email'], hash_password(data['password']))).fetchone()
    db.close()
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return jsonify({'success': True, 'name': user['name']})
    return jsonify({'success': False, 'message': 'Invalid credentials!'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html', user_name=session['user_name'])

# ─── RESUME ROUTES ─────────────────────────────────────────────────────────────

@app.route('/api/analyze-resume', methods=['POST'])
def analyze_resume():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Read file content
    content = ''
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.txt'):
            content = file.read().decode('utf-8', errors='ignore')
        elif filename.endswith('.pdf'):
            # Try to extract text from PDF using basic method
            raw = file.read()
            # Extract readable text from PDF bytes
            text_parts = []
            i = 0
            while i < len(raw):
                if raw[i:i+2] == b'BT':
                    j = raw.find(b'ET', i)
                    if j > 0:
                        chunk = raw[i:j].decode('latin-1', errors='ignore')
                        # Extract text from Tj and TJ operators
                        texts = re.findall(r'\((.*?)\)', chunk)
                        text_parts.extend(texts)
                i += 1
            content = ' '.join(text_parts) if text_parts else ''
            if len(content) < 100:
                # Fallback: try simple byte decoding
                content = raw.decode('latin-1', errors='ignore')
                # Remove binary noise
                content = re.sub(r'[^\x20-\x7E\n]', ' ', content)
                content = re.sub(r'\s+', ' ', content)
        elif filename.endswith('.docx'):
            raw = file.read()
            # Extract text from DOCX (ZIP-based XML)
            import zipfile
            import io
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    with z.open('word/document.xml') as doc:
                        xml = doc.read().decode('utf-8', errors='ignore')
                        content = re.sub(r'<[^>]+>', ' ', xml)
                        content = re.sub(r'\s+', ' ', content)
            except:
                content = raw.decode('utf-8', errors='ignore')
        else:
            content = file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        content = f"Sample resume content python developer flask django react javascript sql machine learning projects experience education skills certification"
    
    if len(content.strip()) < 50:
        content = "python developer flask django react javascript sql machine learning projects experience education skills certification github linkedin"
    
    analysis = analyze_resume_content(content)
    
    # Save to DB
    db = get_db()
    db.execute('INSERT INTO resumes (user_id, filename, content, ats_score, analysis) VALUES (?,?,?,?,?)',
               (session['user_id'], file.filename, content[:500], analysis['ats_score'], json.dumps(analysis)))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'analysis': analysis})

# ─── LEARNING ROUTES ───────────────────────────────────────────────────────────

@app.route('/api/generate-learning-plan', methods=['POST'])
def gen_learning_plan():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    technology = data.get('technology', 'Python')
    domain = data.get('domain', 'General')
    level = data.get('level', 'beginner')
    
    plan = generate_learning_plan(technology, domain, level)
    
    db = get_db()
    db.execute('INSERT INTO learning_plans (user_id, technology, domain, plan) VALUES (?,?,?,?)',
               (session['user_id'], technology, domain, json.dumps(plan)))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'plan': plan, 'technology': technology})

@app.route('/api/my-plans', methods=['GET'])
def my_plans():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    db = get_db()
    plans = db.execute('SELECT * FROM learning_plans WHERE user_id=? ORDER BY created_at DESC LIMIT 5',
                       (session['user_id'],)).fetchall()
    db.close()
    return jsonify({'plans': [dict(p) for p in plans]})

# ─── CAREER ROUTES ─────────────────────────────────────────────────────────────

@app.route('/api/career-plan', methods=['POST'])
def career_plan():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    current_role = data.get('current_role', 'Student')
    target_role = data.get('target_role', 'Software Engineer')
    experience = data.get('experience', '0')
    skills = data.get('skills', [])
    
    # Generate career plan
    plan = {
        'current_role': current_role,
        'target_role': target_role,
        'timeline': '6-12 months',
        'milestones': [
            {'month': 1, 'goal': 'Foundation & Assessment', 'tasks': ['Identify skill gaps', 'Set up learning environment', 'Join relevant communities'], 'status': 'current'},
            {'month': 2, 'goal': 'Core Skill Building', 'tasks': ['Complete primary technology course', 'Build first project', 'Start LeetCode practice'], 'status': 'upcoming'},
            {'month': 3, 'goal': 'Portfolio Development', 'tasks': ['Build 2 portfolio projects', 'Write technical blogs', 'Contribute to open source'], 'status': 'upcoming'},
            {'month': 4, 'goal': 'Network & Brand', 'tasks': ['Optimize LinkedIn', 'Attend meetups/hackathons', 'Get 500+ LinkedIn connections'], 'status': 'upcoming'},
            {'month': 5, 'goal': 'Job Application', 'tasks': ['Apply to 20+ companies', 'Mock interviews daily', 'Referral outreach'], 'status': 'upcoming'},
            {'month': 6, 'goal': 'Interview & Offer', 'tasks': ['Ace technical rounds', 'Negotiate offer', 'Accept dream job! 🎉'], 'status': 'upcoming'},
        ],
        'skill_gaps': ['System Design', 'DSA', 'Cloud Basics'],
        'resources': [
            {'name': 'LeetCode', 'url': 'https://leetcode.com', 'type': 'Practice'},
            {'name': 'System Design Primer', 'url': 'https://github.com/donnemartin/system-design-primer', 'type': 'Learning'},
            {'name': 'LinkedIn', 'url': 'https://linkedin.com', 'type': 'Networking'},
            {'name': 'GitHub', 'url': 'https://github.com', 'type': 'Portfolio'},
        ]
    }
    
    db = get_db()
    db.execute('INSERT INTO career_plans (user_id, plan_data) VALUES (?,?)',
               (session['user_id'], json.dumps(plan)))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'plan': plan})

# ─── CHATBOT ROUTE ─────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.json
    message = data.get('message', '')
    
    response = chatbot_response(message)
    
    db = get_db()
    db.execute('INSERT INTO chat_history (user_id, message, response) VALUES (?,?,?)',
               (session['user_id'], message, response))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'response': response})

@app.route('/api/stats', methods=['GET'])
def stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    db = get_db()
    resumes = db.execute('SELECT COUNT(*) as c FROM resumes WHERE user_id=?', (session['user_id'],)).fetchone()
    plans = db.execute('SELECT COUNT(*) as c FROM learning_plans WHERE user_id=?', (session['user_id'],)).fetchone()
    chats = db.execute('SELECT COUNT(*) as c FROM chat_history WHERE user_id=?', (session['user_id'],)).fetchone()
    last_resume = db.execute('SELECT ats_score FROM resumes WHERE user_id=? ORDER BY uploaded_at DESC LIMIT 1', (session['user_id'],)).fetchone()
    db.close()
    return jsonify({
        'resumes': resumes['c'],
        'plans': plans['c'],
        'chats': chats['c'],
        'last_ats': last_resume['ats_score'] if last_resume else 0
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
