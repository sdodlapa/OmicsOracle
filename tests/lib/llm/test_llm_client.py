"""
Tests for LLM client.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from omics_oracle_v2.lib.llm.client import LLMClient


class TestLLMClient:
    """Test LLM client."""

    def test_initialization_default(self):
        """Test default initialization."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient()
            assert client.provider == "openai"
            assert client.model is not None
            assert client.cache_enabled is True
            assert client.temperature == 0.1

    def test_initialization_custom(self):
        """Test custom initialization."""
        client = LLMClient(
            provider="anthropic",
            model="claude-3-opus-20240229",
            cache_enabled=False,
            temperature=0.5,
        )
        assert client.provider == "anthropic"
        assert client.model == "claude-3-opus-20240229"
        assert client.cache_enabled is False
        assert client.temperature == 0.5

    def test_cache_key_generation(self):
        """Test cache key generation."""
        client = LLMClient(provider="openai")

        key1 = client._get_cache_key("prompt1", "system1", "gpt-4-turbo-preview")
        key2 = client._get_cache_key("prompt1", "system1", "gpt-4-turbo-preview")
        key3 = client._get_cache_key("prompt2", "system1", "gpt-4-turbo-preview")

        # Same inputs should produce same key
        assert key1 == key2

        # Different inputs should produce different keys
        assert key1 != key3

    def test_cache_save_load(self):
        """Test cache save and load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = LLMClient(provider="openai", cache_enabled=True)
            client.cache_dir = tmpdir

            # Save to cache
            response = {"content": "Test response", "usage": {"total_tokens": 100}}
            cache_key = "test_key"
            client._save_to_cache(cache_key, response)

            # Load from cache
            loaded = client._load_from_cache(cache_key)
            assert loaded == response

    def test_cache_disabled(self):
        """Test that cache is not used when disabled."""
        client = LLMClient(provider="openai", cache_enabled=False)

        # Should not save or load from cache
        response = {"content": "Test"}
        cache_key = "test_key"

        result = client._load_from_cache(cache_key)
        assert result is None

    @patch("omics_oracle_v2.lib.llm.client.openai")
    def test_openai_generate_success(self, mock_openai):
        """Test OpenAI generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="AI response"))]
        mock_response.usage = Mock(total_tokens=50, prompt_tokens=30, completion_tokens=20)
        mock_openai.OpenAI.return_value.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            client = LLMClient(provider="openai", cache_enabled=False)
            result = client.generate("Test prompt")

            assert result["content"] == "AI response"
            assert result["usage"]["total_tokens"] == 50

    @patch("omics_oracle_v2.lib.llm.client.anthropic")
    def test_anthropic_generate_success(self, mock_anthropic):
        """Test Anthropic generation."""
        # Mock Anthropic response
        mock_response = Mock()
        mock_response.content = [Mock(text="Claude response")]
        mock_response.usage = Mock(input_tokens=30, output_tokens=20)
        mock_anthropic.Anthropic.return_value.messages.create.return_value = mock_response

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            client = LLMClient(provider="anthropic", cache_enabled=False)
            result = client.generate("Test prompt")

            assert result["content"] == "Claude response"
            assert result["usage"]["total_tokens"] == 50

    @patch("omics_oracle_v2.lib.llm.client.requests")
    def test_ollama_generate_success(self, mock_requests):
        """Test Ollama generation."""
        # Mock Ollama response
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Ollama response"}
        mock_response.raise_for_status = Mock()
        mock_requests.post.return_value = mock_response

        client = LLMClient(provider="ollama", model="llama2", cache_enabled=False)
        result = client.generate("Test prompt")

        assert result["content"] == "Ollama response"

    def test_generate_json_success(self):
        """Test JSON generation."""
        client = LLMClient(provider="openai", cache_enabled=False)

        # Mock the generate method
        client.generate = Mock(
            return_value={
                "content": '{"key": "value", "number": 42}',
                "usage": {"total_tokens": 100},
            }
        )

        result = client.generate_json("Test prompt")

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_generate_json_invalid(self):
        """Test JSON generation with invalid JSON."""
        client = LLMClient(provider="openai", cache_enabled=False)

        # Mock the generate method to return invalid JSON
        client.generate = Mock(return_value={"content": "Not valid JSON", "usage": {"total_tokens": 100}})

        with pytest.raises(ValueError, match="Failed to parse LLM response as JSON"):
            client.generate_json("Test prompt")

    def test_usage_stats_tracking(self):
        """Test usage statistics tracking."""
        client = LLMClient(provider="openai", cache_enabled=False)

        # Mock generate to track usage
        def mock_generate(*args, **kwargs):
            return {
                "content": "Response",
                "usage": {"total_tokens": 100, "prompt_tokens": 60, "completion_tokens": 40},
            }

        client.generate = mock_generate

        # Make some calls
        client.generate("Prompt 1")
        client.generate("Prompt 2")
        client.generate("Prompt 3")

        stats = client.get_usage_stats()

        assert stats["total_calls"] == 3
        assert stats["total_tokens"] == 300
        assert stats["total_prompt_tokens"] == 180
        assert stats["total_completion_tokens"] == 120

    def test_cache_hit(self):
        """Test cache hit scenario."""
        with tempfile.TemporaryDirectory() as tmpdir:
            client = LLMClient(provider="openai", cache_enabled=True)
            client.cache_dir = tmpdir

            # Mock the underlying generation
            with patch.object(client, "_openai_generate") as mock_gen:
                mock_gen.return_value = {
                    "content": "Response",
                    "usage": {"total_tokens": 100},
                }

                # First call - should hit the API
                result1 = client.generate("Test prompt", "System prompt")
                assert mock_gen.call_count == 1

                # Second call with same inputs - should use cache
                result2 = client.generate("Test prompt", "System prompt")
                assert mock_gen.call_count == 1  # Still 1, not called again

                assert result1 == result2

    def test_retry_logic(self):
        """Test retry logic on failure."""
        client = LLMClient(provider="openai", cache_enabled=False)

        # Mock to fail twice then succeed
        call_count = 0

        def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("API error")
            return {"content": "Success", "usage": {"total_tokens": 50}}

        with patch.object(client, "_openai_generate", side_effect=mock_generate):
            # Should fail after max retries
            with pytest.raises(Exception):
                client.generate("Test prompt", max_retries=2)

    def test_max_tokens_parameter(self):
        """Test max_tokens parameter."""
        with patch("omics_oracle_v2.lib.llm.client.openai") as mock_openai:
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_response.usage = Mock(total_tokens=50, prompt_tokens=30, completion_tokens=20)
            mock_openai.OpenAI.return_value.chat.completions.create.return_value = mock_response

            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
                client = LLMClient(provider="openai", cache_enabled=False)
                client.generate("Test", max_tokens=500)

                # Verify max_tokens was passed
                call_args = mock_openai.OpenAI.return_value.chat.completions.create.call_args
                assert call_args[1]["max_tokens"] == 500


class TestProviderSelection:
    """Test provider selection logic."""

    def test_invalid_provider(self):
        """Test invalid provider raises error."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            client = LLMClient(provider="invalid")
            client.generate("Test")

    def test_provider_model_defaults(self):
        """Test default models for each provider."""
        openai_client = LLMClient(provider="openai")
        assert "gpt" in openai_client.model.lower()

        anthropic_client = LLMClient(provider="anthropic")
        assert "claude" in anthropic_client.model.lower()

        ollama_client = LLMClient(provider="ollama")
        assert "llama" in ollama_client.model.lower()


class TestConcurrency:
    """Test concurrent usage."""

    @pytest.mark.skip(reason="Requires concurrent testing setup")
    def test_concurrent_calls(self):
        """Test concurrent LLM calls."""
        import concurrent.futures

        client = LLMClient(provider="openai", cache_enabled=True)

        # Mock generation
        client.generate = Mock(return_value={"content": "Response", "usage": {"total_tokens": 50}})

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(client.generate, f"Prompt {i}") for i in range(10)]
            results = [f.result() for f in futures]

        assert len(results) == 10
