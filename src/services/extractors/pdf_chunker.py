import json
import pdfplumber
import requests
import structlog

from src.services.prompts.prompting import doc_analyse_prompt
from typing import List
from io import BytesIO
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ChunkPDF:
    """
    ChunkPDF is a utility class for processing and chunking PDF documents from a given URL.
    It extracts text and tables from each page of the PDF, converts tables to JSON format,
    pretty-prints the JSON, and splits both text and tables into manageable chunks for further processing.
        azOpenA_llm: An instance of an LLM (Large Language Model) interface used for table analysis.
    Methods:
        _jsonify_tables(tables: List[List[List[str | None]]]) -> list[str | dict]:
            Converts extracted tables from the PDF into a JSON format using the LLM.
        _pretty_print_json(json_data: str) -> str:
            Formats JSON strings for better readability, removing code block markers if present.
        _extract_text_from_pdf(url: str) -> List[Document]:
            Downloads the PDF from the given URL, extracts text and tables from each page,
            and returns a list of Document objects containing the extracted content.
        _split_texts(documents: List[Document]) -> List[Document]:
            Splits the extracted text and table content into smaller chunks using recursive character splitting.
        chunk_pdf(url: str) -> List[Document]:
            Main method to process a PDF from a URL, extracting and chunking its content.
            Returns a list of Document objects containing both text and tables.
    """
    
    
    def __init__(self, azOpenA_llm):
        self.azOpenA_llm = azOpenA_llm
        self.log = structlog.get_logger(self.__class__.__name__)
        
    def _jsonify_tables(self, tables: List[List[List[str | None]]]) -> list[str | dict]:
        tables_json = []
        
        for idx, table in enumerate(tables):
            rows = ""
            
            for row in table:
                filtered_row = [col for col in row if col not in ('', None)]
                final_row = " | ".join([x.strip().replace('\n', '') for x in filtered_row])
                rows += final_row + "\n"
            
            chain = doc_analyse_prompt | self.azOpenA_llm
            self.log.debug("Invoking LLM for table analysis", table_index=idx)
            
            response = chain.invoke({
                "table_content": rows
            })
            
            tables_json.append(response.content)
        
        return tables_json
    
    def _pretty_print_json(self, json_data: str) -> str:
        content = json_data
        
        # If the content starts with "```json", remove it
        if content.strip().startswith("```json"):
            content = content.strip()[7:]
            
            # If the content ends with "```", remove it
            if content.endswith("```"):
                content = content[:-3]
            
        try:
            parsed = json.loads(content)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except Exception:
            return content.strip()
        
    def _extract_text_from_pdf(self, url: str) -> List[Document]:
        response = requests.get(url)
        response.raise_for_status()

        with pdfplumber.open(BytesIO(response.content)) as pdf:
            doucments = []

            for page in pdf.pages:
                text = page.extract_text()
                tables = page.extract_tables()

                # JSONify the tables. This will convert the tables into a JSON format that can be processed
                j_tables = self._jsonify_tables(tables)

                # Pretty print the JSON tables. This will format the JSON tables for better readability
                pretty_tables = [self._pretty_print_json(tbl) for tbl in j_tables] if j_tables else []

                # Add text to the documents list
                doucments.append(Document(page_content=text, metadata={"page": page.page_number}))
                # Add the pretty printed tables to the documents list
                [doucments.append(Document(page_content=pt, metadata={"page": page.page_number, "table": True})) for pt in pretty_tables if pt]
                
        return doucments
    
    def _split_texts(self, documents: List[Document]) -> List[Document]:
        table_lengths = [len(doc.page_content) for doc in documents if doc.metadata.get("table")]
        max_table_length = max(table_lengths) if table_lengths else None

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
        )

        table_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_table_length if max_table_length else 500,
            chunk_overlap=(int(max_table_length / 5)) if max_table_length else 100,
            length_function=len,
        )

        splitted_docs: List[Document] = []

        for doc in documents:
            if doc.metadata.get("table"):
                # Split the table content using the table splitter
                # split_documents returns a list of Document objects. So we extend the splitted_doc list with the result
                # Note: appending the result directly to splitted_doc will create a nested list
                splitted_docs.extend(table_splitter.split_documents([doc]))
            else:
                # Split the regular text using the text splitter
                # split_documents returns a list of Document objects. So we extend the splitted_doc list with the result
                # Note: appending the result directly to splitted_doc will create a nested list
                splitted_docs.extend(text_splitter.split_documents([doc]))

        return splitted_docs
    
    def chunk_pdf(self, url: str) -> List[Document]:
        """
        Main method to chunk a PDF document from a given URL.
        
        Args:
            url (str): The URL of the PDF document to be processed.
        
        Returns:
            List[Document]: A list of Document objects containing the text and tables from the PDF.
        """
        documents = self._extract_text_from_pdf(url)
        return self._split_texts(documents)
