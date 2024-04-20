import streamlit as st
import os
from dotenv import load_dotenv
import openai
import requests
import threading

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]


# GLOBAL VARIABLES
current_question = ""
current_document_urls = []
current_facts = []
current_status = "processing"


# HELPER FUNCTIONS
def make_gpt_api_call(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.7,
        )
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
    
    # Extract facts from the document
    extract_facts_prompt = rf"""Extract facts relevant to the query from the document. Return your answer as a string of relevant, concise, & factual statements, with each fact separated by a new line.
            Query: {question}
            Document: {document_content}
            Your answer: """
            
    return extract_facts_prompt


def validate_facts_string(question, facts):
    # Validate and consolidate the extracted facts
    prompt = f"""Given the query: {question}
    And the following facts extracted from the documents:
    {chr(10).join(facts)}

    Please validate and consolidate the facts, considering the following:
    - Remove any facts that are irrelevant to the query.
    - If a fact is invalidated or contradicted by a fact from a later document, remove the invalidated fact.
    - Merge similar or redundant facts into a single fact.
    - Provide a final list of validated and consolidated facts relevant to the query. Return your answer as
    a string of relevant, concise, & factual statements, with each fact separated by a new line.
    Your Answer:
    """
    return prompt


def process_documents():
    global current_question, current_document_urls, current_facts, current_status
    
    extracted_facts = []
    
    for url in current_document_urls:
        document_content = fetch_document(url)
        prompt = extract_facts_string(current_question, document_content)        
        response = make_gpt_api_call(prompt)
        facts = parse_response(response)
        extracted_facts.extend(facts)
    
    prompt = validate_facts_string(current_question, extracted_facts)            
    response = make_gpt_api_call(prompt)
    current_facts = parse_response(response)
    current_status = "done"





def main():
    st.title("Fact Extraction Application")

    # Input section
    question = st.text_input("Enter your question:")
    document_urls = st.text_area("Enter the URLs of the documents (one per line):")
    document_urls = [url.strip() for url in document_urls.split("\n") if url.strip()]

    if st.button("Submit"):
        if question and document_urls:
            facts = process_documents(question, document_urls)

            # Display the facts
            st.header("Facts")
            for fact in facts:
                st.write(f"- {fact}")
        else:
            st.error("Please enter a question and at least one document URL.")

if __name__ == "__main__":
    main()