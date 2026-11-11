import argparse
import base64
import json
import os
import re
import shutil
from io import BytesIO
from pathlib import Path
from typing import Optional

from openai import OpenAI
from PyPDF2 import PdfReader, PdfWriter

# Default model ID
# DEFAULT_MODEL = "bh/gemini-3-flash-preview"
DEFAULT_MODEL = "gemini-3.1-pro-preview"

# LiteLLM proxy settings
# DEFAULT_BASE_URL = "https://router.ai.iiis.co:9443/v1"
DEFAULT_BASE_URL = "https://api.wenwen-ai.com/v1"

DEFAULT_API_KEY_ENV = "WENWEN_API_KEY"


# ---------------------------------------------------------------------------
# Eligibility check prompts
# ---------------------------------------------------------------------------

ABSTRACT_TRIAGE_PROMPT = """\
You are an expert classifier for jailbreak attack research papers.

Based ONLY on the title and abstract below, determine whether this paper proposes a NEW jailbreak attack method that is:
1. A jailbreak attack on LLMs (not defense, not survey, not benchmark)
2. Black-box (only needs API access, no gradients/weights/logits)
3. Text-only (not vision, not audio, not multimodal)
4. Practical to run on CPU (no GPU/training required from reading the abstract)

Title: {title}

Abstract: {abstract}

Respond with ONLY a JSON object:
{{
  "eligible": true or false,
  "reason": "one sentence explanation"
}}
"""

DEEP_TRIAGE_PROMPT = """\
You are an expert classifier for jailbreak attack research papers.

You are given the first 8 pages of a paper. Determine whether this paper's proposed attack method is PRACTICALLY CPU-runnable in a black-box text-only setting.

Specifically, check for these DISQUALIFYING signals:
- Uses transformers library to load or run a local model (e.g., for perplexity filtering, token scoring)
- Requires torch/cuda for any part of the attack pipeline
- Needs to calculate perplexity, token probabilities, or embeddings locally
- Requires fine-tuning or training any model
- Needs gradient computation or backpropagation
- Requires vision/audio/multimodal inputs
- Only works with white-box/gray-box access (needs logits, hidden states, model internals)
- Requires running inference on a local LLM (not via API)

Note: Using an external LLM API (like OpenAI, Claude, etc.) for generation/scoring IS acceptable and counts as CPU-runnable.

Respond with ONLY a JSON object:
{{
  "eligible": true or false,
  "reason": "one sentence explanation",
  "disqualifying_signals": ["list of signals found, if any"]
}}
"""


# ---------------------------------------------------------------------------
# LLM Client
# ---------------------------------------------------------------------------

class LLMClient:
    """Thin wrapper around OpenAI-compatible API for triage and OCR."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None, base_url: Optional[str] = None):
        api_key = api_key or os.environ.get(DEFAULT_API_KEY_ENV)
        if not api_key:
            raise ValueError(f"{DEFAULT_API_KEY_ENV} environment variable not set")
        base_url = base_url or DEFAULT_BASE_URL

        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        print(f"LLM client initialized: model={self.model} base_url={base_url}")

    def chat(self, messages: list) -> str:
        """Send chat completion and return content."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    def chat_with_pdf(self, pdf_bytes: bytes, text_prompt: str) -> str:
        """Send chat completion with inline PDF data."""
        chunk_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "file",
                            "file": {
                                "filename": "paper.pdf",
                                "file_data": f"data:application/pdf;base64,{chunk_base64}",
                            },
                        },
                        {
                            "type": "text",
                            "text": text_prompt,
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Eligibility checks
# ---------------------------------------------------------------------------

class EligibilityError(Exception):
    """Raised when a paper fails eligibility checks."""
    pass


def _parse_json_response(text: str) -> dict:
    """Extract JSON object from LLM response."""
    # Try to find JSON in markdown code block
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Try raw JSON
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"Could not parse JSON from response: {text[:200]}")


def _collapse_whitespace(text: str) -> str:
    """Normalize whitespace from arXiv XML/HTML fields."""
    return re.sub(r"\s+", " ", text).strip()


