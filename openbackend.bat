@ECHO OFF

call venv/scripts/activate
call python app.py runserver -h localhost -p 5000