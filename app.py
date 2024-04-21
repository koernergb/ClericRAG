# IMPORTS
import os
from dotenv import load_dotenv
import threading
import time
import openai
import requests
import streamlit as st
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin  



# GLOBAL VARIABLES
current_question = ""
current_document_urls = []
current_facts = []
current_status = "processing"



# INITIALIZATION
# Load OpenAI API key from .env file
load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"] 
# Start Flask app with CORS
app = Flask(__name__)
CORS(app)  



# HELPER FUNCTIONS
def make_gpt_api_call(prompt):
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.05,
        )
        print("Successful API call")
        return response.choices[0].message['content'].strip()
    
    except Exception as e:
        print(f"Error occurred during API call: {e}")
        return None



def fetch_document(url):
    
    if url.startswith("http"):
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            print(f"Fetched document from URL: {url}")
            return response.text
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching document from {url}: {e}")
            return None
    
    else:
        
        try:
            with open(url, 'r') as file:
                content = file.read()
                print(f"Loaded local document: {url}")
                return content
            
        except FileNotFoundError as e:
            print(f"Error reading local file {url}: {e}")
            return None
    
    
    
def parse_response(response):
    
    if response is None:
        print("No response from GPT API")
        return []
    
    facts = response.split('\n')
    return [fact.strip() for fact in facts if fact.strip()]



# PROMPTING FUNCTIONS
def extract_facts(question, document_content):
    
    extract_facts_prompt = rf"""
    
    Extract new FACTS relevant to the QUERY from the DOCUMENT. 
    Return your answer, FACTS, as a string of relevant, concise, & factual statements, with each fact separated by a new line.
    Here is an EXAMPLE:
    
    EXAMPLE_QUERY:
    What are our product design decisions?
     
    EXAMPLE_INPUT_DOCUMENT:
    1
    00:01:11,430 --> 00:01:40,520
    John: Hello, everybody. Let's start with the product design discussion. I think we should go with a modular design for our product. It will allow us to easily add or remove features as needed.

    2
    00:01:41,450 --> 00:01:49,190
    Sara: I agree with John. A modular design will provide us with the flexibility we need. Also, I suggest we use a responsive design to ensure our product works well on all devices. Finally, I think we should use websockets to improve latency and provide real-time updates.

    3
    00:01:49,340 --> 00:01:50,040
    Mike: Sounds good to me. I also propose we use a dark theme for the user interface. It's trendy and reduces eye strain for users. Let's hold off on the websockets for now since it's a little bit too much work.

    EXAMPLE_OUTPUT_FACTS:
    - The team has decided to go with a modular design for the product.
    - The team has decided to use a responsive design to ensure the product works well on all devices.
    - The team has decided to use a dark theme for the user interface.
    
    QUERY: 
    {question}
    
    DOCUMENT: 
    {document_content}
    
    Now return a short bulleted list of FACTS formatted just like EXAMPLE_OUTPUT_FACTS. 
    Answer in brief and concise factual statements, with one simple statement per line: 
    """
    response = make_gpt_api_call(extract_facts_prompt)
    extracted_facts = parse_response(response)
    return extracted_facts



def consolidate_facts(question, fact_lists):
    prompt = f"""
    Given a QUERY and a list of facts, with more recent facts later in the list,
    consolidate these facts into a single, final list of facts, considering the following:
    - Remove any duplicate facts across the lists.
    - If a fact from later in the list contradicts or replaces an earlier fact, keep the later fact.
    - If a fact from later in the list provides additional information or clarification to an earlier fact, only include the later updated fact.

    INSTRUCTIONS:
    - Provide a FINAL_FACTS list with one fact per line.
    - Each factual statement should start with a "- " (hyphen and a space) followed by a single sentence describing the fact.
    - Do not include any additional text, formatting, or numbering in the output.

    QUERY: {question}
    FACT_LISTS:
    {fact_lists}
    FINAL_FACTS:
    """
    response = make_gpt_api_call(prompt)
    response = parse_response(response)
    return response



def format_consolidated_facts(summary):
    prompt = f"""
    You have been provided with a summary of facts about the contents of documents.
    The latest, most recent, subsequent facts are true.
    Your task is to convert this summary into a list of the latest true concise factual statements, with one fact per line, in the following format:

    - [Factual statement]
    
    Here's an example of output in the desired format:
    - The team has decided to focus on a desktop-first approach for the product.
    - The team has decided to provide both dark and light theme options for the user interface.

    Each fact should be a single sentence, starting with a hyphen followed by a space, and should not include any additional formatting or numbering.

    Here is the summary:

    {summary}

    Please provide the list of facts in the desired format:
    """
    response = make_gpt_api_call(prompt)
    response = parse_response(response)
    return response



def process_documents():
    
    global current_question, current_document_urls, current_facts, current_status

    current_facts = []

    for url in current_document_urls:
        
        document_content = fetch_document(url)
        new_facts = extract_facts(current_question, document_content)
        print("Facts: \n")
        print(new_facts)
        current_facts.extend(new_facts)
        time.sleep(5)

    # After processing all documents, validate the consolidated list of facts
    facts = consolidate_facts(current_question, [current_facts])
    print("Consolidated facts:\n" + "\n".join(facts))
    
    formatted_facts = format_consolidated_facts(facts)
    print(f"Formatted facts: \n {formatted_facts}")
    current_facts = formatted_facts

    current_status = "done"
    print("current status should be updated to done")



# FLASK ENDPOINT ROUTING
@app.route('/')
def index():
    
    return "Home"



@app.route('/submit_question_and_documents', methods=['POST'])
@cross_origin()
def submit_question_and_documents():
    print("Received request at /submit_question_and_documents")
    # Clear previous history
    global current_question, current_document_urls, current_facts, current_status
    current_question = ""
    current_document_urls = []
    current_facts = []
    current_status = "processing"

    data = request.get_json()
    question = data['question']
    document_urls = data['documents']

    # Store the question and document URLs in global variables
    current_question = question
    current_document_urls = document_urls

    # Start processing the documents asynchronously
    threading.Thread(target=process_documents).start()

    return jsonify({"message": "Processing started"}), 200



@app.route('/get_question_and_facts', methods=['GET'])
@cross_origin()
def get_question_and_facts():
    print("Entered /get_question_and_facts")
    global current_question, current_facts, current_status
    
    response = {
        "question": current_question,
        "facts": current_facts if current_status == "done" else [],
        "status": current_status
    }
    
    print(f"Returning response from /get_question_and_facts: {response}")
    
    return jsonify(response), 200



# MAIN
if __name__ == '__main__':
    app.run(host='0.0.0.0')