def _strip_html(html_text: str) -> str:
    """Extract readable text from a small arXiv HTML fragment."""
    import html

    text = re.sub(r"<(script|style)\b.*?</\1>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return _collapse_whitespace(html.unescape(text))


def _fetch_arxiv_metadata_from_api(arxiv_id: str) -> tuple[str, str]:
    """Fetch title and abstract through the official arXiv Atom API."""
    import urllib.request
    import xml.etree.ElementTree as ET

    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    print(f"  Fetching arxiv metadata: {url}")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "autojailbreak-paper-preprocessor/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as resp:
        xml_data = resp.read().decode("utf-8")

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_data)
    entry = root.find("atom:entry", ns)

    if entry is None:
        raise EligibilityError(f"Paper {arxiv_id} not found on arXiv")

    title_el = entry.find("atom:title", ns)
    abstract_el = entry.find("atom:summary", ns)
    if title_el is None or abstract_el is None or not title_el.text or not abstract_el.text:
        raise EligibilityError(f"Paper {arxiv_id} metadata is incomplete")

    return _collapse_whitespace(title_el.text), _collapse_whitespace(abstract_el.text)


def _fetch_arxiv_metadata_from_abs_page(arxiv_id: str) -> tuple[str, str]:
    """Fetch title and abstract from https://arxiv.org/abs/{id}."""
    import urllib.request

    url = f"https://arxiv.org/abs/{arxiv_id}"
    print(f"  Fetching arxiv abs page metadata: {url}")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "autojailbreak-paper-preprocessor/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as resp:
        page = resp.read().decode("utf-8", errors="replace")

    title_match = re.search(
        r'<h1\s+class="title\s+mathjax">(.*?)</h1>',
        page,
        flags=re.DOTALL | re.IGNORECASE,
    )
    abstract_match = re.search(
        r'<blockquote\s+class="abstract\s+mathjax">(.*?)</blockquote>',
        page,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if not title_match or not abstract_match:
        raise EligibilityError(f"Paper {arxiv_id} metadata not found on arXiv abs page")

    title = _strip_html(title_match.group(1))
    abstract = _strip_html(abstract_match.group(1))
    title = re.sub(r"^Title:\s*", "", title, flags=re.IGNORECASE).strip()
    abstract = re.sub(r"^Abstract:\s*", "", abstract, flags=re.IGNORECASE).strip()

    if not title or not abstract:
        raise EligibilityError(f"Paper {arxiv_id} metadata is incomplete on arXiv abs page")

    return title, abstract


def fetch_arxiv_metadata(arxiv_id: str) -> tuple[str, str]:
    """Fetch title and abstract, falling back to the abs page when the API is rate-limited."""
    try:
        return _fetch_arxiv_metadata_from_api(arxiv_id)
    except EligibilityError:
        raise
    except Exception as exc:
        print(f"  ⚠️  arXiv API metadata fetch failed ({type(exc).__name__}: {exc}); trying abs page")
        return _fetch_arxiv_metadata_from_abs_page(arxiv_id)


def check_abstract_eligibility(client: LLMClient, arxiv_id: str) -> dict:
    """
    Step 1: Fetch arxiv abstract and check basic eligibility.

    Returns:
        dict with 'eligible' (bool) and 'reason' (str)

    Raises:
        EligibilityError: If paper is not eligible
    """
    print(f"\n{'='*60}")
    print("STEP 1: Abstract eligibility check")
    print(f"{'='*60}")

    title, abstract = fetch_arxiv_metadata(arxiv_id)

    print(f"  Title: {title}")
    print(f"  Abstract: {abstract[:150]}...")

    # Query LLM
    prompt = ABSTRACT_TRIAGE_PROMPT.format(title=title, abstract=abstract)
    print(f"  Querying {client.model} for abstract triage...")

    response_text = client.chat([{"role": "user", "content": prompt}])
    result = _parse_json_response(response_text)

    print(f"  Result: eligible={result.get('eligible')} reason={result.get('reason')}")

    if not result.get("eligible"):
        raise EligibilityError(
            f"Paper {arxiv_id} failed abstract triage: {result.get('reason')}"
        )

    return result


def check_deep_eligibility(client: LLMClient, pdf_path: Path) -> dict:
    """
    Step 2: Send first 8 pages of PDF to verify CPU-runnability.

    Returns:
        dict with 'eligible' (bool), 'reason' (str), 'disqualifying_signals' (list)

    Raises:
        EligibilityError: If paper is not eligible
    """
    print(f"\n{'='*60}")
    print("STEP 2: Deep eligibility check (first 8 pages)")
    print(f"{'='*60}")

    # Extract first 8 pages
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()

    reader = PdfReader(BytesIO(pdf_content))
    total_pages = len(reader.pages)
    pages_to_check = min(8, total_pages)

    writer = PdfWriter()
    for i in range(pages_to_check):
        writer.add_page(reader.pages[i])

    pdf_output = BytesIO()
    writer.write(pdf_output)
    chunk_bytes = pdf_output.getvalue()

    chunk_base64_mb = len(base64.b64encode(chunk_bytes)) / (1024 * 1024)
    print(f"  Sending {pages_to_check}/{total_pages} pages ({chunk_base64_mb:.1f} MB base64)")
    print(f"  Querying {client.model} for deep triage...")

    response_text = client.chat_with_pdf(chunk_bytes, DEEP_TRIAGE_PROMPT)
    result = _parse_json_response(response_text)

    signals = result.get("disqualifying_signals", [])
    print(f"  Result: eligible={result.get('eligible')} reason={result.get('reason')}")
    if signals:
        print(f"  Disqualifying signals: {signals}")

    if not result.get("eligible"):
        raise EligibilityError(
            f"Paper failed deep triage: {result.get('reason')} "
            f"Signals: {signals}"
        )

    return result


# ---------------------------------------------------------------------------
# PDF processing (OCR)
# ---------------------------------------------------------------------------

class PDFProcessor:
    """Handles PDF analysis and chunking operations."""

    MAX_BASE64_SIZE_MB = 5
    MAX_PAGES_PER_CHUNK = 10

    def analyze_pdf(self, pdf_path: Path):
        """Analyze PDF to determine if chunking is needed."""
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()

            reader = PdfReader(BytesIO(pdf_content))
            total_pages = len(reader.pages)

            full_base64 = base64.b64encode(pdf_content).decode('utf-8')
            base64_size_mb = len(full_base64) / (1024 * 1024)

            print(f"PDF Analysis:")
            print(f"  Total pages: {total_pages}")
            print(f"  Base64 size: {base64_size_mb:.2f} MB")

            reasons = []
            if base64_size_mb > self.MAX_BASE64_SIZE_MB:
                reasons.append(f"size > {self.MAX_BASE64_SIZE_MB}MB")
            if total_pages > self.MAX_PAGES_PER_CHUNK:
                reasons.append(f"pages > {self.MAX_PAGES_PER_CHUNK}")

            needs_chunking = len(reasons) > 0
            reason = " and ".join(reasons) if reasons else None

            return needs_chunking, total_pages, base64_size_mb, reason

        except Exception as e:
            print(f"Error analyzing PDF: {e}")
            return False, 0, 0, None

    def find_optimal_chunk_size(self, reader, start_page, max_pages):
        """Binary search for max pages fitting in size limit."""
        left, right = 1, max_pages
        best_pages = 1

        while left <= right:
            mid = (left + right) // 2
            end_page = start_page + mid

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
        """Create a PDF chunk with specified pages in memory."""
        try:
            end_page = start_page + num_pages
            writer = PdfWriter()

            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])

            pdf_output = BytesIO()
            writer.write(pdf_output)
            pdf_output.seek(0)

            chunk_content = pdf_output.read()
            chunk_base64 = base64.b64encode(chunk_content).decode('utf-8')
            chunk_size_mb = len(chunk_base64) / (1024 * 1024)

            return chunk_content, chunk_size_mb

        except Exception as e:
            print(f"Error creating PDF chunk: {e}")
            return None, 0

    def chunk_pdf(self, pdf_path: Path):
        """Split PDF into chunks in memory."""
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()

            reader = PdfReader(BytesIO(pdf_content))
            total_pages = len(reader.pages)

            chunks = []
            current_page = 0
            chunk_num = 1

            print(f"\nChunking PDF in memory...")

            while current_page < total_pages:
                remaining_pages = total_pages - current_page
                max_pages_for_this_chunk = min(remaining_pages, self.MAX_PAGES_PER_CHUNK)

                optimal_pages = self.find_optimal_chunk_size(reader, current_page, max_pages_for_this_chunk)

                chunk_bytes, chunk_size_mb = self.create_pdf_chunk(
                    reader, current_page, optimal_pages
                )

                if chunk_bytes:
                    chunk_info = {
                        'num': chunk_num,
                        'start_page': current_page + 1,
                        'end_page': current_page + optimal_pages,
                        'num_pages': optimal_pages,
                        'size_mb': chunk_size_mb
                    }
                    print(f"  Chunk {chunk_num}: pages {chunk_info['start_page']}-{chunk_info['end_page']} ({optimal_pages} pages), size {chunk_size_mb:.2f} MB")
                    chunks.append((chunk_bytes, chunk_info))
                    current_page += optimal_pages
                    chunk_num += 1
                else:
                    print(f"  Failed to create chunk {chunk_num}")
                    break

            print(f"Created {len(chunks)} chunks total\n")
            return chunks

        except Exception as e:
            print(f"Error chunking PDF: {e}")
            return []


