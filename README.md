# AI Career Assistant Web App

This implementation follows the uploaded project PPT:
- Flask backend
- SQLite database with SQLAlchemy
- Bootstrap/HTML/CSS frontend
- Resume PDF text extraction and keyword-based skill detection
- Resume scoring and suggestions
- Technical/HR interview practice with rule-based evaluation
- Skill-based job recommendation
- PDF resume analysis report

## Run on Windows

1. Install Python 3.10+.
2. Open this folder in VS Code.
3. Open Terminal and run:

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python app.py

4. Open http://127.0.0.1:5000

## Linux/macOS

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py

## Important
- The job data is a local demonstration dataset. Replace it with a verified live job API before claiming that jobs are currently hiring.
- The interview evaluator is rule-based in this version. A real LLM/API can be integrated later.
- The resume analyzer works best with text-based PDFs; scanned image PDFs need OCR.
- Change SECRET_KEY in app.py before deployment.
