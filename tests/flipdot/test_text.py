import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from flipdot.DotMatrix import DotMatrix, NPDotArray
from flipdot.text import string_to_dots

# Helper function to create a DotMatrix from a list of lists
def mat(data: list[list[int]]) -> NPDotArray:
    return np.array(data, dtype=np.uint8)

# --- Mock Font Setup ---
# This is a simplified mock for testing `string_to_dots` without full font loading.
class MockChar:
    def __init__(self, char_str: str, matrix_data: list[list[int]]):
        self.char = char_str
        self.dot_matrix = DotMatrix(mat(matrix_data))
        self.width = self.dot_matrix.width

class MockFont:
    def __init__(self, name: str, line_height: int, char_space_width: int = 1):
        self.name = name
        self.line_height = line_height
        self.char_data = {} # char_str -> MockChar
        # Define a simple dot matrix for character spacing
        self.char_space = MockChar(" ", [[0]] * line_height) # Represents a single column of 'off' dots
        if char_space_width > 0 :
             self.char_space.dot_matrix = DotMatrix(np.zeros((line_height, char_space_width), dtype=np.uint8))
        else: # if char_space_width is 0, make it an empty matrix
            self.char_space.dot_matrix = DotMatrix(np.zeros((line_height, 0), dtype=np.uint8))


    def add_char(self, char_str: str, matrix_data: list[list[int]]):
        # Ensure matrix_data has the correct line_height
        if any(len(row) > 0 for row in matrix_data): # only check if matrix_data is not for an empty char
            assert all(len(row) == len(matrix_data[0]) for row in matrix_data), \
                f"All rows in char '{char_str}' matrix must have same width"
        assert len(matrix_data) == self.line_height, \
            f"Char '{char_str}' matrix height {len(matrix_data)} must match font line_height {self.line_height}"
        self.char_data[char_str] = MockChar(char_str, matrix_data)

    def get_chars(self, text: str) -> list[MockChar]:
        # For simplicity, if a char is not found, return a default representation (e.g., a space or a block)
        # Actual font handling might raise an error or have a specific unknown char symbol.
        default_char_matrix = [[0] * 1] * self.line_height # A single column of 'off' dots for unknown chars
        return [
            self.char_data.get(char, MockChar(char, default_char_matrix))
            for char in text
        ]

# Create a global mock font instance for tests
MOCK_FONT_HEIGHT = 3
MOCK_CHAR_SPACE_WIDTH = 1
mock_font_instance = MockFont("test_font", MOCK_FONT_HEIGHT, MOCK_CHAR_SPACE_WIDTH)
mock_font_instance.add_char("A", [[1], [1], [1]]) # 1x3 char
mock_font_instance.add_char("B", [[1,1], [1,1], [1,1]]) # 2x3 char
mock_font_instance.add_char(" ", [[0], [0], [0]]) # 1x3 space char, content usually ignored by string_to_dots

mock_font_no_space = MockFont("no_space_font", MOCK_FONT_HEIGHT, 0) # Font with 0 width char_space
mock_font_no_space.add_char("A", [[1], [1], [1]])
mock_font_no_space.add_char(" ", [[0],[0],[0]])


