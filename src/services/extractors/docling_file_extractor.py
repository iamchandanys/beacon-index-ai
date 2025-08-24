import time
import structlog

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (PdfPipelineOptions, PictureDescriptionApiOptions)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from langchain.schema import Document
from src.core.app_settings import get_settings

class DoclingFileExtractor:
    def __init__(self):
        self.app_settings = get_settings()
        self.log = structlog.get_logger(self.__class__.__name__)
    
    def __get_pic_desc_api_opts(self) -> PictureDescriptionApiOptions:
        picture_desc_api_option = PictureDescriptionApiOptions(
            url=self.app_settings.AZURE_OPENAI_GPT_4O_FULL_ENDPOINT,
            prompt="Describe this image in sentences in a single paragraph.",
            params={
                "model": self.app_settings.AZURE_OPENAI_GPT_4O_MODEL,
                "max_tokens": 200,
                "temperature": 0.5
            },
            headers={
                "api-key": self.app_settings.AZURE_OPENAI_API_KEY,
            },
            timeout=90,
        )
        
        return picture_desc_api_option
    
    def __get_pdf_pipeline_options(self) -> PdfPipelineOptions:
        # Set device to CUDA for GPU usage
        accelerator_options = AcceleratorOptions(num_threads=8, device=AcceleratorDevice.CUDA)
        
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        pipeline_options.generate_picture_images = True
        pipeline_options.do_picture_description = True
        pipeline_options.picture_description_options = self.__get_pic_desc_api_opts()
        pipeline_options.enable_remote_services = True
        pipeline_options.accelerator_options = accelerator_options
        
        return pipeline_options
    
    def __get_file_markdown(self, file_url: str) -> str:
        """
        Converts a file at the given URL to Markdown using Docling.
        Args:
            file_url (str): Path or URL to the file.
        Returns:
            str: Markdown representation of the file.
        Raises:
            ValueError, Exception
        """
        if file_url is None or file_url.strip() == "":
            self.log.error("No file URL provided.")
            raise ValueError("No file URL provided.")
        
        self.log.info("Starting document conversion.", file_url=file_url)

        # For now, we will only support PDF files. In the future, we may add support for other formats.
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=self.__get_pdf_pipeline_options())
            }
        )
        
        try:
            start_time = time.time()
            conv_result = doc_converter.convert(source=file_url)
            end_time = time.time() - start_time
            
            self.log.info("Document conversion completed.", duration=f"{end_time:.2f} seconds")
            
        except Exception as e:
            self.log.error("Document conversion failed.", error=str(e))
            raise

        mark_down = conv_result.document.export_to_markdown(
            page_break_placeholder="--- PAGE BREAK ---", 
            image_mode=ImageRefMode.PLACEHOLDER
        )
        
        self.log.info("Markdown exported successfully.", preview=mark_down[:100])
        
        return mark_down
    
    def __get_file_documents(self, mark_down: str) -> list[Document]:
        """
        Splits the provided markdown string into pages and creates a list of Document objects for each page.
        Args:
            mark_down (str): The markdown string to be split into pages.
        Returns:
            list[Document]: A list of Document objects, each representing a page.
        Raises:
            ValueError: If the markdown string is empty or None.
        """
        if mark_down is None or mark_down.strip() == "":
            self.log.error("No markdown found.")
            raise ValueError("No markdown found.")

        self.log.info("Splitting markdown into pages.")
        
        page_split = mark_down.split("--- PAGE BREAK ---")

        documents: list[Document] = []
        
        self.log.info("Creating Document objects for each page.", total_pages=len(page_split))

        for i, page in enumerate(page_split):
            doc = Document(
                page_content=page.strip(),
                metadata={"page": i + 1}
            )
            documents.append(doc)

        self.log.info("All Document objects created successfully.", document_count=len(documents))
        
        return documents
    
    def chunk_file(self, file_url: str) -> list[Document]:
        """
        Splits a file into chunks and returns a list of Document objects.
        Args:
            file_url (str): The path or URL to the file.
        Returns:
            list[Document]: A list of Document objects extracted from the file.
        """
        mark_down = self.__get_file_markdown(file_url=file_url)
        documents = self.__get_file_documents(mark_down=mark_down)
        
        return documents
    
if __name__ == "__main__":
    file_extractor = DoclingFileExtractor()
    file_extractor.chunk_file("https://emcdevstoragev2.blob.core.windows.net/public/efba9f0b-70cc-4dab-b6b7-5812a22c0c37.pdf")