def run_ocr(client: LLMClient, pdf_path: Path) -> str:
    """
    Step 3: Full OCR of the PDF with chunking as needed.

    Returns:
        Full markdown text
    """
    print(f"\n{'='*60}")
    print("STEP 3: Full OCR")
    print(f"{'='*60}")

    pdf_processor = PDFProcessor()
    needs_chunking, total_pages, size_mb, reason = pdf_processor.analyze_pdf(pdf_path)

    ocr_prompt = (
        "Extract all text from this PDF document and format it in markdown. "
        "Preserve the document structure, headings, tables, and formatting. "
        "IMPORTANT: Preserve all footnotes and endnotes. Where a footnote contains a URL, "
        "inline the URL directly in the text at the reference point as a markdown link "
        "(e.g. [text](https://...)). Do not drop footnote content or URLs."
    )

    if needs_chunking:
        print(f"  ⚠ Chunking required: {reason}")

        chunks = pdf_processor.chunk_pdf(pdf_path)
        if not chunks:
            raise RuntimeError("Failed to chunk PDF")

        print(f"Processing {len(chunks)} chunks...")
        all_markdown = []

        for chunk_bytes, chunk_info in chunks:
            print(f"\n  Chunk {chunk_info['num']}/{len(chunks)}:")
            chunk_markdown = client.chat_with_pdf(chunk_bytes, ocr_prompt)
            if chunk_markdown:
                all_markdown.append(chunk_markdown)
                print(f"  ✓ {len(chunk_markdown)} chars")
            else:
                print(f"  ⚠ Warning: Failed to process chunk {chunk_info['num']}")

        if not all_markdown:
            raise RuntimeError("Failed to extract text from any chunks")

        return "\n\n".join(all_markdown)

    else:
        print(f"  ✓ No chunking needed - processing entire PDF")

        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        full_markdown = client.chat_with_pdf(pdf_bytes, ocr_prompt)
        if not full_markdown:
            raise RuntimeError("Failed to extract text from PDF")

        print(f"  ✓ {len(full_markdown)} chars extracted")
        return full_markdown


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process PDF papers with eligibility triage and optional OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline:
  1. Fetch arXiv abstract → LLM triage (is it a black-box text-only jailbreak?)
  2. Download PDF, send first 8 pages → LLM deep triage (CPU-runnable?)
  3. Full OCR with chunking unless --skip-ocr is set

