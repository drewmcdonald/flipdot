import pytest
import numpy as np

from flipdot.DotMatrix import DotMatrix
from flipdot.layout import Layout
from flipdot.mode.solid import White, Black
from flipdot.mode.BaseDisplayMode import DisplayModeOptions # Corrected import path

# Mock layout details
MOCK_LAYOUT_WIDTH = 20
MOCK_LAYOUT_HEIGHT = 7

@pytest.fixture
def mock_layout():
    return Layout(width=MOCK_LAYOUT_WIDTH, height=MOCK_LAYOUT_HEIGHT)

@pytest.fixture
def white_mode(mock_layout):
    # Solid modes don't have specific options in SolidModeOptions currently
    # but we pass the empty model for consistency.
    opts = DisplayModeOptions() # Replaced SolidModeOptions
    mode = White(layout=mock_layout, opts=opts)
    return mode

@pytest.fixture
def black_mode(mock_layout):
    opts = DisplayModeOptions() # Replaced SolidModeOptions
    mode = Black(layout=mock_layout, opts=opts)
    return mode

class TestSolidModes:
    # --- White Mode Tests ---
    def test_white_mode_should_render_once(self, white_mode):
        assert white_mode.should_render() is True  # First call
        object.__setattr__(white_mode, 'rendered_once', True) # Simulate it has rendered
        assert white_mode.should_render() is False # Subsequent calls

    def test_white_mode_render(self, white_mode, mock_layout):
        frame = white_mode.render()
        assert frame.shape == (mock_layout.height, mock_layout.width)
        # For White mode, matrix should be full of 1s (or non-zeros).
        # The DotMatrix created by White uses np.ones.
        expected_matrix = np.ones((mock_layout.height, mock_layout.width), dtype=np.uint8)
        assert np.array_equal(frame.mat, expected_matrix)

    def test_white_mode_setup_resets_rendered_once(self, white_mode):
        object.__setattr__(white_mode, 'rendered_once', True)
        assert white_mode.should_render() is False
        white_mode.setup()
        assert white_mode.rendered_once is False
        assert white_mode.should_render() is True

    # --- Black Mode Tests ---
    def test_black_mode_should_render_once(self, black_mode):
        assert black_mode.should_render() is True  # First call
        object.__setattr__(black_mode, 'rendered_once', True) # Simulate it has rendered
        assert black_mode.should_render() is False # Subsequent calls

    def test_black_mode_render(self, black_mode, mock_layout):
        frame = black_mode.render()
        assert frame.shape == (mock_layout.height, mock_layout.width)
        # For Black mode, matrix should be full of 0s.
        # The DotMatrix created by Black uses np.zeros.
        expected_matrix = np.zeros((mock_layout.height, mock_layout.width), dtype=np.uint8)
        assert np.array_equal(frame.mat, expected_matrix)

    def test_black_mode_setup_resets_rendered_once(self, black_mode):
        object.__setattr__(black_mode, 'rendered_once', True)
        assert black_mode.should_render() is False
        black_mode.setup()
        assert black_mode.rendered_once is False
        assert black_mode.should_render() is True

    # --- Test Tick Interval (inherited from BaseDisplayMode) ---
    def test_solid_modes_tick_interval(self, white_mode, black_mode):
        # Solid modes are static, so they don't need frequent updates.
        # The tick_interval is used by the display loop to determine how often to call should_render.
        # They inherit the default from BaseDisplayMode, which is 1.0.
        assert white_mode.tick_interval == 1.0
        assert black_mode.tick_interval == 1.0

    # Test that opts are passed (even if not used by White/Black specifically yet)
    def test_solid_modes_accept_opts(self, mock_layout):
        # This test is more about ensuring the class structure supports options
        # if they were to be added to SolidModeOptions in the future.
        custom_opts = DisplayModeOptions() # Replaced SolidModeOptions
        
        white = White(layout=mock_layout, opts=custom_opts)
        assert white.opts is custom_opts

        black = Black(layout=mock_layout, opts=custom_opts)
        assert black.opts is custom_opts
