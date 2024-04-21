# IMPORTS
import time
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import openai
import requests
import threading
import streamlit as st


# GLOBAL VARIABLES
current_question = ""
current_document_urls = []
current_facts = []
current_status = "processing"


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
            temperature=0.4,
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




def extract_facts_string(question, document_content):
    
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
    
    return extract_facts_prompt



def convert_output_formatting(facts_string):
    # Convert facts string to list of facts by asking the model about the output
    conversion_prompt = rf"""
    You have been giving me undesirably-formatted output like: 
    "1. **Desktop-First Design**: The product will focus on a desktop-first approach, prioritizing functionality on desktop platforms.
    2. **Responsive Design**: The product incorporates a responsive design to ensure efficient functionality across various devices like desktops, tablets, and smartphones.
    3. **User Interface Theme**: The product will offer both dark and light theme options for the user interface, catering to different user preferences and situations.

    I want your output to only consist of facts with one "-" character at the start of each new fact,
    without numbering like "1." or special characters like "**" or titles like "Desktop-First Design".
    Instead, your output formatting should look like this desired format:
    - Desktop-first approach, prioritizing functionality on desktop platforms
    - Responsive design to ensure efficient functionality across various devices like desktops, tablets, and smartphones
    - Offer both dark and light theme options for the user interface, catering to different user preferences and situations
    
    Here is your output:
    {facts_string}
    
    If it is formatted correctly, the output will simply be the facts_string unchanged. 
    Otherwise, the output will be the facts_string reformatted to match the desired format.
    Now convert your facts_string output to the correctly formatted output:
    """
    return conversion_prompt


def remove_duplicates(facts_list):
    
    remove_duplicates_prompt = f"""
    We have a list of facts. Some facts in the list may be duplicates.
    You must return the list of facts without any duplicates.
    
    Here's an illustrative example.
    EXAMPLE FACTS LIST:
    - Focus on a desktop-first design approach
    - Not pursue a modular design at this time
    - Offer both dark and light theme options for the user interface, catering to different user preferences
    - Provide an alternative light theme for users who find the dark theme too intense
    
    EXAMPLE DESIRED OUTPUT:
    - Focus on a desktop-first design approach
    - Not pursue a modular design at this time
    - Offer both dark and light theme options for the user interface, catering to different user preferences
    
    Here's the list of facts to check for duplicates:
    FACTS LIST
    {facts_list}
    YOUR OUTPUT:
    """
    de_duped = make_gpt_api_call(remove_duplicates_prompt)
    return de_duped   
   

def validate_facts_string(question, current_facts, new_facts):
    
    if not current_facts:
        # If current_facts is empty, return new_facts as the updated list of facts
        return '\n'.join(new_facts)
    
    validation_prompt = f"""
    Given a QUERY, CURRENT_FACTS from previous documents, and NEW_FACTS, validate and consolidate the facts, considering the following:
    - Compare each new fact with the current facts.
    - If a new fact contradicts or makes an existing fact obsolete, include the new fact but not the existing fact in the consolidated facts.
    - If a new fact provides additional information or clarification to an existing fact, only add the new update to the consolidated facts.
    - Add any new facts to consolidated facts that do not conflict with or duplicate existing facts.
    - Merge similar or redundant facts into a single fact for your output.
    - Provide an updated list of validated and consolidated facts relevant to the query.
    
    INSTRUCTIONS:
    - Provide a short, concise list of factual statements CONSOLIDATED_FACTS with one fact per line.
    - Keep each factual statement brief and to the point and of this same format, 
    with a "-" followed by a single factual statement sentence
    
    EXAMPLE:
    EXAMPLE_QUERY: What are our product design decisions?
    EXAMPLE_CURRENT_FACTS:
    - The team has decided to use a responsive design to ensure the product works well on all devices.
    - The team has decided to provide both dark and light theme options for the user interface.
    EXAMPLE_NEW_FACTS:
    - The team has decided to focus on a desktop-first approach for the product.
    EXAMPLE_CONSOLIDATED_FACTS:
    - The team has decided to focus on a desktop-first approach for the product.
    - The team has decided to provide both dark and light theme options for the user interface.
    
    QUERY: {question}
    CURRENT_FACTS:
    {chr(10).join(current_facts)}
    NEW_FACTS:
    {chr(10).join(new_facts)}
    CONSOLIDATED_FACTS:
    """
    return validation_prompt



def process_documents():
    
    global current_question, current_document_urls, current_facts, current_status
    
    current_facts = []
    
    for url in current_document_urls:
        document_content = fetch_document(url)
        prompt = extract_facts_string(current_question, document_content)
        print("Preparing to call GPT API")        
        response = make_gpt_api_call(prompt)
        print("Called GPT API")
        new_facts = parse_response(response)
        print(response)
        
        prompt = validate_facts_string(current_question, current_facts, new_facts) 
        print("Preparing to make GPT validation call")
        response = make_gpt_api_call(prompt)
        print("Made GPT API call for validation.")           
        current_facts = parse_response(response)
        print(response)
        time.sleep(5)
    
    # read all documents, convert current facts formatting
    # remove duplicates from facts list
    
    formatted_output_prompt = convert_output_formatting(current_facts)
    print("Preparing final formatting API call")
    current_facts = make_gpt_api_call(formatted_output_prompt)
    print(f"Formatting API call completed, here's the result:\n {current_facts}")
    # current_facts = remove_duplicates(current_facts)
    # print("We've removed duplicates, here's the final result: \n" + current_facts)
    current_status = "done"
    print("current status should be updated to done")



# SET UP FLASK & GPT API
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set up OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

@app.route('/submit_question_and_documents', methods=['POST'])
def submit_question_and_documents():
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



@app.route('/')
def index():
    return "Welcome to the Fact Extraction Application"


@app.route('/test_submit', methods=['GET'])
def test_submit():
    # Clear previous history
    global current_question, current_document_urls, current_facts
    current_question = ""
    current_document_urls = []
    current_facts = []

    test_question = "What are our product design decisions?"
    test_document_urls = [
        "https://koernergb.github.io/pdf/call_log01.txt",
        "https://koernergb.github.io/pdf/call_log02.txt",
        "https://koernergb.github.io/pdf/call_log03.txt"
    ]

    current_question = test_question
    current_document_urls = test_document_urls

    threading.Thread(target=process_documents).start()
    return "Test submission started"


@app.route('/get_question_and_facts', methods=['GET'])
def get_question_and_facts():
    global current_question, current_facts, current_status
    
    response = {
        "question": current_question,
        "facts": current_facts if current_status == "done" else [],
        "status": current_status
    }
    
    print(f"Returning response from /get_question_and_facts: {response}")
    
    return jsonify(response), 200


if __name__ == '__main__':
    app.run()