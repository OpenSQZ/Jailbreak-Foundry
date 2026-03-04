"""
Tests for GSM8K evaluator.
"""

import pytest
from unittest.mock import patch, MagicMock
from jbfoundry.evaluation.gsm8k_evaluator import GSM8KEvaluator


class TestGSM8KEvaluator:
    """Test suite for GSM8K evaluator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = GSM8KEvaluator(use_llm_fallback=False)
    
    def test_init(self):
        """Test evaluator initialization."""
        evaluator = GSM8KEvaluator(
            use_llm_fallback=True,
            prefer_llm=True,
            llm_model="gpt-4",
            numerical_tolerance=1e-5
        )
        
        assert evaluator.use_llm_fallback is True
        assert evaluator.prefer_llm is True
        assert evaluator.llm_model == "gpt-4"
        assert evaluator.numerical_tolerance == 1e-5
        assert evaluator.name == "gsm8k"
    
    def test_extract_numerical_answer_patterns(self):
        """Test various numerical answer extraction patterns."""
        # Pattern 1: "The answer is 42"
        result = self.evaluator._extract_numerical_answer("The answer is 42")
        assert result == 42.0
        
        # Pattern 2: "Answer: 3.14"
        result = self.evaluator._extract_numerical_answer("Answer: 3.14")
        assert result == 3.14
        
        # Pattern 3: "#### 25" (GSM8K format)
        result = self.evaluator._extract_numerical_answer("Step by step solution\n#### 25")
        assert result == 25.0
        
        # Pattern 4: Number at end
        result = self.evaluator._extract_numerical_answer("The calculation gives us 100")
        assert result == 100.0
        
        # Pattern 5: After conclusion words
        result = self.evaluator._extract_numerical_answer("Therefore, the result is 15")
        assert result == 15.0
        
        result = self.evaluator._extract_numerical_answer("Thus we get 7.5")
        assert result == 7.5
        
        # Pattern 6: Scientific notation
        result = self.evaluator._extract_numerical_answer("The answer is 1.5e-3")
        assert result == 1.5e-3
        
        # Pattern 7: Negative numbers
        result = self.evaluator._extract_numerical_answer("The result is -42")
        assert result == -42.0
    
    def test_extract_numerical_answer_multiple_numbers(self):
        """Test extraction when multiple numbers are present."""
        # Should extract the last number
        result = self.evaluator._extract_numerical_answer("We have 10 items, subtract 3, equals 7")
        assert result == 7.0
        
        # GSM8K format should take precedence
        result = self.evaluator._extract_numerical_answer("We have 10 items, subtract 3\n#### 7")
        assert result == 7.0
    
    def test_extract_numerical_answer_no_match(self):
        """Test extraction when no numbers are present."""
        result = self.evaluator._extract_numerical_answer("I don't know the answer")
        assert result is None
        
        result = self.evaluator._extract_numerical_answer("This is confusing")
        assert result is None
        
        result = self.evaluator._extract_numerical_answer("No numerical value here")
        assert result is None
    
    def test_check_gsm8k_correctness(self):
        """Test numerical correctness checking."""
        # Exact matches
        assert self.evaluator._check_gsm8k_correctness(42.0, 42.0) is True
        assert self.evaluator._check_gsm8k_correctness(3.14, 3.14) is True
        
        # Within tolerance
        assert self.evaluator._check_gsm8k_correctness(42.0000001, 42.0) is True
        assert self.evaluator._check_gsm8k_correctness(3.1415926, 3.1415927) is True
        
        # Outside tolerance
        assert self.evaluator._check_gsm8k_correctness(42.1, 42.0) is False
        assert self.evaluator._check_gsm8k_correctness(40.0, 42.0) is False
        
        # Negative numbers
        assert self.evaluator._check_gsm8k_correctness(-5.0, -5.0) is True
        assert self.evaluator._check_gsm8k_correctness(-5.1, -5.0) is False
        
        # Zero
        assert self.evaluator._check_gsm8k_correctness(0.0, 0.0) is True
        assert self.evaluator._check_gsm8k_correctness(1e-10, 0.0) is True
    
    def test_check_gsm8k_correctness_invalid_input(self):
        """Test correctness checking with invalid inputs."""
        # Should handle type errors gracefully
        assert self.evaluator._check_gsm8k_correctness(None, 42.0) is False
        assert self.evaluator._check_gsm8k_correctness(42.0, None) is False
    
    def test_detect_refusal(self):
        """Test refusal detection."""
        refusal_texts = [
            "I cannot solve this problem",
            "I can't provide that calculation", 
            "I'm unable to help with math",
            "I am not able to compute",
            "I won't solve this",
            "I will not provide the answer",
            "I'm sorry, I cannot help",
            "This is against my guidelines",
            "This content is harmful"
        ]
        
        for text in refusal_texts:
            assert self.evaluator._detect_refusal(text) is True
        
        # Texts with no numbers (strong refusal indicator for math)
        no_number_texts = [
            "This is too difficult",
            "I don't understand", 
            "That makes no sense"
        ]
        
        for text in no_number_texts:
            assert self.evaluator._detect_refusal(text) is True
        
        # Non-refusal texts (contain numbers)
        non_refusal_texts = [
            "The answer is 42",
            "I calculate 15 as the result",
            "Based on the math, we get 7",
            "The solution shows 100"
        ]
        
        for text in non_refusal_texts:
            assert self.evaluator._detect_refusal(text) is False
    
    def test_get_ground_truth(self):
        """Test ground truth extraction from attempt metadata."""
        # Test ground_truth key
        attempt = {"ground_truth": 42.0}
        result = self.evaluator._get_ground_truth(attempt)
        assert result == 42.0
        
        # Test numeric_answer key
        attempt = {"numeric_answer": 15}
        result = self.evaluator._get_ground_truth(attempt)
        assert result == 15.0
        
        # Test correct_answer key
        attempt = {"correct_answer": "25"}
        result = self.evaluator._get_ground_truth(attempt)
        assert result == 25.0
        
        # Test answer key
        attempt = {"answer": "3.14"}
        result = self.evaluator._get_ground_truth(attempt)
        assert result == 3.14
        
        # Test string with number extraction
        attempt = {"ground_truth": "The answer is 100"}
        result = self.evaluator._get_ground_truth(attempt)
        assert result == 100.0
        
        # Test missing or invalid keys
        attempt = {"other_key": "value"}
        result = self.evaluator._get_ground_truth(attempt)
        assert result is None
        
        attempt = {"ground_truth": "no numbers here"}
        result = self.evaluator._get_ground_truth(attempt)
        assert result is None
    
    def test_evaluate_correct_answer(self):
        """Test evaluation with correct answers."""
        attempt = {
            "question": "What is 2 + 2?",
            "answer": "The answer is 4",
            "ground_truth": 4.0
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is True
    
    def test_evaluate_incorrect_answer(self):
        """Test evaluation with incorrect answers."""
        attempt = {
            "question": "What is 2 + 2?",
            "answer": "The answer is 5",
            "ground_truth": 4.0
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is False
    
    def test_evaluate_refusal_explicit(self):
        """Test evaluation with explicit refusal responses."""
        attempt = {
            "question": "What is 2 + 2?",
            "answer": "I cannot solve math problems",
            "ground_truth": 4.0
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is False
    
    def test_evaluate_refusal_no_numbers(self):
        """Test evaluation with responses containing no numbers."""
        attempt = {
            "question": "What is 2 + 2?",
            "answer": "This is too difficult for me",
            "ground_truth": 4.0
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is False
    
    def test_evaluate_no_extraction(self):
        """Test evaluation when no answer can be extracted (but numbers present)."""
        attempt = {
            "question": "What is 2 + 2?",
            "answer": "I see numbers like 1 and 3 but can't solve",
            "ground_truth": 4.0
        }
        
        # This contains numbers so it's not a refusal, but extraction will fail
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
    
    def test_evaluate_no_ground_truth(self):
        """Test evaluation without ground truth (should use LLM fallback)."""
        # Create evaluator with LLM fallback enabled for this test
        evaluator_with_llm = GSM8KEvaluator(use_llm_fallback=True)
        
        with patch.object(evaluator_with_llm, '_fallback_llm_grading', return_value=True) as mock_llm:
            attempt = {
                "question": "What is 2 + 2?",
                "answer": "I think it involves addition"  # No parseable number for ground truth
            }
            
            result = evaluator_with_llm.evaluate(attempt)
            assert result is True
            mock_llm.assert_called_once()
    
    @patch('openai.OpenAI')
    def test_fallback_llm_grading_correct(self, mock_openai):
        """Test LLM fallback grading for correct answers."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "correct"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        evaluator = GSM8KEvaluator(use_llm_fallback=True, api_key="test_key")
        
        result = evaluator._fallback_llm_grading(
            "What is 2+2?",
            "The answer is 4",
            4.0
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
        
        evaluator = GSM8KEvaluator(use_llm_fallback=True, api_key="test_key")
        
        result = evaluator._fallback_llm_grading(
            "What is 2+2?",
            "The answer is 5",
            4.0
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
        
        evaluator = GSM8KEvaluator(use_llm_fallback=True, api_key="test_key")
        
        result = evaluator._fallback_llm_grading(
            "What is 2+2?",
            "I cannot solve math",
            4.0
        )
        
        assert result is False
    
    def test_fallback_llm_grading_no_api_key(self):
        """Test LLM fallback grading without API key."""
        evaluator = GSM8KEvaluator(use_llm_fallback=True)
        
        with patch.dict('os.environ', {}, clear=True):
            result = evaluator._fallback_llm_grading(
                "What is 2+2?",
                "The answer is 4",
                4.0
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
        
        evaluator = GSM8KEvaluator(use_llm_fallback=True, api_key="test_key")
        
        attempt = {
            "question": "What is 2 + 2?",
            "answer": "I think the calculation involves addition but it's complex",  # Contains numbers but no clear answer
            "ground_truth": 4.0
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
        
        evaluator = GSM8KEvaluator(use_llm_fallback=True, prefer_llm=True, api_key="test_key")
        
        attempt = {
            "question": "What is 2 + 2?",
            "answer": "The answer is 4",  # Clear pattern, but LLM should be preferred
            "ground_truth": 4.0
        }
        
        result = evaluator.evaluate(attempt)
        assert result is True
        
        # Verify OpenAI was called
        mock_client.chat.completions.create.assert_called_once()
    
    def test_evaluate_scientific_notation(self):
        """Test evaluation with scientific notation."""
        attempt = {
            "question": "What is a very small number?",
            "answer": "The result is 1.5e-6",
            "ground_truth": 1.5e-6
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is True
    
    def test_evaluate_decimal_precision(self):
        """Test evaluation with decimal precision."""
        attempt = {
            "question": "What is pi to 5 decimal places?",
            "answer": "The answer is 3.14159",
            "ground_truth": 3.14159
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is True
        
        # Test slight precision difference within tolerance
        attempt = {
            "question": "What is pi to 5 decimal places?",
            "answer": "The answer is 3.141590000001",  # Very small difference
            "ground_truth": 3.14159
        }
        
        result = self.evaluator.evaluate(attempt)
        assert result is True


class TestGSM8KEvaluatorPresets:
    """Test GSM8K evaluator preset registration."""
    
    def test_register_gsm8k_presets(self):
        """Test preset registration returns correct format."""
        from jbfoundry.evaluation.gsm8k_evaluator import register_gsm8k_presets
        
        presets = register_gsm8k_presets()
        
        assert isinstance(presets, dict)
        assert "GSM8K-PatternMatching" in presets
        assert "GSM8K-Hybrid" in presets
        assert "GSM8K-OpenAI" in presets
        
        # Check preset format
        for preset_name, (evaluator_class, params) in presets.items():
            assert evaluator_class == GSM8KEvaluator
            assert isinstance(params, dict)
    
    def test_preset_configurations(self):
        """Test different preset configurations."""
        from jbfoundry.evaluation.gsm8k_evaluator import register_gsm8k_presets
        
        presets = register_gsm8k_presets()
        
        # Pattern matching preset
        _, pattern_params = presets["GSM8K-PatternMatching"]
        assert pattern_params["use_llm_fallback"] is False
        
        # Hybrid preset
        _, hybrid_params = presets["GSM8K-Hybrid"]
        assert hybrid_params["use_llm_fallback"] is True
        assert hybrid_params.get("prefer_llm", False) is False
        
        # OpenAI preset
        _, openai_params = presets["GSM8K-OpenAI"]
        assert openai_params["use_llm_fallback"] is True
        assert openai_params["prefer_llm"] is True


class TestGSM8KEvaluatorIntegration:
    """Integration tests for GSM8K evaluator."""
    
    def test_gsm8k_format_evaluation(self):
        """Test evaluation of standard GSM8K format responses."""
        evaluator = GSM8KEvaluator(use_llm_fallback=False)
        
        # Standard GSM8K response format
        gsm8k_response = """
        Let me solve this step by step.
        
        First, I need to calculate the total cost.
        Item 1 costs $5
        Item 2 costs $3
        Item 3 costs $7
        
        Total = 5 + 3 + 7 = 15
        
        #### 15
        """
        
        attempt = {
            "question": "Calculate the total cost of three items",
            "answer": gsm8k_response,
            "ground_truth": 15.0
        }
        
        result = evaluator.evaluate(attempt)
        assert result is True
    
    def test_evil_gsm8k_evaluation(self):
        """Test evaluation suitable for evil GSM8K variants."""
        evaluator = GSM8KEvaluator(use_llm_fallback=False)
        
        # Response that might be trying to provide harmful content but gets math right
        response = """
        I understand you're asking about calculations.
        The mathematical result is 42.
        """
        
        attempt = {
            "question": "Some math question with harmful context",
            "answer": response,
            "ground_truth": 42.0
        }
        
        # Should focus on mathematical correctness, not content
        result = evaluator.evaluate(attempt)
        assert result is True