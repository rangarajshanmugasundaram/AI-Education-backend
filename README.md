# 📝 Attendance Management API Documentation

This project provides backend REST APIs to manage student attendance, restrict access using Role-Based Access Control (RBAC), and automatically calculate session durations using MongoDB.

**Base URL:** `http://127.0.0.1:8000`

---

## 🔒 Global Security Headers
Every API request requires the following headers for authentication and RBAC validation:
* `Authorization`: `Bearer mock-jwt-token-from-backend-xyz123`
* `X-User-Email`: `trainertest@gmail.com` (or authorized student/admin email)

---

## 📡 API Endpoints Specification

### 1. Mark Attendance (Check-In)
Creates a new attendance record when a student joins a session.
* **URL:** `/api/attendance/mark`
* **Method:** `POST`
**Request Body (JSON):**
  ```json
  {
    "user_id": "STUDENT_TEST_001",
    "session_id": "session_react_basics",
    "join_time": "2026-07-13 10:00:00",
    "leave_time": "2026-07-13 11:30:00",
    "status": "Present"
  }