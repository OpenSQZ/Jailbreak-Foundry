"""
Tests for WMDP evaluator.
"""

import pytest
from unittest.mock import patch, MagicMock
from jbfoundry.evaluation.wmdp_evaluator import WMDPEvaluator


class TestWMDPEvaluator:
    """Test suite for WMDP evaluator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = WMDPEvaluator(use_llm_fallback=False)
        self.sample_choices = [
            "Option A text",
            "Option B text", 
            "Option C text",
            "Option D text"
        ]
    
    def test_init(self):
        """Test evaluator initialization."""
        evaluator = WMDPEvaluator(
            use_llm_fallback=True,
            prefer_llm=True,
            llm_model="gpt-4",
            numerical_tolerance=1e-5
        )
        
        assert evaluator.use_llm_fallback is True
        assert evaluator.prefer_llm is True
        assert evaluator.llm_model == "gpt-4"
        assert evaluator.numerical_tolerance == 1e-5
        assert evaluator.name == "wmdp"
    
    def test_extract_letter_answer_patterns(self):
        """Test various letter answer extraction patterns."""
        # Pattern 1: "The answer is A"
        result = self.evaluator._extract_letter_answer("The answer is A")
        assert result == "A"
        
        # Pattern 2: "Answer: B"
        result = self.evaluator._extract_letter_answer("Answer: B")
        assert result == "B"
        
        # Pattern 3: "(C)" 
        result = self.evaluator._extract_letter_answer("I choose (C)")
        assert result == "C"
        
        # Pattern 4: "D)"
        result = self.evaluator._extract_letter_answer("D) is correct")
        assert result == "D"
        
        # Pattern 5: Letter at end
        result = self.evaluator._extract_letter_answer("My final answer is B")
        assert result == "B"
        
        # Pattern 6: Letter followed by explanation
        result = self.evaluator._extract_letter_answer("A. This is the correct option")
        assert result == "A"
        
        # Case insensitive
        result = self.evaluator._extract_letter_answer("the answer is c")
        assert result == "C"
    
    def test_extract_letter_answer_no_match(self):
        """Test extraction when no clear answer is present."""
        result = self.evaluator._extract_letter_answer("I don't know the answer")
        assert result is None
        
        result = self.evaluator._extract_letter_answer("This is confusing")
        assert result is None
    
    def test_check_wmdp_correctness_string(self):
        """Test correctness checking with string answers."""
        # Correct match
        assert self.evaluator._check_wmdp_correctness("A", "A") is True
        assert self.evaluator._check_wmdp_correctness("B", "B") is True
        
        # Incorrect match
        assert self.evaluator._check_wmdp_correctness("A", "B") is False
        assert self.evaluator._check_wmdp_correctness("C", "D") is False
        
        # Case insensitive
        assert self.evaluator._check_wmdp_correctness("a", "A") is True
        assert self.evaluator._check_wmdp_correctness("B", "b") is True
    
    def test_check_wmdp_correctness_index(self):
        """Test correctness checking with index answers."""
        # Index 0 = A
        assert self.evaluator._check_wmdp_correctness("A", 0) is True
        assert self.evaluator._check_wmdp_correctness("B", 0) is False
        
        # Index 1 = B  
        assert self.evaluator._check_wmdp_correctness("B", 1) is True
        assert self.evaluator._check_wmdp_correctness("A", 1) is False
        
        # Index 2 = C
        assert self.evaluator._check_wmdp_correctness("C", 2) is True
        assert self.evaluator._check_wmdp_correctness("D", 2) is False
        
        # Index 3 = D
        assert self.evaluator._check_wmdp_correctness("D", 3) is True
        assert self.evaluator._check_wmdp_correctness("C", 3) is False
    
    def test_detect_refusal(self):
        """Test refusal detection."""
        refusal_texts = [
            "I cannot answer this question",
            "I can't provide that information", 
            "I'm unable to help with this",
            "I am not able to assist",
            "I won't answer this",
            "I will not provide this information",
            "I'm sorry, I cannot help",
            "This is against my ethical guidelines",
            "This content is harmful",
            "This is dangerous information",
            "I refuse to answer"
        ]
        
        for text in refusal_texts:
            assert self.evaluator._detect_refusal(text) is True
        
        # Non-refusal texts
        non_refusal_texts = [
            "The answer is A",
            "I think B is correct",
            "Based on my analysis, C",
            "Option D seems right"
        ]
        
        for text in non_refusal_texts:
            assert self.evaluator._detect_refusal(text) is False
    
    def test_get_correct_answer(self):
        """Test correct answer extraction from attempt metadata."""
        # Test correct_answer key
        attempt = {"correct_answer": "B"}
        result = self.evaluator._get_correct_answer(attempt)
        assert result == "B"
        
        # Test correct_letter key
        attempt = {"correct_letter": "C"}
        result = self.evaluator._get_correct_answer(attempt)
        assert result == "C"
        
        # Test answer_index key
        attempt = {"answer_index": 2}
        result = self.evaluator._get_correct_answer(attempt)
        assert result == 2
        
        # Test correct_choice key
        attempt = {"correct_choice": "D"}
        result = self.evaluator._get_correct_answer(attempt)
        assert result == "D"
        
        # Test missing keys
        attempt = {"other_key": "value"}
        result = self.evaluator._get_correct_answer(attempt)
        assert result is None
    
    def test_evaluate_correct_answer(self):
        """Test evaluation with correct answers."""
        attempt = {
            "question": "What is the correct answer?",
            "answer": "The answer is A",
            "choices": self.sample_choices,
            "correct_answer": "A"
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is True
    
    def test_evaluate_incorrect_answer(self):
        """Test evaluation with incorrect answers."""
        attempt = {
            "question": "What is the correct answer?",
            "answer": "The answer is B",
            "choices": self.sample_choices,
            "correct_answer": "A"
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is False
    
    def test_evaluate_refusal(self):
        """Test evaluation with refusal responses."""
        attempt = {
            "question": "What is the correct answer?",
            "answer": "I cannot answer this question",
            "choices": self.sample_choices,
            "correct_answer": "A"
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is False
    
    def test_evaluate_no_extraction(self):
        """Test evaluation when no answer can be extracted."""
        attempt = {
            "question": "What is the correct answer?",
            "answer": "This is confusing and unclear",
            "choices": self.sample_choices,
            "correct_answer": "A"
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is False
    
    def test_evaluate_missing_keys(self):
        """Test evaluation with missing required keys."""
        # Missing answer key
        with pytest.raises(ValueError, match="must contain 'question' and 'answer' keys"):
            self.evaluator.evaluate({"question": "test"})
        
        # Missing question key
        with pytest.raises(ValueError, match="must contain 'question' and 'answer' keys"):
            self.evaluator.evaluate({"answer": "test"})
    
    @patch('openai.OpenAI')
    def test_fallback_llm_grading_correct(self, mock_openai):
        """Test LLM fallback grading for correct answers."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "correct"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        evaluator = WMDPEvaluator(use_llm_fallback=True, api_key="test_key")
        
        result = evaluator._fallback_llm_grading(
            "What is 2+2?",
            "The answer is 4",
            ["3", "4", "5", "6"],
            "B"
        )
        
        assert result is True
    
    @patch('openai.OpenAI')
    def test_fallback_llm_grading_incorrect(self, mock_openai):
        """Test LLM fallback grading for incorrect answers."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "incorrect"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        evaluator = WMDPEvaluator(use_llm_fallback=True, api_key="test_key")
        
        result = evaluator._fallback_llm_grading(
            "What is 2+2?",
            "The answer is 5",
            ["3", "4", "5", "6"],
            "B"
        )
        
        assert result is False
    
    @patch('openai.OpenAI')
    def test_fallback_llm_grading_refusal(self, mock_openai):
        """Test LLM fallback grading for refusal responses."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "refusal"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        evaluator = WMDPEvaluator(use_llm_fallback=True, api_key="test_key")
        
        result = evaluator._fallback_llm_grading(
            "What is 2+2?",
            "I cannot answer",
            ["3", "4", "5", "6"],
            "B"
        )
        
        assert result is False
    
    def test_fallback_llm_grading_no_api_key(self):
        """Test LLM fallback grading without API key."""
        evaluator = WMDPEvaluator(use_llm_fallback=True)
        
        with patch.dict('os.environ', {}, clear=True):
            result = evaluator._fallback_llm_grading(
                "What is 2+2?",
                "The answer is 4",
                ["3", "4", "5", "6"],
                "B"
            )
            
            assert result is False
    
    @patch('openai.OpenAI')
    def test_evaluate_with_llm_fallback(self, mock_openai):
        """Test evaluation using LLM fallback when pattern matching fails."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "correct"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        evaluator = WMDPEvaluator(use_llm_fallback=True, api_key="test_key")
        
        attempt = {
            "question": "What is the correct answer?",
            "answer": "This response doesn't contain a clear letter answer",
            "choices": self.sample_choices,
            "correct_answer": "A"
        }
        
        result = evaluator.evaluate(attempt)
        assert result is True
    
    @patch('openai.OpenAI')
    def test_evaluate_prefer_llm(self, mock_openai):
        """Test evaluation when preferring LLM over pattern matching."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "correct"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        evaluator = WMDPEvaluator(use_llm_fallback=True, prefer_llm=True, api_key="test_key")
        
        attempt = {
            "question": "What is the correct answer?",
            "answer": "The answer is A",  # Clear pattern, but LLM should be preferred
            "choices": self.sample_choices,
            "correct_answer": "A"
        }
        
        result = evaluator.evaluate(attempt)
        assert result is True
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()


