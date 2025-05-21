import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from flipdot.DotMatrix import DotMatrix
from flipdot.layout import Layout
from flipdot.mode.clock import Clock, ClockModeOptions

# Mock font and layout details
MOCK_FONT_NAME = "test_font"
MOCK_LAYOUT_WIDTH = 20
MOCK_LAYOUT_HEIGHT = 7

@pytest.fixture
def mock_layout():
    layout = Layout(width=MOCK_LAYOUT_WIDTH, height=MOCK_LAYOUT_HEIGHT)
    layout.center_middle = MagicMock(side_effect=lambda x: x) # Simple pass-through mock
    return layout

@pytest.fixture
def clock_mode(mock_layout):
    opts = ClockModeOptions(font=MOCK_FONT_NAME, format="%H:%M")
    mode = Clock(layout=mock_layout, opts=opts)
    return mode

class TestClockMode:
    @patch('flipdot.mode.clock.datetime')
    def test_should_render_minute_change(self, mock_dt, clock_mode):
        # Initial render
        mock_dt.now.return_value = datetime(2023, 1, 1, 10, 0, 0)
        assert clock_mode.should_render() is True # First call, should render
        clock_mode.last_rendered_time = mock_dt.now()

        # Time hasn't changed by a minute
        mock_dt.now.return_value = datetime(2023, 1, 1, 10, 0, 30)
        assert clock_mode.should_render() is False

        # Minute changes
        mock_dt.now.return_value = datetime(2023, 1, 1, 10, 1, 0)
        assert clock_mode.should_render() is True
        clock_mode.last_rendered_time = mock_dt.now()

        # Second changes but minute is the same
        mock_dt.now.return_value = datetime(2023, 1, 1, 10, 1, 30)
        assert clock_mode.should_render() is False
        
        # Hour changes
        mock_dt.now.return_value = datetime(2023, 1, 1, 11, 1, 30)
        assert clock_mode.should_render() is True


    @patch('flipdot.mode.clock.string_to_dots')
    @patch('flipdot.mode.clock.datetime')
    def test_render_calls_string_to_dots_and_center(self, mock_dt, mock_s2d, clock_mode, mock_layout):
        mock_time = datetime(2023, 1, 1, 12, 30, 0)
        mock_dt.now.return_value = mock_time
        
        # Mock what string_to_dots returns
        mock_dot_matrix = DotMatrix.from_shape((MOCK_LAYOUT_HEIGHT, MOCK_LAYOUT_WIDTH - 2)) # Example matrix
        mock_s2d.return_value = mock_dot_matrix

        frame = clock_mode.render()

        # Check string_to_dots call
        expected_time_str = mock_time.strftime(clock_mode.opts.format) # "12:30"
        mock_s2d.assert_called_once_with(expected_time_str, clock_mode.opts.font)

        # Check layout.center_middle call
        mock_layout.center_middle.assert_called_once_with(mock_dot_matrix)
        
        # Check that the returned frame is what center_middle returned (which is mock_dot_matrix due to side_effect)
        assert frame is mock_dot_matrix

    @patch('flipdot.mode.clock.string_to_dots')
    @patch('flipdot.mode.clock.datetime')
    def test_render_different_formats(self, mock_dt, mock_s2d, clock_mode, mock_layout):
        mock_time = datetime(2023, 1, 1, 12, 30, 55) # Include seconds
        mock_dt.now.return_value = mock_time
        mock_s2d.return_value = DotMatrix.from_shape((MOCK_LAYOUT_HEIGHT, 1)) # Dummy matrix

        # Test with HH:MM:SS format
        clock_mode.opts.format = "%H:%M:%S"
        clock_mode.render()
        expected_time_str_hms = mock_time.strftime("%H:%M:%S") # "12:30:55"
        mock_s2d.assert_called_with(expected_time_str_hms, clock_mode.opts.font)
        mock_layout.center_middle.assert_called_with(mock_s2d.return_value)

        # Test with custom format like "It's %I:%M %p"
        clock_mode.opts.format = "It's %I:%M %p"
        clock_mode.render()
        expected_time_str_custom = mock_time.strftime("It's %I:%M %p") # "It's 12:30 PM"
        # call was already made, so check last call
        mock_s2d.assert_called_with(expected_time_str_custom, clock_mode.opts.font)
        mock_layout.center_middle.assert_called_with(mock_s2d.return_value)

    def test_options_default_font(self, mock_layout):
        # Test that default font is applied if not specified
        opts = ClockModeOptions(format="%H:%M") # No font specified
        mode = Clock(layout=mock_layout, opts=opts)
        assert mode.opts.font == "telematrix" # Default from ClockModeOptions

    def test_tick_interval(self, clock_mode):
        # Clock mode should update based on its internal logic (minute changes)
        # but tick_interval can be used for how often should_render is checked.
        # Default tick_interval is 0.5 in BaseDisplayMode.
        assert clock_mode.tick_interval == 0.5 # Check if it inherits default or has its own.
                                             # Clock mode does not override, so it's BaseDisplayMode's.
    
    def test_setup_resets_last_rendered_time(self, clock_mode):
        clock_mode.last_rendered_time = datetime(2000,1,1,1,1,1)
        clock_mode.setup()
        assert clock_mode.last_rendered_time is None

    @patch('flipdot.mode.clock.datetime')
    def test_should_render_true_after_setup(self, mock_dt, clock_mode):
        mock_dt.now.return_value = datetime(2023, 1, 1, 10, 0, 0)
        clock_mode.last_rendered_time = mock_dt.now() # Simulate it has rendered before
        assert clock_mode.should_render() is False # Minute hasn't changed

        clock_mode.setup() # This should reset last_rendered_time
        assert clock_mode.should_render() is True # Now it should render because last_rendered_time is None
