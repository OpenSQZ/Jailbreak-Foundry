"""
LLM interface for API-based models using LiteLLM.
"""

import logging

logger = logging.getLogger(__name__)

import os
import json
from typing import Dict, List, Optional, Union, Any, Tuple
import time

# Import litellm with a try-except to provide informative error
try:
    import litellm
    from litellm import completion
    litellm.suppress_debug_info = True
    litellm.drop_params = True
except ImportError:
    raise ImportError(
        "LiteLLM is required to use LLMLiteLLM. "
        "Install it with `pip install litellm`."
    )

from ..llm.base import BaseLLM
from ..defenses import DefenseFactory
from ..cost_tracker import CostTracker
from ..payloads import (
    AttackPayload,
    ImagePart,
    ModelCapabilities,
    TextPart,
    infer_prompt_modalities,
)


class RichResponse(str):
    """
    A string subclass that contains both the response text and usage information.
    This class behaves exactly like a string for backward compatibility.
    """
    def __new__(cls, text: str, usage: Dict[str, int] = None, reasoning_content: str = None):
        # Create a new string instance
        instance = super().__new__(cls, text)
        # Set default values if not provided (needed for pickle/deepcopy support)
        instance.usage = usage if usage is not None else {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "reasoning_tokens": 0}
        instance.reasoning_content = reasoning_content if reasoning_content is not None else ""
        return instance

    def __getnewargs__(self):
        """Return arguments for pickle/deepcopy to use when reconstructing the object."""
        return (str(self), getattr(self, 'usage', None), getattr(self, 'reasoning_content', None))

    def get_usage(self) -> Dict[str, int]:
        """Get the token usage information."""
        return self.usage.copy()

    def get_reasoning_content(self) -> str:
        """Get the reasoning content."""
        return self.reasoning_content


class RichResponseList(list):
    """
    A list subclass that behaves like a normal list but has get_usage() and
    get_reasoning_content() methods to aggregate information from RichResponse items.
    """
    def get_usage(self) -> Dict[str, int]:
        """Get aggregated token usage information from all RichResponse items."""
        total_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "reasoning_tokens": 0
        }
        for item in self:
            if isinstance(item, RichResponse):
                usage = item.get_usage()
                total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
                total_usage["completion_tokens"] += usage.get("completion_tokens", 0)
                total_usage["total_tokens"] += usage.get("total_tokens", 0)
                total_usage["reasoning_tokens"] += usage.get("reasoning_tokens", 0)
        return total_usage

    def get_reasoning_content(self) -> List[str]:
        """Get list of reasoning content from all RichResponse items."""
        return [item.get_reasoning_content() if isinstance(item, RichResponse) else "" for item in self]

