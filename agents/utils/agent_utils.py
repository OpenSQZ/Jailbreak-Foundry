#!/usr/bin/env python3
"""
Utility functions for agent workflows.

This module provides auxiliary functions for:
- Prompt assembly
- Command building
- Stream response parsing
- JSON communication handling

Supports pluggable agent backends via the AgentRunner base class:
- ClaudeAgentRunner: Claude Code CLI (for planner and implementer agents)
- CodexAgentRunner: OpenAI Codex CLI (for auditor agents)

Use create_agent_runner("claude", repo_root) or create_agent_runner("codex", repo_root)
to instantiate runners by name.
"""

import abc
import json
import os
import re
import subprocess
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class AgentResult:
    """Result from an agent pass with structured output."""
    success: bool
    output_text: str
    metadata: Dict[str, Any]
    error: Optional[str] = None


def build_prompt(
    repo_root: Path,
    pass_name: str,
    playbook_content: str,
    context: Dict[str, Any],
    extra_instructions: str = ""
) -> str:
    """
    Build a prompt for agent execution.

    Args:
        repo_root: Repository root path
        pass_name: Name of the pass (e.g., "attack-implementation")
        playbook_content: Content of the markdown playbook
        context: Context variables to inject into the prompt
        extra_instructions: Additional instructions to append

    Returns:
        Formatted prompt string
    """
    context_lines = [f"{key}: {value}" for key, value in context.items()]
    context_str = "\n".join(context_lines)

    prompt = f"""Repository root: {repo_root}
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


def find_in_json(data: Any, key: str) -> Any:
    """
    Recursively search for a key in a nested dict structure.

    Returns the first value found, or None if the key doesn't exist at any level.
    """
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for v in data.values():
            found = find_in_json(v, key)
            if found is not None:
                return found
    return None


def extract_json_result(text: str) -> Optional[Dict[str, Any]]:
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
    # Try 1: Look for ```json ... ``` blocks (preferred format)
    json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)

    if json_blocks:
        # Try to parse the last JSON block
        try:
            return json.loads(json_blocks[-1])
        except json.JSONDecodeError:
            pass  # Fall through to try raw JSON

    # Try 2: Look for raw JSON objects {...}
    json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)

    # Try parsing each found object, starting from the end (most recent)
    for json_str in reversed(json_objects):
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and ('status' in parsed or 'result' in parsed):
                return parsed
        except json.JSONDecodeError:
            continue

    return None


def _is_transient_network_error(error_output: str) -> bool:
    """
    Heuristics for transient proxy/network/server cancellation errors
    that are typically resolved by retrying.
    """
    if not error_output:
        return False
    text = error_output.lower()
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
        "at capacity",
        "overloaded",
        "organization has been disabled",
        "account has been disabled",
    ]
    return any(marker in text for marker in transient_markers)


# ---------------------------------------------------------------------------
# Agent Runner base class and subclasses
# ---------------------------------------------------------------------------

class AgentRunner(abc.ABC):
    """Abstract base class for agent CLI runners."""

    def __init__(self, repo_root: Optional[Path] = None, max_retries: int = 3):
        self.repo_root = repo_root or Path.cwd()
        self.max_retries = max(0, int(max_retries))

    @property
    @abc.abstractmethod
    def agent_name(self) -> str:
        """Human-readable agent name for log messages."""
        ...

    @property
    @abc.abstractmethod
    def bin_path(self) -> str:
        """Return the path to the agent binary (for environment validation)."""
        ...

    @abc.abstractmethod
    def _build_command(self, prompt: str, model: str) -> list:
        """Build the CLI command list for this agent."""
        ...

    @abc.abstractmethod
    def _parse_output(self, process: subprocess.Popen, log_file: Optional[Path] = None) -> AgentResult:
        """Parse subprocess output into an AgentResult."""
        ...

    def _get_env(self) -> Optional[dict]:
        """Return custom environment dict for the subprocess, or None to inherit."""
        return None

    def build_prompt(
        self,
        pass_name: str,
        playbook_content: str,
        context: Dict[str, Any],
        extra_instructions: str = ""
    ) -> str:
        """Build a prompt for agent execution (delegates to module-level function)."""
        return build_prompt(self.repo_root, pass_name, playbook_content, context, extra_instructions)

    def run(
        self,
        prompt: str,
        model: str,
        log_file: Optional[Path] = None,
    ) -> AgentResult:
        """
        Run the agent with the given prompt, with retry logic for transient errors.

        Args:
            prompt: Full prompt to send to agent
            model: Model identifier to use
            log_file: Optional file to log output

        Returns:
            AgentResult with parsed output
        """
        print(f"\n🧠 Starting {self.agent_name} pass")
        print(f"🤖 Model: {model}")
        if log_file:
            print(f"📝 Log: {log_file}")

        env = self._get_env()

        attempt = 0
        while True:
            cmd = self._build_command(prompt, model)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.repo_root,
                env=env
            )

            result = self._parse_output(process, log_file)

            if result.success:
                return result

            stderr_output = result.error or ""
            combined_output = stderr_output + "\n" + (result.output_text or "")
            retryable = _is_transient_network_error(combined_output)

            if not retryable or attempt >= self.max_retries:
                return result

            attempt += 1
            fixed_delay_seconds = 2.0
            print(f"♻️  Transient error detected (attempt {attempt}/{self.max_retries}). "
                  f"Retrying in {fixed_delay_seconds:.1f}s ...")
            time.sleep(fixed_delay_seconds)


class ClaudeAgentRunner(AgentRunner):
    """Claude Code CLI runner. Reads bin/flags from environment variables."""

    def __init__(self, repo_root: Optional[Path] = None, max_retries: int = 3):
        super().__init__(repo_root=repo_root, max_retries=max_retries)
        self._bin = os.environ.get("CLAUDE_CODE_BIN", "claude")
        self._flags = (
            os.environ.get("CLAUDE_CODE_FLAGS", "").split()
            if os.environ.get("CLAUDE_CODE_FLAGS")
            else []
        )

    @property
    def agent_name(self) -> str:
        return "Claude Code"

    @property
    def bin_path(self) -> str:
        return self._bin

    def _build_command(self, prompt: str, model: str) -> list:
        cmd = [self._bin]
        cmd.extend(["-p", "--verbose", "--output-format", "stream-json"])
        cmd.extend(["--model", model])
        # IS_SANDBOX=1 env var (set in _get_env) allows this flag under root
        cmd.append("--dangerously-skip-permissions")
        cmd.extend(["--permission-mode", "acceptEdits"])
        cmd.extend(self._flags)
        cmd.append(prompt)
        return cmd

    def _get_env(self) -> dict:
        """Return env dict with IS_SANDBOX=1 so Claude Code skips permission prompts."""
        env = os.environ.copy()
        env["IS_SANDBOX"] = "1"
        return env

    def _parse_output(
        self,
        process: subprocess.Popen,
        log_file: Optional[Path] = None
    ) -> AgentResult:
        """Parse streaming JSON output from Claude Code CLI."""
        accumulated_text = ""
        tool_count = 0
        start_time = time.time()
        model_name = "unknown"

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
                    # Content blocks are inside message.content[]
                    content_blocks = data.get("message", {}).get("content", [])
                    for block in content_blocks:
                        block_type = block.get("type", "")
                        if block_type == "text" and block.get("text"):
                            print(f"\n\033[94m{block['text']}\033[0m\n", end="", flush=True)
                            accumulated_text += block["text"] + "\n\n"
                        elif block_type == "tool_use":
                            tool_count += 1
                            tool_name = block.get("name", "unknown")
                            tool_input = block.get("input", {})
                            # Show tool name + key input (e.g., file path)
                            input_preview = ""
                            if "file_path" in tool_input:
                                input_preview = f" → {tool_input['file_path']}"
                            elif "command" in tool_input:
                                input_preview = f" → {tool_input['command'][:100]}"
                            elif "pattern" in tool_input:
                                input_preview = f" → {tool_input['pattern']}"
                            print(f"\n🔧 Tool #{tool_count}: {tool_name}{input_preview}")

                    if log_handle:
                        log_handle.seek(0)
                        log_handle.write(accumulated_text)
                        log_handle.truncate()
                        log_handle.flush()

                elif msg_type == "user":
                    # Tool results come back as user messages
                    content_blocks = data.get("message", {}).get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "tool_result":
                            content = block.get("content", "")
                            if isinstance(content, str):
                                size = len(content)
                            else:
                                size = len(str(content))
                            print(f"   ✅ {size} chars result")

                elif msg_type == "result":
                    duration = data.get("duration_ms", 0)
                    cost = data.get("total_cost_usd", 0)
                    num_turns = data.get("num_turns", 0)
                    end_time = time.time()
                    total_time = int(end_time - start_time)
                    print(f"\n\n🎯 Completed in {duration}ms ({total_time}s total)")
                    print(f"📊 Stats: {tool_count} tools, {num_turns} turns, {len(accumulated_text)} chars, ${cost:.4f}")

        except Exception as e:
            parse_exception = (e, traceback.format_exc())
        finally:
            if log_handle:
                log_handle.close()

        process.wait()

        if parse_exception is not None:
            _, error_traceback = parse_exception
            return AgentResult(
                success=False,
                output_text=accumulated_text,
                metadata={"tool_count": tool_count, "model": model_name},
                error=f"Exception during stream parsing:\n{error_traceback}"
            )

        if process.returncode != 0:
            stderr_output = ""
            if process.stderr:
                try:
                    stderr_output = process.stderr.read()
                    if isinstance(stderr_output, bytes):
                        stderr_output = stderr_output.decode('utf-8', errors='replace')
                except Exception:
                    stderr_output = f"Failed to read stderr: {traceback.format_exc()}"
            else:
                stderr_output = "No stderr available"

            return AgentResult(
                success=False,
                output_text=accumulated_text,
                metadata={"tool_count": tool_count, "model": model_name, "returncode": process.returncode},
                error=f"Process failed with return code {process.returncode}\n\nStderr:\n{stderr_output}"
            )

        result_json = extract_json_result(accumulated_text)

        return AgentResult(
            success=True,
            output_text=accumulated_text,
            metadata={
                "tool_count": tool_count,
                "model": model_name,
                "result_data": result_json
            }
        )


class CodexAgentRunner(AgentRunner):
    """OpenAI Codex CLI runner. Reads bin/flags from environment variables."""

    def __init__(self, repo_root: Optional[Path] = None, max_retries: int = 3):
        super().__init__(repo_root=repo_root, max_retries=max_retries)
        self._bin = os.environ.get("CODEX_BIN", "codex")
        self._flags = (
            os.environ.get("CODEX_FLAGS", "").split()
            if os.environ.get("CODEX_FLAGS")
            else []
        )

    @property
    def agent_name(self) -> str:
        return "Codex"

    @property
    def bin_path(self) -> str:
        return self._bin

    def _build_command(self, prompt: str, model: str) -> list:
        cmd = [
            self._bin, "exec",
            prompt,
            "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
            "--model", model,
            "--json",
        ]
        cmd.extend(self._flags)
        return cmd

    def _parse_output(
        self,
        process: subprocess.Popen,
        log_file: Optional[Path] = None
    ) -> AgentResult:
        """Parse JSONL stream output from Codex CLI (--json mode).

        Event types:
        - thread.started: session info
        - turn.started: new turn begins
        - item.completed: message or tool result with item.type and item.text
        - turn.completed: usage stats
        - error: error/retry messages
        """
        accumulated_text = ""
        tool_count = 0
        start_time = time.time()

        log_handle = None
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_handle = open(log_file, 'w')

        print("🚀 Parsing Codex JSONL stream...")

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

                event_type = data.get("type", "")

                if event_type == "thread.started":
                    session_id = data.get("thread_id", "unknown")
                    print(f"🆔 Session: {session_id}")

                elif event_type == "item.started":
                    item = data.get("item", {})
                    item_type = item.get("type", "")
                    if item_type == "command_execution":
                        tool_count += 1
                        cmd = item.get("command", "")
                        print(f"\n🔧 Tool #{tool_count}: {cmd[:200]}")

                elif event_type == "item.completed":
                    item = data.get("item", {})
                    item_type = item.get("type", "")
                    text = item.get("text", "")

                    if item_type == "agent_message" and text:
                        print(f"\n\033[94m{text}\033[0m\n", end="", flush=True)
                        accumulated_text += text + "\n\n"
                    elif item_type == "command_execution":
                        exit_code = item.get("exit_code", None)
                        output = item.get("aggregated_output", "")
                        status = "✅" if exit_code == 0 else f"❌ (exit {exit_code})"
                        print(f"   {status} {len(output)} chars output")

                    if log_handle:
                        log_handle.seek(0)
                        log_handle.write(accumulated_text)
                        log_handle.truncate()
                        log_handle.flush()

                elif event_type == "turn.completed":
                    usage = data.get("usage", {})
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    cached = usage.get("cached_input_tokens", 0)
                    end_time = time.time()
                    total_time = int(end_time - start_time)
                    print(f"\n\n🎯 Completed in {total_time}s")
                    print(f"📊 Stats: {tool_count} tools, {len(accumulated_text)} chars, "
                          f"tokens: {input_tokens} in ({cached} cached) / {output_tokens} out")

                elif event_type == "error":
                    msg = data.get("message", "")
                    print(f"\n⚠️  {msg}")

        except Exception as e:
            parse_exception = (e, traceback.format_exc())
        finally:
            if log_handle:
                log_handle.close()

        process.wait()

        if parse_exception is not None:
            _, error_traceback = parse_exception
            return AgentResult(
                success=False,
                output_text=accumulated_text,
                metadata={"tool_count": tool_count},
                error=f"Exception during stream parsing:\n{error_traceback}"
            )

        if process.returncode != 0:
            stderr_output = ""
            if process.stderr:
                try:
                    stderr_output = process.stderr.read()
                    if isinstance(stderr_output, bytes):
                        stderr_output = stderr_output.decode('utf-8', errors='replace')
                except Exception:
                    stderr_output = f"Failed to read stderr: {traceback.format_exc()}"
            else:
                stderr_output = "No stderr available"

            if stderr_output:
                print(f"\n❌ Codex stderr:\n{stderr_output}")

            return AgentResult(
                success=False,
                output_text=accumulated_text,
                metadata={"tool_count": tool_count, "returncode": process.returncode},
                error=f"Process failed with return code {process.returncode}\n\nStderr:\n{stderr_output}"
            )

        result_json = extract_json_result(accumulated_text)

        return AgentResult(
            success=True,
            output_text=accumulated_text,
            metadata={
                "tool_count": tool_count,
                "result_data": result_json
            }
        )


# ---------------------------------------------------------------------------
# Agent registry and factory
# ---------------------------------------------------------------------------

_AGENT_REGISTRY: Dict[str, type] = {
    "claude": ClaudeAgentRunner,
    "codex": CodexAgentRunner,
}


def create_agent_runner(
    agent_type: str,
    repo_root: Optional[Path] = None,
    max_retries: int = 3
) -> AgentRunner:
    """
    Create an AgentRunner by name.

    Args:
        agent_type: One of "claude", "codex"
        repo_root: Repository root path
        max_retries: Number of retries for transient errors

    Returns:
        Configured AgentRunner instance

    Raises:
        ValueError: If agent_type is not recognized
    """
    cls = _AGENT_REGISTRY.get(agent_type.lower())
    if cls is None:
        valid = ", ".join(sorted(_AGENT_REGISTRY))
        raise ValueError(f"Unknown agent type {agent_type!r}. Valid types: {valid}")
    return cls(repo_root=repo_root, max_retries=max_retries)


# Backward compatibility aliases
ClaudeCodeRunner = ClaudeAgentRunner
CodexRunner = CodexAgentRunner


def validate_environment(agent_bin: str, required_files: list[Path]) -> None:
    """
    Validate that all required tools and files exist.

    Args:
        agent_bin: Path to agent binary (claude or codex)
        required_files: List of required file paths

    Raises:
        SystemExit: If validation fails
    """
    import sys

    # Check for agent binary
    if subprocess.run(
        ["command", "-v", agent_bin],
        shell=True,
        capture_output=True
    ).returncode != 0:
        print(f"❌ {agent_bin} not found in PATH", file=sys.stderr)
        sys.exit(1)

    # Check for required files
    for file_path in required_files:
        if not file_path.exists():
            print(f"❌ Missing required file: {file_path}", file=sys.stderr)
            sys.exit(1)

    print("✅ Environment validation passed")
