# SmartCampus — Issue Reporting & Resolution Platform

A full-stack Flask web application for centralized campus issue management.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install flask werkzeug

# 2. Run the app
cd SmartCampus
python app.py

# 3. Open in browser
http://localhost:5000
```

## 🔑 Demo Credentials

| Role    | Email                  | Password    |
|---------|------------------------|-------------|
| Admin   | admin@campus.edu       | admin123    |
| Student | student@campus.edu     | student123  |

## 📁 Project Structure

```
SmartCampus/
├── app.py                  # Main Flask application
├── campus.db               # SQLite database (auto-created)
├── templates/
│   ├── base.html           # Shared layout with sidebar
│   ├── landing.html        # Public landing page
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── dashboard.html      # User/Admin dashboard
│   ├── report.html         # Report new issue
│   ├── issue_detail.html   # Issue details + comments
│   ├── all_issues.html     # Admin: all issues + filters
│   └── analytics.html      # Admin: analytics dashboard
└── static/
    └── uploads/            # Uploaded issue images
```

## ✨ Features

### Student/Staff
- Register & login with secure password hashing
- Report issues with: title, category, location, priority, description, image
- Track issue status in real-time (Open → In Progress → Resolved)
- View issue history on dashboard
- Comment on issues for follow-up

### Admin
- View all campus issues in one place
- Filter by category, status, priority
- Assign issues to teams/personnel
- Update issue status with resolution notes
- Full analytics dashboard with charts:
  - Issues by category (bar chart)
  - Status distribution (donut chart)
  - Priority breakdown (horizontal bar)
  - Monthly trend (line chart)
  - Top issue locations (visual progress bars)

## 🛠 Technology Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite (with parameterized queries)
- **Frontend**: HTML5, CSS3, Jinja2 templating
- **Charts**: Chart.js 4
- **Icons**: Font Awesome 6
- **Fonts**: Syne + DM Sans (Google Fonts)
- **Security**: Werkzeug password hashing, session-based auth, RBAC