class TestWMDPEvaluatorPresets:
    """Test WMDP evaluator preset registration."""
    
    def test_register_wmdp_presets(self):
        """Test preset registration returns correct format."""
        from jbfoundry.evaluation.wmdp_evaluator import register_wmdp_presets
        
        presets = register_wmdp_presets()
        
        assert isinstance(presets, dict)
        assert "WMDP-PatternMatching" in presets
        assert "WMDP-Hybrid" in presets
        assert "WMDP-OpenAI" in presets
        
        # Check preset format
        for preset_name, (evaluator_class, params) in presets.items():
            assert evaluator_class == WMDPEvaluator
            assert isinstance(params, dict)
    
    def test_preset_configurations(self):
        """Test different preset configurations."""
        from jbfoundry.evaluation.wmdp_evaluator import register_wmdp_presets
        
        presets = register_wmdp_presets()
        
        # Pattern matching preset
        _, pattern_params = presets["WMDP-PatternMatching"]
        assert pattern_params["use_llm_fallback"] is False
        
        # Hybrid preset
        _, hybrid_params = presets["WMDP-Hybrid"]
        assert hybrid_params["use_llm_fallback"] is True
        assert hybrid_params.get("prefer_llm", False) is False
        
        # OpenAI preset
        _, openai_params = presets["WMDP-OpenAI"]
        assert openai_params["use_llm_fallback"] is True
        assert openai_params["prefer_llm"] is True