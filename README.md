First, create your virtual environment:

  _python -m venv env_

Then activate the environment.

On Windows:

_./env/Scripts/Activate.ps1_

On Linux:

_source env/bin/activate_

Then install the dependencies in the active virtual environment:

_pip install -r requirements.txt_

You can now run the Flask app with:

_python app.py_

You can also run the Streamlit app with:

_streamlit run streamlit_app.py_
