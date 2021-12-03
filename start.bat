call venv\Scripts\activate.bat

set PYTHONPATH=./src
set FLASK_APP=app_flask:app
set FLASK_ENV=development

flask run

pause