@patch('flipdot.text.get_font') # Patch the get_font function in flipdot.text module
class TestStringToDots:
    def test_empty_string(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_instance
        result = string_to_dots("", "test_font")
        assert result.shape == (MOCK_FONT_HEIGHT, 0)

    def test_single_char(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_instance
        result = string_to_dots("A", "test_font")
        # Expected: Char 'A' + trailing space
        # 'A' is 1x3. Trailing space is MOCK_CHAR_SPACE_WIDTHx3 (1x3). Total width = 1 + 1 = 2.
        expected_matrix = mat([
            [1, 0],
            [1, 0],
            [1, 0]
        ])
        assert np.array_equal(result.mat, expected_matrix)
        assert result.shape == (MOCK_FONT_HEIGHT, 1 + MOCK_CHAR_SPACE_WIDTH)

    def test_multiple_chars(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_instance
        result = string_to_dots("AB", "test_font")
        # Expected: A + space + B + trailing_space
        # A (1x3), space (1x3), B (2x3), trailing_space (1x3)
        # Total width = 1 + 1 + 2 + 1 = 5
        expected_matrix = mat([
            [1, 0, 1, 1, 0],
            [1, 0, 1, 1, 0],
            [1, 0, 1, 1, 0]
        ])
        assert np.array_equal(result.mat, expected_matrix)
        assert result.shape == (MOCK_FONT_HEIGHT, 1 + MOCK_CHAR_SPACE_WIDTH + 2 + MOCK_CHAR_SPACE_WIDTH)

    def test_string_with_spaces(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_instance
        result = string_to_dots("A B", "test_font")
        # Expected: A + space_char_from_font + B + trailing_space
        # A (1x3), actual space char (1x3), B (2x3), trailing_space (1x3)
        # Note: string_to_dots logic: if char is " " or prev_char is " ", no *extra* char_space is added.
        # The " " char from font.get_chars(" ") is added directly.
        # A (1x3) + space_char (1x3) + B (2x3) + trailing_space (1x3)
        # Total width = 1 + 1 + 2 + 1 = 5
        expected_matrix = mat([
            [1, 0, 0, 1, 1, 0], # A, space_char_matrix, B, trailing_space
            [1, 0, 0, 1, 1, 0],
            [1, 0, 0, 1, 1, 0]
        ])
        # A (1) + space_char (1) + B (2) + trailing_space (1) = 5
        assert result.width == mock_font_instance.char_data['A'].width + \
                               mock_font_instance.char_data[' '].width + \
                               mock_font_instance.char_data['B'].width + \
                               mock_font_instance.char_space.width
        
        # Detailed check:
        # A: [[1],[1],[1]]
        # Space char (mocked as 1 wide '0'): [[0],[0],[0]]
        # B: [[1,1],[1,1],[1,1]]
        # Trailing space (1 wide '0'): [[0],[0],[0]]
        # Concatenated:
        # [1, 0, 1, 1, 0]
        # [1, 0, 1, 1, 0]
        # [1, 0, 1, 1, 0]
        # This was my manual expectation. The current code's logic regarding first_char_processed and prev_char might be slightly different.
        # Let's re-verify the string_to_dots logic for "A B":
        # 1. char='A': spaced_chars = A (no leading space as first_char_processed=false) -> [[1],[1],[1]] ; prev_char='A', first_char_processed=true
        # 2. char=' ': (first_char_processed=true, char.char=" ", prev_char.char="A"!= " ") -> NO font.char_space added.
        #              spaced_chars += space_char_matrix -> [[1,0],[1,0],[1,0]] ; prev_char=' '
        # 3. char='B': (first_char_processed=true, char.char="B"!=" ", prev_char.char==" ") -> NO font.char_space added.
        #              spaced_chars += B_matrix -> [[1,0,1,1],[1,0,1,1],[1,0,1,1]] ; prev_char='B'
        # 4. Trailing space: spaced_chars += font.char_space -> [[1,0,1,1,0],[1,0,1,1,0],[1,0,1,1,0]]
        # This matches the expected_matrix above.
        assert np.array_equal(result.mat, expected_matrix)


    def test_unknown_char(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_instance
        result = string_to_dots("X", "test_font") # 'X' is not in our mock_font
        # Expected: Default char (1x3 all zeros) + trailing_space (1x3)
        # Total width = 1 + 1 = 2
        default_char_width = 1 # As defined in MockFont.get_chars
        expected_matrix = mat([
            [0, 0],
            [0, 0],
            [0, 0]
        ])
        assert np.array_equal(result.mat, expected_matrix)
        assert result.shape == (MOCK_FONT_HEIGHT, default_char_width + MOCK_CHAR_SPACE_WIDTH)

    def test_font_with_no_char_spacing(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_no_space # Font where char_space.width is 0
        result = string_to_dots("AA", "test_font_no_space")
        # Expected: A + A (no inter-char space, no trailing space if char_space.width is 0)
        # A (1x3) + A (1x3)
        # Total width = 1 + 1 = 2
        # The current string_to_dots logic adds font.char_space.dot_matrix.
        # If this matrix is 0-width, it should effectively add nothing.
        expected_matrix = mat([
            [1, 1],
            [1, 1],
            [1, 1]
        ])
        assert np.array_equal(result.mat, expected_matrix)
        assert result.shape == (MOCK_FONT_HEIGHT, 1 + 1) # A_width + A_width
        
    def test_string_starting_with_space(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_instance
        result = string_to_dots(" A", "test_font")
        # Expected: space_char_from_font + A + trailing_space
        # space_char (1x3) + A (1x3) + trailing_space (1x3)
        # No extra space before 'A' because prev_char was ' '.
        # Total width = 1 + 1 + 1 = 3
        expected_matrix = mat([
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0]
        ])
        assert np.array_equal(result.mat, expected_matrix)
        assert result.shape == (MOCK_FONT_HEIGHT, 
                                mock_font_instance.char_data[' '].width + 
                                mock_font_instance.char_data['A'].width + 
                                mock_font_instance.char_space.width)

    def test_string_ending_with_space(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_instance
        result = string_to_dots("A ", "test_font")
        # Expected: A + space_char_from_font + trailing_space
        # A (1x3) + space_char (1x3) + trailing_space (1x3)
        # No extra space before ' ' because current char is ' '.
        # Total width = 1 + 1 + 1 = 3
        expected_matrix = mat([
            [1, 0, 0],
            [1, 0, 0],
            [1, 0, 0]
        ])
        assert np.array_equal(result.mat, expected_matrix)
        assert result.shape == (MOCK_FONT_HEIGHT,
                                mock_font_instance.char_data['A'].width + 
                                mock_font_instance.char_data[' '].width + 
                                mock_font_instance.char_space.width)

    def test_string_with_only_spaces(self, mock_get_font: MagicMock):
        mock_get_font.return_value = mock_font_instance
        result = string_to_dots("  ", "test_font") # Two spaces
        # Expected: space_char + space_char + trailing_space
        # space_char (1x3) + space_char (1x3) + trailing_space (1x3)
        # Total width = 1 + 1 + 1 = 3
        expected_matrix = mat([
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ])
        assert np.array_equal(result.mat, expected_matrix)
        assert result.shape == (MOCK_FONT_HEIGHT,
                                mock_font_instance.char_data[' '].width * 2 + 
                                mock_font_instance.char_space.width)

# To run these tests:
# Ensure pytest and numpy are installed.
# Navigate to the project root directory in the terminal.
# Run the command: pytest
# (Or poetry run pytest if using poetry environments)
