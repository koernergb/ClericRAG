First, create your virtual environment:
  python -m venv env

Then activate the environment.

On Windows:
  ./env/Scripts/Activate.ps1

On Linux:
  source env/bin/activate

Then install the dependencies in the active virtual environment:
  pip install -r requirements.txt

You can now run the Flask app with:
  python app.py

You can also run the Streamlit app with:
  streamlit run streamlit_app.py
