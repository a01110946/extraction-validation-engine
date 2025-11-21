# Quick Start Guide

Get the Extraction Validation Engine running in 5 minutes.

## Prerequisites Check

Before starting, ensure you have:

```bash
# Check Python version (need 3.11+)
python --version

# Check Node.js version (need 18+)
node --version

# Check if MongoDB is installed
mongod --version
```

If any are missing, install them first.

---

## Step 1: Get a Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key (you'll need it in Step 3)

---

## Step 2: Start MongoDB

### Option A: Local MongoDB

```bash
# Windows (if installed as service)
net start MongoDB

# Mac/Linux
mongod
```

### Option B: MongoDB Atlas (Cloud)

1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster
3. Get connection string (you'll use this in `.env`)

---

## Step 3: Backend Setup

Open a terminal:

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -e .

# Create environment file
cp .env.example .env

# Edit .env file
# On Windows: notepad .env
# On Mac/Linux: nano .env

# Add your Google API key:
# GOOGLE_API_KEY=your_key_here
```

Start the backend server:

```bash
python main.py
```

You should see:
```
🚀 Starting Extraction Validation Engine...
✅ Connected to MongoDB: extraction_validation
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

Test backend: Open `http://localhost:8000/docs` in your browser. You should see the API documentation.

---

## Step 4: Frontend Setup

Open a **new terminal** (keep backend running):

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

You should see:
```
  VITE v6.0.1  ready in X ms

  ➜  Local:   http://localhost:5173/
```

**Keep this terminal open too!**

---

## Step 5: Test the Application

1. Open `http://localhost:5173` in your browser

2. You should see the **Extraction Validation Engine** interface

3. **Test with a sample image:**
   - If you have column drawings from your Colab experiments, use those
   - Or take a screenshot of a construction detail drawing
   - Drag and drop it into the upload area

4. **Watch the magic:**
   - Image uploads → Gemini extracts data
   - ACI 318 validates and heals data
   - NumPy calculates coordinates
   - Three.js renders 3D visualization

5. **Edit and validate:**
   - Modify any values in the right sidebar
   - The 3D view updates instantly
   - Click "Save & Validate" to store in MongoDB

---

## Troubleshooting

### Backend won't start

**Error: `ModuleNotFoundError: No module named 'fastapi'`**

Solution:
```bash
cd backend
pip install -e .
```

**Error: `GOOGLE_API_KEY not found`**

Solution: Make sure you created `.env` file and added your API key:
```bash
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_actual_key
```

**Error: `MongoDB connection failed`**

Solution: Make sure MongoDB is running:
```bash
# Check if MongoDB is running
# On Windows:
tasklist | findstr mongod

# On Mac/Linux:
ps aux | grep mongod
```

### Frontend won't start

**Error: `command not found: npm`**

Solution: Install Node.js from [nodejs.org](https://nodejs.org)

**Error: `Cannot find module 'react'`**

Solution:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Extraction fails

**Error: `Extraction failed: 429`**

Solution: You've hit Gemini API rate limit. Wait a minute and try again.

**Error: `Extraction failed: 401`**

Solution: Your API key is invalid. Check your `.env` file.

---

## Next Steps

Once everything is working:

1. **Read the docs:** Check [Project Definition](docs/project-definition-and-architectural-blueprint.md) to understand the architecture

2. **Explore the code:**
   - Backend: `backend/src/`
   - Frontend: `frontend/src/`

3. **Try your own drawings:** Upload construction detail images

4. **Customize:** Modify the Pydantic schemas to support beams, slabs, etc.

---

## Quick Reference

### Backend

- **Start:** `cd backend && python main.py`
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### Frontend

- **Start:** `cd frontend && npm run dev`
- **URL:** http://localhost:5173

### MongoDB

- **Local URL:** `mongodb://localhost:27017`
- **Database:** `extraction_validation`
- **Collection:** `extractions`

---

Need help? Check the main [README.md](README.md) or open an issue on GitHub.
