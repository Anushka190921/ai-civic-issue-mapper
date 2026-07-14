<div align="center">

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&height=200&color=0:1a73e8,100:0d47a1&text=AI%20Civic%20Issue%20Mapper&fontColor=ffffff&fontSize=40&fontAlignY=38&animation=fadeIn"/>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Google OAuth](https://img.shields.io/badge/Google_OAuth-4285F4?style=for-the-badge&logo=google&logoColor=white)

![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)
![Deployed](https://img.shields.io/badge/Deployed-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

</div>

---

## 🌐 Live Demo

The application is deployed and live at: **[https://ai-civic-issue-mapper.onrender.com](https://ai-civic-issue-mapper.onrender.com)**

**Tech used for deployment:**
- **Hosting:** Render (Free tier)
- **Database:** Aiven for MySQL (Free tier)
- **Email delivery:** Brevo API (bypasses Render's free-tier SMTP restrictions)

> Note: Free tier services may take 30-60 seconds to wake up after periods of inactivity.


---

## 📌 About

A government-style civic issue reporting portal where citizens can report problems like garbage dumping, broken roads, water leakage, and street light failures. Authorities can track, manage, and resolve issues efficiently while keeping citizens informed.

---

## ✨ Features

| Feature | Status |
|---------|--------|
| User Registration & Login | ✅ Done |
| Google OAuth Login | ✅ Done |
| Report Issue with Image & Location | ✅ Done |
| Admin Dashboard | ✅ Done |
| Dashboard Statistics | ✅ Done |
| Department Assignment | ✅ Done |
| Complaint Status Tracking | ✅ Done |
| Email Validation & Password Rules | ✅ Done |
| Rate Limiting | ✅ Done |
| Custom 404 / 500 / 429 Error Pages | ✅ Done |
| Mobile Responsive Design | ✅ Done |
| Citizen Feedback System | ✅ Done |
| Notification System | ✅ Done |
| Forgot / Reset Password (Email Verification) | ✅ Done |
| AI Image Classification | ⏳ Coming Soon |
| Map Visualization | ⏳ Coming Soon |
| Search & Filter Dashboard | ⏳ Coming Soon |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Database | MySQL |
| Frontend | HTML, CSS, Bootstrap |
| Authentication | Flask-Dance, Google OAuth |
| Security | Werkzeug, python-dotenv |

---

## 📁 Project Structure
ai-civic-issue-mapper/

├── static/

│   ├── uploads/        ← complaint images

│   └── style.css

├── templates/

│   ├── login.html

│   ├── register.html

│   ├── form.html

│   ├── my_issues.html

│   ├── admin.html

│   ├── admin_login.html

│   └── success.html

├── .env                ← credentials (not on GitHub)

├── .gitignore

├── app.py              ← main backend

└── requirements.txt

---

## 🚀 How to Run

**1. Clone the repository**
```bash
git clone https://github.com/Anushka190921/ai-civic-issue-mapper.git
cd ai-civic-issue-mapper
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Create .env file**
SECRET_KEY=your_secret_key

DB_HOST=localhost

DB_USER=root

DB_PASSWORD=your_password

DB_NAME=civic_issues

GOOGLE_CLIENT_ID=your_google_client_id

GOOGLE_CLIENT_SECRET=your_google_client_secret


**4. Run the app**
```bash
python app.py
```

**5. Open browser**
http://127.0.0.1:5000

---

## 📸 Screenshots

| Login | Register |
|-------|----------|
| ![Login](assets/login.png) | ![Register](assets/register.png) |

| Report Issue | Success Page |
|-------------|--------------|
| ![Form](assets/form.png) | ![Success](assets/success.png) |

| My Complaints |
|--------------|
| ![My Issues](assets/my_issues.png) |



## 👥 Team

| Role | Name | GitHub |
|------|------|--------|
| 👑 Project Lead & Backend Developer | Anushka | [Anushka190921](https://github.com/Anushka190921) |
| 🎨 Frontend Developer | Kanishka | [Kanishka240306](https://github.com/Kanishka240306) |
| 🔗 API / Testing / Integration | [Anushka504-S](https://github.com/Anushka504-S)

---

## 🔮 Coming Soon

- 🤖 AI Image Classification
- 🗺️ Map Visualization (Leaflet.js)
- 📊 Analytics Dashboard

---

<div align="center">

**⭐ If you find this project useful, please star the repository!**

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&section=footer&height=100&color=0:1a73e8,100:0d47a1"/>

</div>