class LLMLiteLLM(BaseLLM):
    """
    Implementation of BaseLLM using LiteLLM for API-based models.
    
    This class supports various model providers like OpenAI, Together, Anthropic, etc.
    """
    
    @classmethod
    def from_config(
        cls,
        model_name: str,
        provider: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ) -> "LLMLiteLLM":
        """
        Create an LLMLiteLLM instance from a user-friendly configuration.

        This factory method handles provider-specific logic, such as API key
        environment variables and API base URL overrides for certain providers.

        Args:
            model_name: Name of the model.
            provider: User-facing provider name (e.g., 'openai', 'aliyun').
            api_key: Optional API key.
            api_base: Optional API base URL.
            **kwargs: Additional parameters to pass to the LLM.

        Returns:
            An instance of LLMLiteLLM.
        """
        llm_provider = provider
        llm_api_key = api_key
        llm_api_base = api_base
        
        init_kwargs = kwargs.copy()

        if provider == "openai":
            llm_api_key = api_key or os.getenv("OPENAI_API_KEY")
            llm_api_base = api_base or os.getenv("OPENAI_API_BASE")
        elif provider == "anthropic":
            llm_api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        elif provider == "azure":
            llm_api_key = api_key or os.getenv("AZURE_API_KEY")
            llm_api_base = api_base or os.getenv("AZURE_API_BASE")
        elif provider == "aliyun":
            llm_provider = "openai"
            llm_api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
            llm_api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        elif provider == "wenwen":
            # DEPRECATED: wenwen endpoint (api.wenwen-ai.com) is retired.
            # Alias to the IIIS router so existing YAMLs/configs keep working.
            # Prefer provider: iiis with a prefixed model (e.g. jwg/gpt-4o).
            llm_provider = "openai"
            llm_api_key = api_key or os.getenv("IIIS_API_KEY") or os.getenv("WENWEN_API_KEY")
            llm_api_base = "https://router.ai.iiis.co:9443/v1"
        elif provider == "infini":
            llm_provider = "openai"
            llm_api_key = api_key or os.getenv("INFINI_API_KEY")
            llm_api_base = "https://cloud.infini-ai.com/maas/v1"
        elif provider == "iiis":
            llm_provider = "openai"
            llm_api_key = api_key or os.getenv("IIIS_API_KEY")
            llm_api_base = "https://router.ai.iiis.co:9443/v1"
        elif provider == "local-llama2-7b":
            llm_provider = "openai"
            llm_api_base = "http://10.210.22.10:30254/v1"
        elif provider == "local-llama3-8b":
            llm_provider = "openai"
            llm_api_base = "http://10.210.22.10:30253/v1"
        elif provider == "local-deepseek-abliterated":
            # Self-hosted abliterated (refusal-removed) DeepSeek-V4-Flash endpoint,
            # OpenAI-compatible. Used as the default judge so evaluation is not
            # biased by a safety-aligned model refusing to score harmful content.
            llm_provider = "openai"
            llm_api_key = api_key or os.getenv("ABLITERATED_API_KEY")
            llm_api_base = "http://10.210.22.164:31987/v1"
        elif provider == "local-glm-abliterated":
            # Self-hosted abliterated (refusal-removed) GLM-5.3-Flash endpoint,
            # OpenAI-compatible, intranet VPN only. Current default judge.
            llm_provider = "openai"
            llm_api_key = api_key or os.getenv("GLM_ABLITERATED_API_KEY")
            llm_api_base = "http://10.210.22.176:30460/v1"
        elif provider == "bedrock":
            llm_api_key = api_key or os.getenv("AWS_BEARER_TOKEN_BEDROCK")
        elif provider == "vertex_ai":
            llm_api_key = api_key or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Avoid double-prefix in the identifier too (see __init__).
        if model_name.startswith(f"{provider}/"):
            identifier = model_name
        else:
            identifier = f"{provider}/{model_name}"
        return cls(
            model_identifier=identifier,
            model_name=model_name,
            provider=llm_provider,
            real_provider=provider,
            api_key=llm_api_key,
            api_base=llm_api_base,
            **init_kwargs
        )

    def __init__(
        self,
        model_identifier: str,
        model_name: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        provider: Optional[str] = None,
        real_provider: Optional[str] = None,
        temperature: float = 1,
        max_tokens: Optional[int] = None,
        max_retries: int = 5,
        log_dir: Optional[str] = "logs",
        supports_vision: Optional[bool] = None,
        max_image_bytes: int = 20 * 1024 * 1024,
        request_timeout: Optional[float] = None,
        **kwargs
    ):
        """
        Initialize the LiteLLM-based LLM.
        
        Args:
            model_name: Name of the model to use
            api_key: API key for the provider
            api_base: Base URL for the API
            provider: Provider of the model
            temperature: Temperature parameter for generation
            max_tokens: Maximum number of tokens to generate
            max_retries: Maximum number of retries on API failures (default: 5)
            log_dir: Directory to store logs
            supports_vision: Explicit vision capability override. When omitted,
                LiteLLM model metadata is used.
            max_image_bytes: Maximum local image size accepted for transport.
            request_timeout: Per-request timeout in seconds. Defaults to
                JBF_REQUEST_TIMEOUT (180s).
            **kwargs: Additional parameters to pass to LiteLLM
        """
        super().__init__(model_name, **kwargs)
        self.model_identifier = model_identifier
        self.model_name = model_name
        self.real_provider = real_provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.log_dir = log_dir
        self.max_image_bytes = max_image_bytes
        self.request_timeout = request_timeout or float(os.environ.get("JBF_REQUEST_TIMEOUT", "180"))
        if self.max_image_bytes <= 0:
            raise ValueError("max_image_bytes must be greater than zero")

        if provider:
            # Avoid double-prefixing: configs often already include the router
            # prefix (e.g. "infi/deepseek-v4-pro"), and prepending provider
            # again ("iiis/infi/deepseek-v4-pro") makes the IIIS router reject
            # the request with "no healthy deployments".
            if model_name.startswith(f"{provider}/"):
                self.model_name = model_name
            else:
                self.model_name = f"{provider}/{model_name}"
        else:
            raise ValueError(f"Provider not provided.")

        if supports_vision is None:
            try:
                vision_enabled = bool(litellm.supports_vision(model=self.model_name))
                capability_source = "litellm"
            except Exception as exc:
                logger.debug("Could not detect vision support for %s: %s", self.model_name, exc)
                vision_enabled = False
                capability_source = "default"
        else:
            vision_enabled = supports_vision
            capability_source = "configuration"

        input_modalities = {"text"}
        if vision_enabled:
            input_modalities.add("image")
        self._capabilities = ModelCapabilities(
            input_modalities=frozenset(input_modalities),
            output_modalities=frozenset({"text"}),
            source=capability_source,
        )
        
        # Set up API key and base url if provided
        self.api_key = api_key
        self.api_base = api_base
        
        # Set up logging
        if log_dir:
            os.makedirs(f'{log_dir}/{provider}', exist_ok=True)
        
        # Store additional parameters
        self.kwargs = kwargs

        # Initialize query counter
        self.query_count = 0

    def _log_query_progress(
        self,
        event: str,
        query_id: str,
        messages: List[Dict[str, Any]],
        elapsed: Optional[float] = None,
        usage: Optional[Dict[str, int]] = None,
        error: Optional[Exception] = None,
    ) -> None:
        """Log compact live-call progress without prompt text or credentials."""
        prompt_chars = 0
        image_count = 0
        for message in messages:
            content = message.get("content", "")
            if isinstance(content, str):
                prompt_chars += len(content)
            elif isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    if part.get("type") in {"text", "input_text"}:
                        prompt_chars += len(str(part.get("text", "")))
                    elif part.get("type") in {"image", "image_url", "input_image"}:
                        image_count += 1
        parts = [
            f"LLM {event}",
            f"model={self.model_identifier}",
            f"messages={len(messages)}",
            f"prompt_chars={prompt_chars}",
        ]
        if image_count:
            parts.append(f"images={image_count}")
        if elapsed is not None:
            parts.append(f"elapsed={elapsed:.1f}s")
        if usage:
            parts.append(f"tokens={usage.get('total_tokens', 0)}")
        if error:
            parts.append(f"error={type(error).__name__}: {str(error)[:160]}")
        logger.info(" | ".join(parts))

    def _redact_completion_kwargs(self, completion_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        redacted = self._sanitize_for_log(completion_kwargs)
        if redacted.get("api_key"):
            redacted["api_key"] = "***REDACTED***"
        return redacted

    def _sanitize_for_log(self, value: Any) -> Any:
        """Recursively remove image bytes and remote image URLs from log payloads."""
        if isinstance(value, str):
            if value.startswith("data:image/"):
                mime_type = value.split(";", 1)[0].replace("data:", "")
                return f"[{mime_type} data omitted]"
            return value
        if isinstance(value, list):
            return [self._sanitize_for_log(item) for item in value]
        if isinstance(value, tuple):
            return [self._sanitize_for_log(item) for item in value]
        if isinstance(value, dict):
            if value.get("type") in {"image", "image_url", "input_image"}:
                sanitized = {
                    key: self._sanitize_for_log(item)
                    for key, item in value.items()
                    if key not in {"image_url", "url", "data", "image"}
                }
                sanitized["image"] = "[image reference omitted]"
                return sanitized
            return {key: self._sanitize_for_log(item) for key, item in value.items()}
        if isinstance(value, bytes):
            return f"[{len(value)} image bytes omitted]"
        return value
    
    def _make_messages(self, prompt: str) -> List[Dict[str, Any]]:
        """
        Format a prompt as a list of messages for chat-based models.
        
        Args:
            prompt: Raw prompt text
            
        Returns:
            List of message dictionaries
        """
        # Check if prompt already contains role prefixes
        if "SYSTEM:" in prompt or "USER:" in prompt or "ASSISTANT:" in prompt:
            # Parse from role prefixes
            messages = []
            lines = prompt.split("\n")
            current_role = None
            current_content = []
            
            for line in lines:
                if line.startswith("SYSTEM:"):
                    if current_role:
                        messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
                    current_role = "system"
                    current_content = [line[7:].strip()]
                elif line.startswith("USER:"):
                    if current_role:
                        messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
                    current_role = "user"
                    current_content = [line[5:].strip()]
                elif line.startswith("ASSISTANT:"):
                    if current_role:
                        messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
                    current_role = "assistant"
                    current_content = [line[10:].strip()]
                elif current_role:
                    current_content.append(line)
            
            if current_role:
                messages.append({"role": current_role, "content": "\n".join(current_content).strip()})
            
            # If no system message, add a default one
            if not any(m["role"] == "system" for m in messages):
                messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
            
            return messages
        
        # Simple format: user message only
        return [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]

    def _payload_to_messages(self, payload: AttackPayload) -> List[Dict[str, Any]]:
        """Convert a canonical payload to LiteLLM content blocks."""
        self._require_input_modalities(payload.modalities)
        messages: List[Dict[str, Any]] = []

        for message in payload.messages:
            content = []
            for part in message.parts:
                if isinstance(part, TextPart):
                    content.append({"type": "text", "text": part.text})
                    continue

                if not isinstance(part, ImagePart):
                    raise TypeError(f"Unsupported payload part: {type(part).__name__}")

                asset = part.image
                image_url = (
                    asset.source
                    if asset.is_remote
                    else asset.to_data_url(max_bytes=self.max_image_bytes)
                )
                image_block: Dict[str, Any] = {"url": image_url}
                if asset.detail:
                    image_block["detail"] = asset.detail
                content.append({"type": "image_url", "image_url": image_block})

            messages.append({"role": message.role, "content": content})

        return messages

    def _require_input_modalities(self, modalities) -> None:
        unsupported = set(modalities) - set(self._capabilities.input_modalities)
        if unsupported:
            raise ValueError(
                f"Model '{self.model_identifier}' does not support required input modalities: "
                + ", ".join(sorted(unsupported))
                + ". Select a vision-capable model or set supports_vision explicitly "
                "for a compatible custom endpoint."
            )

    def get_capabilities(self) -> ModelCapabilities:
        return self._capabilities

    def _normalize_prompts(
        self,
        prompts: Union[
            str,
            AttackPayload,
            List[str],
            List[AttackPayload],
            List[Dict[str, Any]],
        ],
    ) -> Tuple[bool, List[Any], bool]:
        """
        Normalize user input into (single_input, prompts_list, is_preformatted_messages).

        "Preformatted messages" means a list of dicts with {"role", "content"} keys.
        """
        if isinstance(prompts, (str, AttackPayload)):
            return True, [prompts], False
        
        if isinstance(prompts, list) and prompts:
            # Check if all items are dicts with "role" and "content" keys
            if all(isinstance(m, dict) and "role" in m and "content" in m for m in prompts):
                return True, [prompts], True

            if all(isinstance(prompt, AttackPayload) for prompt in prompts):
                return False, prompts, False

        return False, prompts, False

    def _apply_defense_to_prompts(
        self,
        prompts_list: List[Any],
        defense: str,
        behavior: Optional[str],
        phase: Optional[str],
        cost_tracker: Optional[CostTracker],
    ) -> Tuple[List[Any], Any]:
        """Apply a defense to prompts and return (new_prompts_list, defense_obj)."""
        defense_config = DefenseFactory.get_default_config(defense)
        defense_obj = DefenseFactory.create_defense(
            defense,
            defense_config=defense_config,
            llm=self,
            cost_tracker=cost_tracker,
        )
        for prompt in prompts_list:
            defense_obj.validate_modalities(infer_prompt_modalities(prompt))
        defended_prompts = [
            defense_obj.apply(p, behavior=behavior, defense=defense, phase=phase) for p in prompts_list
        ]
        return defended_prompts, defense_obj

    def _next_query_id(self) -> str:
        self.query_count += 1
        safe_name = self.model_name.replace("/", "_")
        return f"{safe_name}_{self.query_count}_{int(time.time())}"

    def _log_json(self, path: str, payload: Dict[str, Any]) -> None:
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

    def _build_completion_kwargs(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        completion_kwargs: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "api_key": self.api_key or "sk-dummy-key-for-local-endpoint",
            "api_base": self.api_base,
            # Per-request timeout so a hung/stalled upstream connection raises and is
            # picked up by the retry/backoff loop instead of blocking forever. Kept
            # generous enough to not clip legitimately slow reasoning completions.
            "timeout": kwargs.get("timeout", self.request_timeout),
        }

        # Add optional parameters only if provided.
        # Skip max_tokens for infini provider as it causes empty responses with reasoning models.
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        if max_tokens and self.real_provider != "infini":
            completion_kwargs["max_tokens"] = max_tokens

        # Add any additional kwargs passed during initialization.
        for key, value in self.kwargs.items():
            if key not in completion_kwargs:
                completion_kwargs[key] = value

        # Aliyun (DashScope) requires enable_thinking to be false on non-streaming calls.
        if self.real_provider == "aliyun" and not completion_kwargs.get("stream", False):
            extra_body = (completion_kwargs.get("extra_body") or {}).copy()
            extra_body["enable_thinking"] = False
            completion_kwargs["extra_body"] = extra_body

        return completion_kwargs

    def _completion_with_retries(self, completion_kwargs: Dict[str, Any]) -> Any:
        """Call LiteLLM completion with retry/backoff. Returns the raw LiteLLM response."""
        last_error: Optional[Exception] = None
        none_content_error_occurred = False

        for attempt in range(self.max_retries):
            try:
                response = completion(**completion_kwargs)
                response_text = response.choices[0].message.content
                if response_text is None:
                    none_content_error_occurred = True
                    raise ValueError(
                        "Model returned None content - likely refused to respond or encountered an error"
                    )
                return response
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # If None content error occurred, remove token limits for next retry.
                    if none_content_error_occurred or "None content" in str(e):
                        if "max_tokens" in completion_kwargs or "max_completion_tokens" in completion_kwargs:
                            logger.warning(
                                "Removing token limits for retry attempt %s/%s due to None content response",
                                attempt + 2,
                                self.max_retries,
                            )
                            completion_kwargs.pop("max_tokens", None)
                            completion_kwargs.pop("max_completion_tokens", None)
                            none_content_error_occurred = False

                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(
                        "API call failed (attempt %s/%s): %s. Retrying in %ss...",
                        attempt + 1,
                        self.max_retries,
                        str(e),
                        wait_time,
                    )
                    time.sleep(wait_time)
                    continue

                raise last_error

        raise RuntimeError("Failed to get response after all retries")

    def _resolve_cost_tracker(self, explicit_cost_tracker: Optional[CostTracker]) -> Optional[CostTracker]:
        """Resolve the cost tracker from explicit param or attack context (if present)."""
        if explicit_cost_tracker:
            return explicit_cost_tracker
        try:
            from ..attacks.context import ctx_get
            return ctx_get("cost_tracker", None)
        except (ImportError, RuntimeError):
            return None
    
    def query(
        self,
        prompts: Union[
            str,
            AttackPayload,
            List[str],
            List[AttackPayload],
            List[Dict[str, Any]],
        ],
        behavior: Optional[str] = None,
        defense: Optional[str] = None,
        phase: Optional[str] = None,
        cost_tracker: Optional[CostTracker] = None,
        **kwargs
    ) -> Union[str, List[str]]:
        """
        Query the model with a prompt or list of prompts.

        Args:
            prompts: Prompt(s) to send to the model. Can be:
                - A string prompt
                - A list of string prompts
                - A pre-formatted messages list [{"role": "...", "content": "..."}]
            behavior: Behavior context for logging and evaluation
            defense: Defense to apply (if any)
            phase: Phase of querying (e.g., "test", "optimization")
            cost_tracker: Optional CostTracker instance for usage tracking
            **kwargs: Additional query parameters

        Returns:
            Model response(s)
        """
        single_input, prompts_list, is_preformatted_messages = self._normalize_prompts(prompts)
        
        defense_obj = None
        # Apply defense if specified
        if defense:
            prompts_list, defense_obj = self._apply_defense_to_prompts(
                prompts_list=prompts_list,
                defense=defense,
                behavior=behavior,
                phase=phase,
                cost_tracker=cost_tracker,
            )
        
        responses = []
        for prompt in prompts_list:
            completion_kwargs = None
            query_id = None
            messages = None
            query_started_at = None
            try:
                # Format prompt as messages
                # If it's already a pre-formatted messages list, use it directly
                if isinstance(prompt, AttackPayload):
                    messages = self._payload_to_messages(prompt)
                elif is_preformatted_messages:
                    messages = prompt  # prompt is already a messages list
                else:
                    messages = self._make_messages(prompt)

                self._require_input_modalities(infer_prompt_modalities(messages))
                
                query_id = self._next_query_id()
                
                # Log the query
                if self.log_dir:
                    log_path = os.path.join(self.log_dir, f"{query_id}_query.json")
                    self._log_json(
                        log_path,
                        {
                            "model": self.model_name,
                            "messages": self._sanitize_for_log(messages),
                            "behavior": behavior,
                            "defense": defense,
                            "phase": phase,
                        },
                    )

                # Make the API call
                query_started_at = time.monotonic()
                self._log_query_progress("start", query_id, messages)
                completion_kwargs = self._build_completion_kwargs(messages, **kwargs)
                logger.debug(
                    "LiteLLM request (API key and image data redacted):\n%s",
                    json.dumps(
                        self._redact_completion_kwargs(completion_kwargs),
                        indent=2,
                        default=str,
                    ),
                )
                response = self._completion_with_retries(completion_kwargs)
                elapsed = time.monotonic() - query_started_at
                response_text = response.choices[0].message.content
                reasoning_content = getattr(response.choices[0].message, "reasoning_content", "")
                temporary_response = {"content": response_text}
                if reasoning_content:
                    temporary_response["reasoning_content"] = reasoning_content
                logger.debug(
                    "LiteLLM response:\n%s",
                    json.dumps(temporary_response, indent=2, default=str),
                )

                reasoning_tokens = (
                    getattr(getattr(response.usage, "completion_tokens_details", None), "reasoning_tokens", None)
                    or (self.get_token_count(reasoning_content) if reasoning_content else 0)
                )
                
                # Apply defense processing if applicable
                if defense:
                    response_text = defense_obj.process_response(
                        response_text,
                        behavior=behavior,
                        defense=defense,
                        phase=phase
                    )
                
                # Log the response
                if self.log_dir:
                    log_path = os.path.join(self.log_dir, f"{query_id}_response.json")
                    self._log_json(
                        log_path,
                        {
                            "model": self.model_name,
                            "response": response_text,
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens,
                        },
                    )

                # Create usage dictionary
                usage_dict = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                    "reasoning_tokens": reasoning_tokens
                }
                self._log_query_progress("done", query_id, messages, elapsed=elapsed, usage=usage_dict)

                active_cost_tracker = self._resolve_cost_tracker(cost_tracker)

                if active_cost_tracker:
                    active_cost_tracker.add_usage(self.model_identifier, usage_dict)

                responses.append(RichResponse(response_text, usage_dict, reasoning_content))

            except Exception as e:
                if completion_kwargs is not None:
                    logger.error(
                        "Error querying model: %s, completion_kwargs: %s",
                        str(e),
                        json.dumps(self._redact_completion_kwargs(completion_kwargs), indent=2),
                    )
                else:
                    logger.error("Error querying model: %s", str(e))
                # Re-raise the exception instead of creating an error response
                # This allows the caller to handle the failure appropriately
                raise
        
        # Return results
        if single_input:
            return responses[0]
        # Return as RichResponseList which behaves like a list but has usage methods
        return RichResponseList(responses)
    
    def get_token_count(self, text: str) -> int:
        """
        Count the number of tokens in the text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        try:
            return litellm.utils.token_counter(model=self.model_name, text=text)
        except Exception as e:
            logger.warning(f"Error counting tokens: {str(e)}")
            # Fallback to approximate token count
            return int(len(text.split()) * 1.33)  # Rough approximation
