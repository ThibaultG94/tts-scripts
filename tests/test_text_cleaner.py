"""Tests for text cleaning utilities."""

import pytest
from lib.text_cleaner import TextCleaner


class TestTextCleaner:
    """Test text cleaning functions."""
    
    def test_extract_text_from_html(self):
        """Test HTML text extraction."""
        html = """
        <html>
            <body>
                <h1>Title</h1>
                <p>This is a <strong>test</strong> paragraph.</p>
                <script>alert('test');</script>
            </body>
        </html>
        """
        
        result = TextCleaner.extract_text_from_html(html)
        
        assert "Title" in result
        assert "test paragraph" in result
        assert "alert" not in result  # Script content should be removed
        
    def test_clean_text_for_tts(self):
        """Test TTS text cleaning."""
        text = "Hello…   This is a 'test'  with special–characters!"
        
        result = TextCleaner.clean_text_for_tts(text)
        
        assert "..." in result  # Ellipsis converted
        assert '"test"' in result  # Smart quotes converted
        assert "--" not in result or "-" in result  # Dashes simplified
        assert "  " not in result  # Multiple spaces removed
        
    def test_fix_pronunciation(self):
        """Test pronunciation fixes."""
        text = "M. Dupont et Mme Martin, etc."
        
        result = TextCleaner.fix_pronunciation(text)
        
        assert "Monsieur" in result
        assert "Madame" in result
        assert "et cetera" in result
        
    def test_split_into_sentences(self):
        """Test sentence splitting."""
        text = "First sentence. Second one! And a third? Last one."
        
        result = TextCleaner.split_into_sentences(text)
        
        assert len(result) == 4
        assert result[0] == "First sentence."
        assert result[1] == "Second one!"
        
    def test_estimate_reading_time(self):
        """Test reading time estimation."""
        # 150 words at 150 wpm = 1 minute
        text = " ".join(["word"] * 150)
        
        result = TextCleaner.estimate_reading_time(text, 150)
        
        assert result == 1.0
        
    def test_empty_input_handling(self):
        """Test handling of empty inputs."""
        assert TextCleaner.extract_text_from_html("") == ""
        assert TextCleaner.extract_text_from_html(None) == ""
        assert TextCleaner.clean_text_for_tts("") == ""
        assert TextCleaner.clean_text_for_tts(None) == ""