Examples:
  python paper_preprocessor.py --arxiv-id "2505.10066"
  python paper_preprocessor.py --arxiv-id "2505.10066" --skip-ocr
  python paper_preprocessor.py --arxiv-id "2505.10066" --skip-triage
  python paper_preprocessor.py --local-pdf "path/to/paper.pdf" --skip-abstract-triage

Note: Requires WENWEN_API_KEY unless both --skip-triage and --skip-ocr are set.
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pdf-link", type=str, help="Direct PDF download link")
    group.add_argument("--arxiv-id", type=str, help="arXiv paper ID (e.g., '2505.10066')")
    group.add_argument("--local-pdf", type=str, help="Path to local PDF file")

    parser.add_argument(
        "--model", type=str, default=DEFAULT_MODEL,
        help=f"Model to use for triage and OCR (default: {DEFAULT_MODEL})"
    )
    parser.add_argument(
        "--output-root", type=str, default="attacks_paper_info",
        help="Root directory to store processed paper assets (default: attacks_paper_info)"
    )
    parser.add_argument(
        "--skip-triage", action="store_true",
        help="Skip both eligibility checks (abstract and deep)"
    )
    parser.add_argument(
        "--skip-abstract-triage", action="store_true",
        help="Skip abstract triage only (still run deep triage on PDF)"
    )
    parser.add_argument(
        "--skip-ocr", action="store_true",
        help="Download and triage the PDF, but do not create OCR markdown"
    )

    return parser.parse_args()


