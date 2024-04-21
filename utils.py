   
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
    with a "-" followed by a single factual statement sentence. Do not output markdown formatting.
    
    EXAMPLE:
    EXAMPLE_QUERY: What are our product design decisions?
    EXAMPLE_CURRENT_FACTS:
    - The team has decided to use a responsive design to ensure the product works well on all devices.
    - The team has decided to provide both dark and light theme options for the user interface.
    EXAMPLE_NEW_FACTS:
    - The team has decided to focus on a desktop-first approach instead of responsive design for the product.
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