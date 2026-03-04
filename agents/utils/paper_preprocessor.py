import requests
import base64
import json
import math
import argparse
import os
import shutil
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# TODO(developer): Update these values for your project
MISTRAL_MODEL_ID = "mistral-ocr-2505"
GEMINI_MODEL_ID = "gemini-2.5-pro"
PROJECT_ID = "nova-gemini-250403"
REGION = "us-central1"

class VertexAIOCR:
    """Base class for Vertex AI OCR operations using service account authentication."""

    def __init__(self, model_id, project_id, service_account_path):
        self.model_id = model_id
        self.project_id = project_id
        self.service_account_path = service_account_path
        self.credentials = None

        # Load credentials from service account JSON file
        if not service_account_path:
            raise ValueError("Service account JSON file path is required")
        self._load_credentials()

    def _load_credentials(self):
        """Load service account credentials from JSON file."""
        try:
            with open(self.service_account_path, "r") as f:
                service_account_info = json.load(f)

            self.credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            print(f"Loaded service account credentials from {self.service_account_path}")
        except Exception as e:
            print(f"Error loading service account credentials: {e}")
            raise

    def get_access_token(self):
        """获取Google Cloud访问令牌"""
        try:
            # Refresh credentials to get access token
            self.credentials.refresh(Request())
            return self.credentials.token
        except Exception as e:
            print(f"Error getting access token from service account: {e}")
            return None

    def prepare_ocr_payload(self, base64_pdf_content):
        """Prepare OCR payload. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement prepare_ocr_payload()")

    def send_ocr_request(self, payload):
        """Send OCR request. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement send_ocr_request()")

    def extract_text(self, response):
        """Extract text from response. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement extract_text()")

class MistralOCR(VertexAIOCR):
    """Handles Vertex AI Mistral OCR API operations using service account authentication."""

    def __init__(self, model_id=MISTRAL_MODEL_ID, project_id=PROJECT_ID, region=REGION, service_account_path=None):
        super().__init__(model_id, project_id, service_account_path)
        self.region = region

    def prepare_ocr_payload(self, base64_pdf_content):
        """
        准备Vertex AI Mistral OCR API请求体
        
        Args:
            base64_pdf_content (str): Base64编码的PDF内容
        
        Returns:
            dict: 请求体字典
        """
        payload = {
            "model": self.model_id,
            "document": {
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf_content}"
            },
            "include_image_base64": True,
        }
        return payload

    def send_ocr_request(self, payload):
        """
        发送OCR请求到Vertex AI Mistral OCR API
        
        Args:
            payload (dict): 请求体
        
        Returns:
            dict: 解析后的JSON响应，如果失败则返回None
        """
        try:
            # 获取访问令牌
            access_token = self.get_access_token()
            if not access_token:
                print("Failed to get access token")
                return None
            
            # 构建请求URL
            url = f"https://{self.region}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.region}/publishers/mistralai/models/{self.model_id}:rawPredict"
            
            # 构建请求头
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            print("正在发送OCR请求到Vertex AI Mistral OCR API...")
            response = requests.post(url=url, headers=headers, json=payload)
            
            if response.status_code == 200:
                try:
                    response_dict = response.json()
                    print("OCR请求成功完成")
                    return response_dict
                except json.JSONDecodeError as e:
                    print("Error decoding JSON:", e)
                    print("Raw response:", response.text)
                    return None
            else:
                print(f"Request failed with status code: {response.status_code}")
                print("Response text:", response.text)
                return None
                
        except Exception as e:
            print(f"Error sending OCR request: {e}")
            return None

    def extract_text(self, response):
        """
        Extract markdown text from Mistral OCR response

        Args:
            response (dict): Mistral OCR API response

        Returns:
            str: Extracted markdown text
        """
        if not response or 'pages' not in response:
            return ""
        return "".join([page["markdown"] for page in response["pages"]])

class GeminiOCR(VertexAIOCR):
    """Handles Vertex AI Gemini 2.5 Pro API operations using service account authentication."""

    def __init__(self, model_id=GEMINI_MODEL_ID, project_id=PROJECT_ID, service_account_path=None):
        super().__init__(model_id, project_id, service_account_path)

    def prepare_ocr_payload(self, base64_pdf_content):
        """
        准备Vertex AI Gemini API请求体

        Args:
            base64_pdf_content (str): Base64编码的PDF内容

        Returns:
            dict: 请求体字典
        """
        payload = {
            "contents": {
                "role": "user",
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "application/pdf",
                            "data": base64_pdf_content
                        }
                    },
                    {
                        "text": "Extract all text from this PDF document and format it in markdown. Preserve the document structure, headings, tables, and formatting."
                    }
                ]
            }
        }
        return payload

    def send_ocr_request(self, payload):
        """
        发送OCR请求到Vertex AI Gemini API

        Args:
            payload (dict): 请求体

        Returns:
            dict: 解析后的JSON响应，如果失败则返回None
        """
        try:
            # 获取访问令牌
            access_token = self.get_access_token()
            if not access_token:
                print("Failed to get access token")
                return None

            # 构建请求URL - Note: Gemini uses 'global' location
            url = f"https://aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/global/publishers/google/models/{self.model_id}:streamGenerateContent"

            # 构建请求头
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            # 发送请求
            print("正在发送OCR请求到Vertex AI Gemini API...")
            response = requests.post(url=url, headers=headers, json=payload)

            if response.status_code == 200:
                try:
                    response_dict = response.json()
                    print("OCR请求成功完成")
                    return response_dict
                except json.JSONDecodeError as e:
                    print("Error decoding JSON:", e)
                    print("Raw response:", response.text)
                    return None
            else:
                print(f"Request failed with status code: {response.status_code}")
                print("Response text:", response.text)
                return None

        except Exception as e:
            print(f"Error sending OCR request: {e}")
            return None

    def extract_text(self, response):
        """
        Extract text from Gemini API streaming response

        Args:
            response (list): Gemini API streaming response (list of chunks)

        Returns:
            str: Extracted text
        """
        if not response:
            return ""

        full_text = ""
        for chunk in response:
            if 'candidates' in chunk and len(chunk['candidates']) > 0:
                candidate = chunk['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    for part in candidate['content']['parts']:
                        if 'text' in part:
                            full_text += part['text']
        return full_text

class PDFProcessor:
    """Handles PDF downloading, processing, and chunking operations."""
    
    MAX_BASE64_SIZE_MB = 30
    MAX_PAGES_PER_CHUNK = 30
    
    def find_optimal_chunk_size(self, reader, start_page, max_pages):
        """
        Use binary search to find the maximum number of pages that fit in a <30MB chunk.
        
        Args:
            reader: PdfReader object
            start_page: Starting page index
            max_pages: Maximum pages to consider
        
        Returns:
            int: Optimal number of pages for this chunk
        """
        left, right = 1, max_pages
        best_pages = 1
        
        while left <= right:
            mid = (left + right) // 2
            end_page = start_page + mid
            
            # Create test chunk
            writer = PdfWriter()
            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])
            
            pdf_output = BytesIO()
            writer.write(pdf_output)
            pdf_output.seek(0)
            
            chunk_base64 = base64.b64encode(pdf_output.read()).decode('utf-8')
            chunk_size_mb = len(chunk_base64) / (1024 * 1024)
            
            if chunk_size_mb <= self.MAX_BASE64_SIZE_MB:
                best_pages = mid
                left = mid + 1
            else:
                right = mid - 1
        
        return best_pages

    def create_pdf_chunk(self, reader, start_page, num_pages):
        """
        Create a PDF chunk with specified pages and return base64 encoded string.
        
        Args:
            reader: PdfReader object
            start_page: Starting page index
            num_pages: Number of pages to include
        
        Returns:
            tuple: (base64_string, size_in_mb)
        """
        end_page = start_page + num_pages
        writer = PdfWriter()
        
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        
        pdf_output = BytesIO()
        writer.write(pdf_output)
        pdf_output.seek(0)
        
        chunk_base64 = base64.b64encode(pdf_output.read()).decode('utf-8')
        chunk_size_mb = len(chunk_base64) / (1024 * 1024)
        
        return chunk_base64, chunk_size_mb

    def load_local_pdf_and_encode(self, pdf_path):
        """Load a local PDF file and encode it to base64, split into chunks if needed."""
        try:
            # Step 1: Read the local PDF file
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()

            print(f"Loaded local PDF from {pdf_path}")

            # Step 2: Load the PDF into memory
            pdf_data = BytesIO(pdf_content)
            reader = PdfReader(pdf_data)

            return self._process_pdf_chunks(reader, pdf_content)

        except Exception as e:
            print(f"Error loading local PDF: {e}")
            return None

    def download_pdf_and_encode(self, pdf_link, save_pdf=True, pdf_filename=None):
        """Encode the pdf to base64, split into chunks so each chunk < 30MB and <= 30 pages."""
        try:
            # Step 1: Fetch the PDF using requests
            response = requests.get(pdf_link)
            response.raise_for_status()

            # Step 1.5: Save the PDF file if requested
            if save_pdf and pdf_filename:
                with open(pdf_filename, 'wb') as f:
                    f.write(response.content)
                print(f"PDF saved to {pdf_filename}")

            # Step 2: Load the PDF into memory
            pdf_data = BytesIO(response.content)
            reader = PdfReader(pdf_data)

            return self._process_pdf_chunks(reader, response.content)

        except Exception as e:
            print(f"Error: {e}")
            return None

    def _process_pdf_chunks(self, reader, pdf_content):
        """Common logic to process PDF chunks."""
        try:
            total_pages = len(reader.pages)
            print(f"Total pages: {total_pages}")

            # Step 3: Check if entire PDF is small enough and not too many pages
            full_base64 = base64.b64encode(pdf_content).decode('utf-8')
            base64_size_mb = len(full_base64) / (1024 * 1024)
            print(f"Full PDF base64 size: {base64_size_mb:.2f} MB")

            if base64_size_mb <= self.MAX_BASE64_SIZE_MB and total_pages <= self.MAX_PAGES_PER_CHUNK:
                return [full_base64]

            # Step 4: Dynamic chunking
            reason = []
            if base64_size_mb > self.MAX_BASE64_SIZE_MB:
                reason.append("size > 30MB")
            if total_pages > self.MAX_PAGES_PER_CHUNK:
                reason.append("pages > 30")
            print(f"Using dynamic chunking due to {' and '.join(reason)}...")
            chunks = []
            current_page = 0

            while current_page < total_pages:
                remaining_pages = total_pages - current_page
                max_pages_for_this_chunk = min(remaining_pages, self.MAX_PAGES_PER_CHUNK)

                # Find optimal chunk size for current position (respect page and size limits)
                optimal_pages = self.find_optimal_chunk_size(reader, current_page, max_pages_for_this_chunk)

                # Create the chunk
                chunk_base64, chunk_size_mb = self.create_pdf_chunk(reader, current_page, optimal_pages)

                print(f"Chunk {len(chunks)+1}: pages {current_page}-{current_page + optimal_pages - 1} ({optimal_pages} pages), size {chunk_size_mb:.2f} MB")
                chunks.append(chunk_base64)

                current_page += optimal_pages

            print(f"Created {len(chunks)} chunks total")
            return chunks

        except Exception as e:
            print(f"Error processing PDF chunks: {e}")
            return None

def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Process PDF papers using Vertex AI OCR (Gemini or Mistral)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python paper_preprocessor.py --arxiv-id "2505.10066" --service-account "path/to/service-account.json"
  python paper_preprocessor.py --arxiv-id "2505.10066" --service-account "path/to/service-account.json" --model mistral
  python paper_preprocessor.py --pdf-link "https://arxiv.org/pdf/2505.10066" --service-account "path/to/service-account.json"
  python paper_preprocessor.py --local-pdf "path/to/paper.pdf" --service-account "path/to/service-account.json"
        """
    )
    
    # Create mutually exclusive group for PDF link, arXiv ID, or local PDF
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--pdf-link",
        type=str,
        help="Direct PDF download link"
    )
    group.add_argument(
        "--arxiv-id",
        type=str,
        help="arXiv paper ID (e.g., '2505.10066' or 'arxiv:2505.10066')"
    )
    group.add_argument(
        "--local-pdf",
        type=str,
        help="Path to local PDF file"
    )
    
    parser.add_argument(
        "--service-account",
        type=str,
        required=True,
        help="Path to Google Cloud service account JSON file for authentication (required)"
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=["mistral", "gemini"],
        default="gemini",
        help="OCR model to use: 'mistral' for Mistral OCR or 'gemini' for Gemini 2.5 Pro (default: gemini)"
    )
    parser.add_argument(
        "--output-root",
        type=str,
        default="attacks_paper_info",
        help="Root directory to store processed paper assets (default: attacks_paper_info)"
    )

    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()

    # Determine PDF source and ID based on input
    if args.local_pdf:
        # Use local PDF file
        local_pdf_path = Path(args.local_pdf).resolve()
        if not local_pdf_path.exists():
            print(f"Error: Local PDF file not found: {local_pdf_path}")
            exit(1)

        pdf_id = local_pdf_path.stem  # Use filename without extension as ID
        pdf_source = str(local_pdf_path)
        is_local = True
        print(f"Processing local PDF: {pdf_source}")
    elif args.pdf_link:
        pdf_link = args.pdf_link
        pdf_id = pdf_link.split("/")[-1]
        pdf_source = pdf_link
        is_local = False
        print(f"Processing PDF from URL: {pdf_source}")
    else:  # args.arxiv_id
        pdf_link = f"https://arxiv.org/pdf/{args.arxiv_id}"
        pdf_id = args.arxiv_id
        pdf_source = pdf_link
        is_local = False
        print(f"Processing arXiv PDF: {pdf_source}")

    # Initialize processors
    pdf_processor = PDFProcessor()

    # Initialize OCR client based on model choice
    if args.model == "mistral":
        print(f"Using Mistral OCR model")
        ocr_client = MistralOCR(service_account_path=args.service_account)
    else:  # gemini
        print(f"Using Gemini 2.5 Pro model")
        ocr_client = GeminiOCR(service_account_path=args.service_account)

    # Create directory structure
    # Find project root (where .git directory is located)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent  # Go up from agents/utils/ to project root
    output_dir = project_root / args.output_root / pdf_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir = str(output_dir)

    # Process the PDF
    if is_local:
        # For local PDF, copy it to output directory if not already there
        pdf_filename = os.path.join(output_dir, f"{pdf_id}.pdf")
        if os.path.abspath(local_pdf_path) != os.path.abspath(pdf_filename):
            shutil.copy2(local_pdf_path, pdf_filename)
            print(f"PDF copied to {pdf_filename}")
        else:
            print(f"PDF already in output directory: {pdf_filename}")

        # Load and encode local PDF
        chunks = pdf_processor.load_local_pdf_and_encode(local_pdf_path)
    else:
        # Download and encode PDF from URL
        pdf_filename = os.path.join(output_dir, f"{pdf_id}.pdf")
        chunks = pdf_processor.download_pdf_and_encode(pdf_source, save_pdf=True, pdf_filename=pdf_filename)

    if not chunks:
        print("Failed to process PDF")
        exit(1)
    
    responses = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        payload = ocr_client.prepare_ocr_payload(chunk)
        response = ocr_client.send_ocr_request(payload)
        
        if not response:
            print(f"Failed to get OCR response for chunk {i+1}")
            continue
        
        responses.append(response)
    
    if not responses:
        print("Failed to get OCR responses for any chunks")
        exit(1)

    # Extract markdown content using OCR client's extract_text method
    full_markdown = "".join([ocr_client.extract_text(response) for response in responses])

    # Save to file
    output_filename = os.path.join(output_dir, f"{pdf_id}.md")
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(full_markdown)
    
    print(f"OCR result saved to {output_filename}")
    print(f"All files saved in directory: {output_dir}")