if __name__ == "__main__":
    import requests

    args = parse_arguments()

    # Determine PDF source and ID
    if args.local_pdf:
        pdf_path = Path(args.local_pdf).resolve()
        if not pdf_path.exists():
            print(f"Error: Local PDF file not found: {pdf_path}")
            exit(1)
        pdf_id = pdf_path.stem
        arxiv_id = None
        print(f"Processing local PDF: {pdf_path}")
    elif args.pdf_link:
        pdf_id = args.pdf_link.split("/")[-1].replace(".pdf", "")
        arxiv_id = pdf_id
        pdf_path = None
        print(f"Processing PDF from URL: {args.pdf_link}")
    else:
        pdf_id = args.arxiv_id
        arxiv_id = args.arxiv_id
        pdf_path = None
        print(f"Processing arXiv PDF: {pdf_id}")

    # Initialize LLM client only when triage or OCR will call the model.
    client = LLMClient(model=args.model) if (not args.skip_triage or not args.skip_ocr) else None

    # --- Step 1: Abstract triage ---
    if arxiv_id and not args.skip_triage and not args.skip_abstract_triage:
        try:
            assert client is not None
            check_abstract_eligibility(client, arxiv_id)
        except EligibilityError as e:
            print(f"\n❌ REJECTED: {e}")
            exit(4)  # Exit code 4 = ineligible paper (CPU impractical / not a jailbreak)
    else:
        if args.skip_triage or args.skip_abstract_triage:
            print("\n⏭️  Skipping abstract triage")
        elif not arxiv_id:
            print("\n⏭️  No arXiv ID available, skipping abstract triage")

    # --- Download PDF if needed ---
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    output_dir = project_root / args.output_root / pdf_id
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path:
        pdf_filename = output_dir / f"{pdf_id}.pdf"

        if args.pdf_link:
            download_url = args.pdf_link
        else:
            download_url = f"https://arxiv.org/pdf/{pdf_id}"

        print(f"\nDownloading PDF to {pdf_filename}...")
        try:
            response = requests.get(download_url)
            response.raise_for_status()
            with open(pdf_filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ PDF saved to {pdf_filename}")
            pdf_path = pdf_filename
        except Exception as e:
            print(f"✗ Error downloading PDF: {e}")
            exit(1)
    else:
        pdf_filename = output_dir / f"{pdf_id}.pdf"
        if pdf_path.resolve() != pdf_filename.resolve():
            shutil.copy2(pdf_path, pdf_filename)
            print(f"PDF copied to {pdf_filename}")
            pdf_path = pdf_filename

    # --- Step 2: Deep triage (first 8 pages) ---
    if not args.skip_triage:
        try:
            assert client is not None
            check_deep_eligibility(client, pdf_path)
        except EligibilityError as e:
            print(f"\n❌ REJECTED: {e}")
            exit(4)  # Exit code 4 = ineligible paper (CPU impractical / not a jailbreak)
    else:
        print("\n⏭️  Skipping deep triage")

    if args.skip_ocr:
        print(f"\n✓ PDF ready at {pdf_path}")
        print(f"✓ Skipping OCR; all files saved in directory: {output_dir}")
        exit(0)

    # --- Step 3: Full OCR ---
    try:
        assert client is not None
        full_markdown = run_ocr(client, pdf_path)
    except RuntimeError as e:
        print(f"\n✗ OCR failed: {e}")
        exit(1)

    # Save output
    print(f"\n{'='*60}")
    output_filename = output_dir / f"{pdf_id}.md"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(full_markdown)

    print(f"✓ OCR result saved to {output_filename}")
    print(f"✓ All files saved in directory: {output_dir}")
    print("="*60)
