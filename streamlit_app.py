import streamlit as st
import requests
import time

FLASK_API_URL = "http://localhost:5000"

def input_screen():
    st.title("Fact Extraction App - Input Screen")
    question = st.text_input('Question')
    urls = st.text_area('Enter the URLs of the call logs (one per line):')
    document_urls = [url.strip() for url in urls.split('\n') if url.strip()]
    submit_button = st.button('Submit')
    if submit_button:
        payload = {
            "question": question,
            "documents": document_urls
        }
        response = requests.post(f"{FLASK_API_URL}/submit_question_and_documents", json=payload)
        if response.status_code == 200:
            st.success("Question and documents submitted successfully.")
        else:
            st.error(f"Error submitting question and documents: {response.status_code}")
    return submit_button, question

def output_screen(question):
    st.title("Fact Extraction App - Output Screen")
    st.write(f"Question: {question}")
    message = st.empty()
    message.info("Processing the documents, please wait...")
    while True:
        response = requests.get(f"{FLASK_API_URL}/get_question_and_facts")
        print(f"Received response from /get_question_and_facts: {response.json()}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'processing':
                print("Still processing, waiting...")
                message.info("Still processing, please wait...")
            elif data['status'] == 'done':
                print("Processing complete, displaying facts...")
                message.info("Processing complete")
                facts = data['facts'].split('\n')
                for fact in facts:
                    if fact.strip():
                        st.write(f"• {fact.strip()}")
                break
        else:
            print(f"Error fetching processing status: {response.status_code}")
            st.error(f"Error fetching processing status: {response.status_code}")
        time.sleep(2)

def main():
    if 'output' not in st.session_state:
        print("output is not in state")
        st.session_state['output'] = False
    if not st.session_state['output']:
        print("cue input_screen")
        submit_button, question = input_screen()
        if submit_button:
            print("Submit button pressed")
            print("now set session state output to true and sesion question to question")
            st.session_state['output'] = True
            st.session_state['question'] = question
            st.experimental_rerun()
    else:
        print("output screen start")
        output_screen(st.session_state['question'])
    if st.session_state['output']:
        if st.button('Back'):
            st.session_state['output'] = False

if __name__ == "__main__":
    main()