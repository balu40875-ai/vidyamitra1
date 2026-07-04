# 🎓 VidyaMitra — Intelligent Career Agent

> AI-Powered Resume Evaluator, Trainer & Career Planner

---

## ⚡ Setup in VS Code (Easy Steps)

### Step 1 — Install Python
Make sure Python 3.9+ is installed. Check: `python --version`

### Step 2 — Open in VS Code
```
File → Open Folder → Select the "vidyamitra" folder
```

### Step 3 — Open Terminal in VS Code
```
Terminal → New Terminal  (or press Ctrl + `)
```

### Step 4 — Create Virtual Environment
```bash
python -m venv venv
```

### Step 5 — Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```
**Mac/Linux:**
```bash
source venv/bin/activate
```

### Step 6 — Install Dependencies
```bash
pip install flask
```

### Step 7 — Run the App
```bash
python app.py
```

### Step 8 — Open in Browser
```
http://localhost:5000
```

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 🔐 Secure Login | SQLite3 user auth with SHA-256 hashing |
| 📊 Resume Evaluator | ATS scoring, skill detection, job matching |
| 🎓 AI Trainer | 0-to-hero learning plans for 50+ technologies |
| 🗺️ Career Planner | Milestone-based personalized roadmap |
| 💬 AI Chatbot | 24/7 career guidance assistant |
| 🎨 Liquid Glass UI | Apple-inspired premium design |

## 📁 Project Structure
```
vidyamitra/
├── app.py              ← Flask backend (all APIs)
├── requirements.txt    ← Dependencies
├── vidyamitra.db      ← SQLite database (auto-created)
├── uploads/           ← Resume uploads
└── templates/
    ├── index.html     ← Landing + Login page
    └── dashboard.html ← Main app dashboard
```

## 🏆 Hackathon Winning Features
- Premium liquid glass UI (Apple-inspired)
- Real ATS scoring algorithm
- 5 powerful AI-powered tools in one platform
- Zero external database needed (SQLite3)
- Works 100% offline after setup
- Mobile-responsive design

---
Made with ❤️ for VidyaMitra Hackathon
