# 📅 Week 1 Assignment

## 📌 Overview
This folder contains my Week 1 work for the Generative AI course.  
It includes a Python project and supporting materials such as images related to account setup.

---

## 💻 Project: Registration Form (Streamlit + Email OTP Verification)

### 🧠 Description
I developed a **Registration Form web application** using Python and Streamlit with secure email verification.

The system uses **Google App Password authentication** to securely send OTPs without exposing the original email password.  
Users receive a real working OTP to verify their email during registration.

---

## 🔐 Key Features

- 📩 Email OTP verification system  
- 🔁 Resend OTP functionality  
- 🔒 Secure authentication using Google App Password  
- ⚡ Real-time interaction with Streamlit  
- 🧑‍💻 Simple and user-friendly interface  

---

## ⚙️ How It Works

1. User enters details in the registration form  
2. System generates a One-Time Password (OTP)  
3. OTP is sent to the user's email  
4. User enters OTP to verify  
5. Access is granted after successful verification  
6. If OTP is not received, user can **resend OTP**

---

## 🛠️ Technologies Used

- Python  
- Streamlit  
- SMTP (Email sending)  
- Google App Password  

---

## ▶️ How to Run the Project

1. Install dependencies:
```bash
pip install streamlit
