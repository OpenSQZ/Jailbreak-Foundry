import argparse
import base64
import json
import os
import re
import shutil
from io import BytesIO
from pathlib import Path
from typing import Optional

import pymupdf  # local CPU text-layer extraction; the router hangs on image-dense PDFs

from openai import OpenAI
from PyPDF2 import PdfReader, PdfWriter

# Default model ID (env-overridable so a down/overloaded channel can be
# swapped without editing the workflow that invokes this script).
DEFAULT_MODEL = os.environ.get("PREPROCESS_MODEL", "ora/gpt-5.6")

# LiteLLM proxy settings
DEFAULT_BASE_URL = "https://router.ai.iiis.co:9443/v1"

DEFAULT_API_KEY_ENV = "IIIS_API_KEY"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader so IIIS_API_KEY is picked up automatically."""
    if not path.exists():
        return
    try:
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception:
        pass


# Load .env from repo root (parent of agents/) at import time.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_load_dotenv(_REPO_ROOT / ".env")

# Capability envelope: single source of truth for admissible payload
# modalities. The preprocessor enforces it in Python, not just in prompt text.
import sys as _sys
_sys.path.insert(0, str(_REPO_ROOT))
try:
    from agents.utils.capability import payload_ok as _payload_ok
except Exception:  # pragma: no cover
    _payload_ok = None


# ---------------------------------------------------------------------------
# Eligibility check prompts
# ---------------------------------------------------------------------------

ABSTRACT_TRIAGE_PROMPT = """\
You are an expert classifier for jailbreak attack research papers.

Based ONLY on the title and abstract below, determine whether this paper proposes a NEW jailbreak attack method that is:
1. A jailbreak attack on LLMs (not defense, not survey, not benchmark)
2. Black-box (only needs API access, no gradients/weights/logits)
3. Uses only text and/or raster-image inputs to the remote victim model (vision-language and multimodal image attacks are allowed; audio and video attacks are not supported)
4. Practical to run on CPU (no GPU/training required from reading the abstract)

Do NOT reject a paper merely because the remote victim model accepts images or
because the paper calls the attack vision-language or multimodal. If the
abstract does not establish whether local GPU, training, or model inference is
required, leave that question to the deep triage instead of rejecting it here.

Also extract the PAYLOAD MODALITIES: what does the attack actually feed into
the victim model? Return a JSON array of one or more of:
"text", "image", "video", "audio", "3d", "other".
- Static raster images (typographic prompts, adversarial images, screenshots,
  charts, figures) -> include "image".
- A sequence of video frames or temporally-ordered frames/subtitles -> include
  "video" (NOT "image").
- Pure text prompts/templates, even if the victim is a VLM -> ["text"] only.
- Cannot tell from abstract -> [] (empty array).

Title: {title}

Abstract: {abstract}

Respond with ONLY a JSON object:
{{
  "eligible": true or false,
  "payload_modalities": ["text"|"image"|"video"|"audio"|"3d"|"other", ...],
  "surrogate_required": true|false|null,
  "reason": "one sentence explanation"
}}
"""

DEEP_TRIAGE_PROMPT = """\
You are an expert classifier for jailbreak attack research papers.

You are given the first 3 pages of a paper. Determine whether this paper's proposed attack method is PRACTICALLY CPU-runnable in a black-box setting. The supported victim inputs are text and raster images, and the victim output must be text.

Specifically, check for these DISQUALIFYING signals:
- Uses transformers library to load or run a local model (e.g., for perplexity filtering, token scoring)
- Requires torch/cuda for any part of the attack pipeline
- Needs to calculate perplexity, token probabilities, or embeddings locally
- Requires fine-tuning or training any model
- Needs gradient computation or backpropagation
- Requires audio, video, or another unsupported input modality
- Only works with white-box/gray-box access (needs logits, hidden states, model internals)
- Requires running inference on a local LLM (not via API)
- Needs a local white-box surrogate model to generate adversarial examples that are then transferred to the (black-box) victim

Notes:
- Sending text and/or raster images to a remote vision-language victim API IS acceptable.
- Creating typographic or otherwise programmatic images locally with CPU-safe libraries IS acceptable.
- Using an external model API (like OpenAI, Claude, etc.) for generation/scoring IS acceptable and counts as CPU-runnable.
- Do NOT treat vision-language or multimodal terminology alone as disqualifying. Reject only when the actual method requires unsupported modalities or non-CPU local computation.

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
        """Send a PDF via the Responses API (input_file) and return text.

        The IIIS router does not forward inline PDF `file` parts in chat
        completions, but it does accept the Responses API `input_file` part,
        so OCR and deep triage go through /v1/responses here.
        """
        chunk_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": "paper.pdf",
                            "file_data": f"data:application/pdf;base64,{chunk_base64}",
                        },
                        {"type": "input_text", "text": text_prompt},
                    ],
                }
            ],
        )
        parts = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) == "message":
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", None) == "output_text":
                        parts.append(getattr(c, "text", ""))
        return "".join(parts)


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

    # Check runtime support without applying the image-only paper-search policy.
    mods = result.get("payload_modalities") or []
    if _payload_ok is not None:
        ok, reason = _payload_ok(mods, require_image=False)
        if not ok:
            print(f"  Result: eligible=False (payload check: {reason}) "
                  f"payload={mods} llm_reason={result.get('reason')}")
            raise EligibilityError(
                f"Paper {arxiv_id} failed payload triage: {reason} (payload={mods})"
            )

    print(f"  Result: eligible={result.get('eligible')} payload={mods} reason={result.get('reason')}")

    if not result.get("eligible"):
        raise EligibilityError(
            f"Paper {arxiv_id} failed abstract triage: {result.get('reason')}"
        )

    return result


