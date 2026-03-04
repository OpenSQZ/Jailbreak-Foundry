#!/usr/bin/env python3
"""
Utility functions for cursor agent workflow.

This module provides auxiliary functions for:
- Prompt assembly
- Command building
- Stream response parsing
- JSON communication handling
"""

import json
import subprocess
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional


@dataclass
class AgentResult:
    """Result from a cursor agent pass with structured output."""
    success: bool
    output_text: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


class CursorAgentRunner:
    """Handles cursor-agent execution and stream parsing."""

    def __init__(
        self,
        cursor_agent_bin: str = "cursor-agent",
        cursor_agent_flags: Optional[list] = None,
        repo_root: Optional[Path] = None,
        max_retries: int = 3
    ):
        """
        Initialize cursor agent runner.

        Args:
            cursor_agent_bin: Path to cursor-agent binary
            cursor_agent_flags: Additional flags for cursor-agent
            repo_root: Repository root path
            max_retries: Number of retries for transient network/proxy errors
        """
        self.cursor_agent_bin = cursor_agent_bin
        self.cursor_agent_flags = cursor_agent_flags or []
        self.repo_root = repo_root or Path.cwd()
        self.max_retries = max(0, int(max_retries))

    def _is_transient_network_error(self, stderr_output: str) -> bool:
        """
        Heuristics for transient proxy/network/server cancellation errors
        that are typically resolved by retrying.
        """
        if not stderr_output:
            return False
        text = stderr_output.lower()
        transient_markers = [
            "http/2 stream closed with error code cancel",
            "http2 stream closed with error code cancel",
            "goaway",
            "protocol_error",
            "socket error or timeout",
            "connection reset by peer",
            "econnreset",
            "timed out",
            "timeout",
            "temporarily unavailable",
            "try again",
        ]
        return any(marker in text for marker in transient_markers)

    def build_prompt(
        self,
        pass_name: str,
        playbook_content: str,
        context: Dict[str, Any],
        extra_instructions: str = ""
    ) -> str:
        """
        Build a prompt for cursor agent execution.

        Args:
            pass_name: Name of the pass (e.g., "attack-implementation")
            playbook_content: Content of the markdown playbook
            context: Context variables to inject into the prompt
            extra_instructions: Additional instructions to append

        Returns:
            Formatted prompt string
        """
        # Build context section
        context_lines = [f"{key}: {value}" for key, value in context.items()]
        context_str = "\n".join(context_lines)

        prompt = f"""Repository root: {self.repo_root}
Pass type: {pass_name}

Context:
{context_str}

Follow the playbook below. Execute the task and respond with structured JSON at the end.

{playbook_content}

{extra_instructions}

IMPORTANT: Your final response MUST include a JSON block in this format:
```json
{{
  "status": "success|failure",
  "result": {{
    // Your structured result data here
  }},
  "error": "error message if any"
}}
```
"""
        return prompt

    def parse_stream_output(
        self,
        process: subprocess.Popen,
        log_file: Optional[Path] = None
    ) -> AgentResult:
        """
        Parse streaming JSON output from cursor-agent.

        Args:
            process: Subprocess running cursor-agent
            log_file: Optional file to log output to

        Returns:
            AgentResult with parsed output and metadata
        """
        accumulated_text = ""
        tool_count = 0
        start_time = time.time()
        model_name = "unknown"

        # Open log file for live updates if provided
        log_handle = None
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_handle = open(log_file, 'w')

        print("🚀 Parsing stream output...")

        parse_exception = None
        try:
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type", "")
                subtype = data.get("subtype", "")

                if msg_type == "system":
                    if subtype == "init":
                        model_name = data.get("model", "unknown")
                        print(f"🤖 Using model: {model_name}")

                elif msg_type == "assistant":
                    content = data.get("message", {}).get("content", [{}])[0].get("text", "")
                    # Without --stream-partial-output, each message is a complete segment
                    # We need to concatenate all segments to build the full response
                    if content:
                        # Print the new segment in light blue with indentation
                        # ANSI color code: \033[94m = light blue, \033[0m = reset
                        print(f"\n\033[94m{content}\033[0m\n", end="", flush=True)
                        # Append to accumulated text with line break for log file
                        accumulated_text += content + "\n\n"

                    # Write live updates to log file
                    if log_handle:
                        log_handle.seek(0)
                        log_handle.write(accumulated_text)
                        log_handle.truncate()
                        log_handle.flush()

                elif msg_type == "tool_call":
                    if subtype == "started":
                        tool_count += 1
                        tool_call = data.get("tool_call", {})

                        if "writeToolCall" in tool_call:
                            path = tool_call["writeToolCall"].get("args", {}).get("path", "unknown")
                            print(f"\n🔧 Tool #{tool_count}: Creating {path}")
                        elif "readToolCall" in tool_call:
                            path = tool_call["readToolCall"].get("args", {}).get("path", "unknown")
                            print(f"\n📖 Tool #{tool_count}: Reading {path}")
                        elif "bashToolCall" in tool_call:
                            print(f"\n⚙️  Tool #{tool_count}: Running bash command")

                    elif subtype == "completed":
                        tool_call = data.get("tool_call", {})
                        if "writeToolCall" in tool_call:
                            result = tool_call["writeToolCall"].get("result", {}).get("success", {})
                            lines = result.get("linesCreated", 0)
                            size = result.get("fileSize", 0)
                            print(f"   ✅ Created {lines} lines ({size} bytes)")
                        elif "readToolCall" in tool_call:
                            result = tool_call["readToolCall"].get("result", {}).get("success", {})
                            lines = result.get("totalLines", 0)
                            print(f"   ✅ Read {lines} lines")

                elif msg_type == "result":
                    duration = data.get("duration_ms", 0)
                    end_time = time.time()
                    total_time = int(end_time - start_time)

                    print(f"\n\n🎯 Completed in {duration}ms ({total_time}s total)")
                    print(f"📊 Stats: {tool_count} tools, {len(accumulated_text)} chars")
        except Exception as e:
            parse_exception = (e, traceback.format_exc())
        finally:
            # Close log file handle
            if log_handle:
                log_handle.close()

        # Wait for process to complete
        process.wait()

        # Check for parsing exceptions first
        if parse_exception is not None:
            exc, error_traceback = parse_exception
            return AgentResult(
                success=False,
                output_text=accumulated_text,
                metadata={"tool_count": tool_count, "model": model_name},
                error=f"Exception during stream parsing:\n{error_traceback}"
            )

        # Check for process errors
        if process.returncode != 0:
            # Read stderr - handle both text and bytes
            stderr_output = ""
            if process.stderr:
                try:
                    # Try reading as text first
                    stderr_output = process.stderr.read()
                    if isinstance(stderr_output, bytes):
                        stderr_output = stderr_output.decode('utf-8', errors='replace')
                except Exception as e:
                    stderr_output = f"Failed to read stderr: {traceback.format_exc()}"
            else:
                stderr_output = "No stderr available"
            
            return AgentResult(
                success=False,
                output_text=accumulated_text,
                metadata={"tool_count": tool_count, "model": model_name, "returncode": process.returncode},
                error=f"Process failed with return code {process.returncode}\n\nStderr:\n{stderr_output}"
            )

        # Extract JSON result from output
        result_json = self._extract_json_result(accumulated_text)

        return AgentResult(
            success=True,
            output_text=accumulated_text,
            metadata={
                "tool_count": tool_count,
                "model": model_name,
                "result_data": result_json
            }
        )

    def _extract_json_result(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON result block from agent output.

        Tries multiple patterns:
        1. Markdown code blocks: ```json {...} ```
        2. Raw JSON objects: {...}

        Args:
            text: Full text output from agent

        Returns:
            Parsed JSON dict or None if not found
        """
        import re

        # Try 1: Look for ```json ... ``` blocks (preferred format)
        json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)

        if json_blocks:
            # Try to parse the last JSON block
            try:
                return json.loads(json_blocks[-1])
            except json.JSONDecodeError:
                pass  # Fall through to try raw JSON

        # Try 2: Look for raw JSON objects {...}
        # Find all potential JSON objects (opening { to closing })
        json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)

        # Try parsing each found object, starting from the end (most recent)
        for json_str in reversed(json_objects):
            try:
                parsed = json.loads(json_str)
                # Verify it looks like our expected structure
                if isinstance(parsed, dict) and ('status' in parsed or 'result' in parsed):
                    return parsed
            except json.JSONDecodeError:
                continue

        return None

    def run(
        self,
        prompt: str,
        model: str = "sonnet-4.5",
        log_file: Optional[Path] = None,
        use_proxychains: bool = True
    ) -> AgentResult:
        """
        Run cursor-agent with the given prompt.

        Args:
            prompt: Full prompt to send to agent
            model: Model to use
            log_file: Optional file to log output
            use_proxychains: Whether to use proxychains4

        Returns:
            AgentResult with parsed output
        """
        print(f"\n🧠 Starting cursor-agent pass")
        print(f"🤖 Model: {model}")
        if log_file:
            print(f"📝 Log: {log_file}")

        # Build command
        cmd = []
        if use_proxychains:
            cmd.append("proxychains4")

        cmd.extend([
            self.cursor_agent_bin,
            "-p",
            "--force",
            "--output-format", "stream-json",
            "--model", model,
        ])
        cmd.extend(self.cursor_agent_flags)
        cmd.append(prompt)

        # Retry loop for transient proxy/network errors
        attempt = 0

        while True:
            # Run process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.repo_root
            )

            result = self.parse_stream_output(process, log_file)

            # Success fast-path
            if result.success:
                return result

            # Determine if retryable
            stderr_output = result.error or ""
            retryable = self._is_transient_network_error(stderr_output)

            if not retryable or attempt >= self.max_retries:
                # Either non-retryable or out of retries
                return result

            attempt += 1
            # Fixed delay between retries
            fixed_delay_seconds = 2.0
            print(f"♻️  Transient error detected (attempt {attempt}/{self.max_retries}). "
                  f"Retrying in {fixed_delay_seconds:.1f}s ...")
            time.sleep(fixed_delay_seconds)


def validate_environment(cursor_agent_bin: str, required_files: list[Path]) -> None:
    """
    Validate that all required tools and files exist.

    Args:
        cursor_agent_bin: Path to cursor-agent binary
        required_files: List of required file paths

    Raises:
        SystemExit: If validation fails
    """
    import sys

    # Check for cursor-agent binary
    if subprocess.run(
        ["command", "-v", cursor_agent_bin],
        shell=True,
        capture_output=True
    ).returncode != 0:
        print(f"❌ {cursor_agent_bin} not found in PATH", file=sys.stderr)
        sys.exit(1)

    # Check for required files
    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ Missing required file: {file_path}", file=sys.stderr)
            sys.exit(1)

    print("✅ Environment validation passed")
