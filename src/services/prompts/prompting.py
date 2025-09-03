from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

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

contextualize_question_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Task: Rewrite the user's latest message into a standalone question ONLY if it relies on prior context.\n"
     "Context source: You will receive the full conversation as `chat_history` followed by the latest `input`.\n\n"
     "How to use chat_history:\n"
     "1) Resolve anaphora/ellipsis (e.g., 'and pricing?', 'that one', 'them', 'it') using entities from chat_history.\n"
     "2) Pull ONLY the minimal details from chat_history needed to make the question self-contained.\n"
     "3) If chat_history lacks enough info to resolve the reference, return the input unchanged.\n\n"
     "Never rewrite—just return exactly as written—when the input is:\n"
     "- Greetings/farewells (hi, hello, hey, bye, good morning, etc.)\n"
     "- Courtesy/acknowledgment (thanks, thank you, ok/okay, sounds good, cool)\n"
     "- Apologies or chit-chat (sorry, no worries)\n"
     "- Interjections, fillers, emojis, or punctuation (..., ??, 👍)\n\n"
     "Additional rules:\n"
     "- If the input is already a complete standalone question, return it unchanged.\n"
     "- Only rewrite follow-ups that depend on chat_history.\n"
     "- Do NOT answer the question; output only the rewritten text.\n"
     "- Preserve meaning and tone; do not add new requests.\n"
     "- Guardrail: if the input has ≤3 words and contains no question mark or why/how term, return unchanged."
    ),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

context_qa_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a helpful assistant that must answer only using the information in the provided SYSTEM CONTEXT.\n"
     "Rules:\n"
     "- If the user greets you (for example with 'hi', 'hello', 'thank you', etc.), reply with an appropriate friendly greeting before answering. \n"
     "- Use only the provided SYSTEM CONTEXT below; do not rely on outside knowledge or assumptions.\n"
     "- If the answer cannot be found in the SYSTEM CONTEXT, respond exactly with: Sorry, I couldn't find the answer in the provided context.\n"
     "- After the answer, on a new line, ask exactly one short, relevant follow-up question.\n"
     "- Still ask the follow-up question even if you replied with 'Sorry, I couldn't find the answer in the provided context.'\n"
     "- Use chat_history only to resolve references and maintain continuity.\n"
     "- Use user_memory to personalize responses if relevant.\n"
     "- Always format your reply using Markdown."
    ),
    ("system", "Context:\n{context}"),
    ("system", "User Memory:\n{user_memory}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])