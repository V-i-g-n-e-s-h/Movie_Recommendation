# Movie Recommendation System

This project provides personalized movie recommendations using the Neo4j graph database and a Streamlit web interface.

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/V-i-g-n-e-s-h/Movie_Recommendation.git
cd Movie_Recommendation
```
---
### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate       # On macOS/Linux
venv\Scripts\activate          # On Windows
```
---
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
---
### 4. Setup Neo4j Sandbox
- Visit: https://neo4j.com/sandbox

- Create a Recommendations sandbox database.

- Copy the following credentials:

  - Connection URI (e.g., neo4j://<ip>:7687)

  - Username

  - Password
---
### 5. Add Credentials to `.env`

Create a `.env` file in the root of your project:

```ini
SANDBOX_URL=neo4j://<your-sandbox-ip>:7687
SANDBOX_USERNAME=<your-username>
SANDBOX_PASSWORD=<your-password>
```
---
### 6. Run the Streamlit App

```bash
streamlit run main.py
```
---
### 💡 Notes

Ensure your Neo4j sandbox is active while running the app.
---