def check_deep_eligibility(client: LLMClient, pdf_path: Path) -> dict:
    """
    Step 2: Send first 3 pages of PDF to verify CPU-runnability.

    Returns:
        dict with 'eligible' (bool), 'reason' (str), 'disqualifying_signals' (list)

    Raises:
        EligibilityError: If paper is not eligible
    """
    print(f"\n{'='*60}")
    print("STEP 2: Deep eligibility check (first 3 pages)")
    print(f"{'='*60}")

    # Send the text layer, not the PDF: the router silently drops the Responses
    # API input_file part on some channels, and the model then triages an empty
    # document and rejects every paper.
    doc = pymupdf.open(str(pdf_path))
    try:
        total_pages = doc.page_count
        pages_to_check = min(3, total_pages)
        parts = []
        for i in range(pages_to_check):
            text = (doc[i].get_text("text") or "").strip()
            if text:
                parts.append(f"<!-- page {i + 1} -->\n\n{text}")
    finally:
        doc.close()
    excerpt = "\n\n".join(parts)

    print(f"  Querying {client.model} for deep triage...")

    if excerpt:
        print(f"  Sending {pages_to_check}/{total_pages} pages as text ({len(excerpt)} chars)")
        response_text = client.chat([
            {"role": "user", "content": f"{DEEP_TRIAGE_PROMPT}\n\n---\n\n{excerpt}"}
        ])
    else:
        # Image-only pages (scanned paper): inline PDF is the only option left.
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(BytesIO(f.read()))
        writer = PdfWriter()
        for i in range(pages_to_check):
            writer.add_page(reader.pages[i])
        pdf_output = BytesIO()
        writer.write(pdf_output)
        chunk_bytes = pdf_output.getvalue()
        chunk_base64_mb = len(base64.b64encode(chunk_bytes)) / (1024 * 1024)
        print(f"  No text layer in first {pages_to_check} pages; "
              f"falling back to inline PDF ({chunk_base64_mb:.1f} MB base64)")
        response_text = client.chat_with_pdf(chunk_bytes, DEEP_TRIAGE_PROMPT)

    if not (response_text or "").strip():
        # An empty reply means the document never reached the model. Failing
        # loudly beats recording it as an eligibility rejection.
        raise RuntimeError(
            f"Deep triage got an empty reply from {client.model}; the document "
            f"likely never reached the model. Not treating this as a rejection."
        )

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
# PDF processing (local text-layer extraction)
# ---------------------------------------------------------------------------

def run_ocr(pdf_path: Path) -> str:
    """Step 3: Extract the paper text layer locally with PyMuPDF.

    The IIIS router hangs on image-dense inline PDFs (one FigStep page is
    4.9 MB), so extraction runs locally on CPU instead of uploading chunks
    to a remote multimodal model. Only the PDF text layer is read; figure
    bitmaps are not OCR'd. For FigStep this is sufficient because every
    algorithm element and prompt template lives in the text layer, and the
    typographic images are outputs the attack renders itself.
    """
    print(f"\n{'='*60}")
    print("STEP 3: Local text extraction (PyMuPDF)")
    print(f"{'='*60}")

    doc = pymupdf.open(str(pdf_path))
    try:
        page_count = doc.page_count
        parts = []
        for index in range(page_count):
            text = (doc[index].get_text("text") or "").strip()
            if text:
                parts.append(f"<!-- page {index + 1} -->\n\n{text}")
            else:
                parts.append(f"<!-- page {index + 1}: no text layer (image-only page) -->")
    finally:
        doc.close()

    markdown = "\n\n".join(parts)
    if not markdown.strip():
        raise RuntimeError(f"No extractable text layer in {pdf_path}")

    print(f"  ✓ {len(markdown)} chars from {page_count} pages")
    return markdown


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
  1. Fetch arXiv abstract → LLM triage (is it a supported black-box jailbreak?)
  2. Download PDF, send first 3 pages → LLM deep triage (CPU-runnable?)
  3. Local text-layer extraction (PyMuPDF) unless --skip-ocr is set

Examples:
  python paper_preprocessor.py --arxiv-id "2505.10066"
  python paper_preprocessor.py --arxiv-id "2505.10066" --skip-ocr
  python paper_preprocessor.py --arxiv-id "2505.10066" --skip-triage
  python paper_preprocessor.py --local-pdf "path/to/paper.pdf" --skip-abstract-triage

Note: Requires IIIS_API_KEY unless --skip-triage is set (OCR is local, no key needed).
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
    client = LLMClient(model=args.model) if not args.skip_triage else None

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

    # --- Step 2: Deep triage (first 3 pages) ---
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

    # --- Step 3: Local text extraction (no model call) ---
    try:
        full_markdown = run_ocr(pdf_path)
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
