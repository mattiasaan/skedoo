```bash
cd backend

python -m venv venv
#windows
venv\Scripts\activate
#linux
source venv/bin/activate

pip install -r requirements.txt

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```