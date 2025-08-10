from langchain_core.prompts import ChatPromptTemplate

doc_analyse_prompt = ChatPromptTemplate.from_template(
    """
    You are a highly capable assistant trained to analyze and summarize documents.
    Return ONLY valid JSON matching the exact schema below.

    {format_instructions}

    Analyze this document:
    {document_text}
    """
)

doc_analyse_prompt = ChatPromptTemplate.from_template(
    """
    **You are a data-cleaning assistant.**

    I will give you a raw table (possibly from a PDF) that may include:

    - Merged or split cells  
    - Empty columns or rows  
    - Repeated header rows  
    - Multi-line entries  
    - Mixed logical sections  

    ---

    ### Your job:

    1. **Detect separate sections**  
    If the table contains two or more distinct blocks—each with its own header—treat them as separate tables.

    2. **Clean each table:**  
    - **Drop** any fully empty rows or columns.  
    - **Remove** duplicate header rows (keep only the first header in each section).  
    - **Flatten** multi-line cells into single lines and trim extra whitespace.  
    - **Use** the first line of each section as the header.

    3. **Output**  
    - For each section produce a JSON array of objects.  
    - Use the cleaned header labels (in lowerCamelCase or snake_case) as keys.  
    - If there are multiple sections, label each output (e.g. `"policies": […]`, `"errors": […]`).
    - Just return the JSON without any additional text or explanations.
    
    Here's the raw table data:
    {table_content}
    """
)
