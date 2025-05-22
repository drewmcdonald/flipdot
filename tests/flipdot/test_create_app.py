import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi.testclient import TestClient
from pydantic import BaseModel

# Assume flipdot.create_app.create_app is the function that creates the FastAPI app
from flipdot.create_app import create_app, Config as AppConfig # Import Config for type hinting
from flipdot.State import State, StateObject
from flipdot.layout import Layout
# Removed get_display_mode_names, get_font_names from this import
from flipdot.mode import DisplayModeRef, BaseDisplayMode, DisplayModeConfig 
from flipdot.font import FontList, DotFontRef # Import for mock return types
from flipdot.mode.Clock import ClockOptions # Corrected from previous fix

# --- Mocks and Test Setup ---

# Mock Panel and Serial Connection
mock_panel = MagicMock()
mock_panel.total_width = 100
mock_panel.total_height = 20

mock_serial_conn = MagicMock()

# Mock State: This is a simplified mock.
# In a real scenario, you might need a more sophisticated mock or a test fixture
# that provides a State-like object.
mock_state_instance = MagicMock(spec=State)
mock_state_instance.layout = Layout.from_panel(mock_panel)
mock_state_instance.inverted = False
mock_state_instance.flag = False
mock_state_instance.errors = []
mock_state_instance.dev = True # Set dev to True for testing purposes


# A dummy display mode for testing set_mode
class MockTestMode(BaseDisplayMode):
    class Options(BaseModel):
        test_opt: str = "default"

    def render(self) -> "DotMatrix": # type: ignore
        # Not actually called in these tests if State.set_mode is mocked well
        return MagicMock() 
    
    @classmethod
    def get_name(cls) -> str:
        return "TestMode"

@pytest.fixture(scope="module")
def client():
    # Patch external dependencies for the app creation context
    # Note: Patches for list_fonts and list_display_modes are applied directly in the test_get_config test method
    with patch('flipdot.create_app.Panel', return_value=mock_panel) as mock_panel_cls, \
         patch('flipdot.create_app.serial.Serial', return_value=mock_serial_conn) as mock_serial_cls, \
         patch('flipdot.create_app.State', return_value=mock_state_instance) as mock_state_cls, \
         patch('flipdot.create_app.asyncio.create_task') as mock_create_task: # Mock display loop start

        # The actual app creation
        # Default mode for testing
        default_mode_ref = DisplayModeRef(mode_name="Clock", opts=ClockOptions(font="telematrix", format="%H:%M").model_dump())
        
        app = create_app(
            panel=mock_panel, 
            serial_conn=mock_serial_conn, 
            default_mode=default_mode_ref,
            dev=True # Corrected dev_mode to dev
        )
        # The TestClient wraps the app
        with TestClient(app) as c:
            yield c
        # Cleanup if necessary, though TestClient handles lifespan for sync context


# Reset relevant parts of the global mock_state_instance before each test
@pytest.fixture(autouse=True)
def reset_mock_state():
    mock_state_instance.reset_mock() # Resets call counts, etc.
    # Re-assign specific attributes if they are modified by tests or need a default state
    mock_state_instance.layout = Layout.from_panel(mock_panel)
    mock_state_instance.inverted = False
    mock_state_instance.flag = False
    mock_state_instance.errors = []
    mock_state_instance.dev = True
    
    # Default mode reference for the mock_state_instance
    default_mode_opts_obj = ClockOptions(font="telematrix", format="%H:%M")
    default_display_mode_ref = DisplayModeRef(mode_name="Clock", opts=default_mode_opts_obj.model_dump())
    
    # Mock the to_ref method for the default mode on the state's mode object
    # This requires state.mode to also be a mock that has a to_ref method.
    mock_current_mode = MagicMock(spec=BaseDisplayMode)
    mock_current_mode.to_ref.return_value = default_display_mode_ref
    mock_state_instance.mode = mock_current_mode

    # Mock to_object to return a valid StateObject based on current mock_state_instance attributes
    def _get_state_object():
        return StateObject(
            mode=mock_state_instance.mode.to_ref(),
            errors=list(mock_state_instance.errors),
            layout=mock_state_instance.layout,
            inverted=mock_state_instance.inverted,
            flag=mock_state_instance.flag
        )
    mock_state_instance.to_object.side_effect = _get_state_object
    
    # Mock set_mode to be an async function for TestClient compatibility
    mock_state_instance.set_mode = AsyncMock()


# --- Test Cases ---

def test_heartbeat(client: TestClient):
    response = client.get("/api/heartbeat")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

# Corrected patches for test_get_config
@patch('flipdot.create_app.list_fonts')
@patch('flipdot.create_app.list_display_modes')
def test_get_config(mock_list_display_modes_func, mock_list_fonts_func, client: TestClient):
    # Setup mock return values
    mock_fonts_data = {
        "font1": DotFontRef(name="font1", line_height=7, space_width=3, width_between_chars=1),
        "font2": DotFontRef(name="font2", line_height=5, space_width=2, width_between_chars=1)
    }
    mock_list_fonts_func.return_value = FontList(fonts=mock_fonts_data)
    
    mock_modes_data = [
        DisplayModeConfig(mode_name="ModeA", opts={"type": "object", "properties": {"opt1": {"type": "string"}}}),
        DisplayModeConfig(mode_name="ModeB", opts={"type": "object", "properties": {"opt2": {"type": "integer"}}})
    ]
    mock_list_display_modes_func.return_value = mock_modes_data

    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    
    # Validate against the structure of AppConfig and the mocked data
    assert data["fonts"]["fonts"] == {k: v.model_dump() for k, v in mock_fonts_data.items()}
    assert data["modes"] == [m.model_dump() for m in mock_modes_data]
    assert data["dimensions"]["width"] == mock_panel.total_width
    assert data["dimensions"]["height"] == mock_panel.total_height
    
    mock_list_fonts_func.assert_called_once()
    mock_list_display_modes_func.assert_called_once()


def test_get_current_mode(client: TestClient):
    # The mock_state_instance.mode.to_ref() is configured in reset_mock_state
    expected_mode_ref = mock_state_instance.mode.to_ref()

    response = client.get("/api/mode")
    assert response.status_code == 200
    assert response.json() == expected_mode_ref.model_dump() # Pydantic models are often dumped for JSON


@patch('flipdot.create_app.get_display_mode') # To return our MockTestMode
def test_set_valid_mode(mock_get_mode_cls, client: TestClient):
    mock_get_mode_cls.return_value = MockTestMode # Return the class itself

    new_mode_data = {"mode_name": "TestMode", "opts": {"test_opt": "new_value"}}
    
    response = client.patch("/api/mode", json=new_mode_data)
    assert response.status_code == 200
    
    # Check that state.set_mode was called with a DisplayModeRef matching new_mode_data
    mock_state_instance.set_mode.assert_called_once()
    called_arg = mock_state_instance.set_mode.call_args[0][0] # Get the first positional arg
    assert isinstance(called_arg, DisplayModeRef)
    assert called_arg.mode_name == "TestMode"
    assert called_arg.opts["test_opt"] == "new_value"

    # Check that the response is the new mode (as if state.set_mode updated it and to_ref reflects it)
    # For this, we need to make state.mode.to_ref() return the new mode after set_mode is called
    # This can be done by configuring the side_effect of set_mode or state.mode.to_ref directly
    
    # Simulate that state.mode was updated by set_mode
    updated_mode_mock = MagicMock(spec=BaseDisplayMode)
    updated_mode_mock.to_ref.return_value = DisplayModeRef(**new_mode_data)
    mock_state_instance.mode = updated_mode_mock # Assume set_mode changed this

    # Now when state.to_object() is called by the endpoint, it uses the updated state.mode
    assert response.json() == new_mode_data


@patch('flipdot.create_app.get_display_mode', side_effect=KeyError("Mode not found"))
def test_set_non_existent_mode(mock_get_mode_cls, client: TestClient):
    new_mode_data = {"mode_name": "NonExistentMode", "opts": {}}
    response = client.patch("/api/mode", json=new_mode_data)
    assert response.status_code == 404
    assert "Mode NonExistentMode not found" in response.json()["detail"]


@patch('flipdot.create_app.get_display_mode') # Return a mode that has options
def test_set_mode_with_invalid_options(mock_get_mode_cls, client: TestClient):
    # Use ClockMode as an example, assuming ClockOptions requires 'font' and 'format'
    # We'll make get_display_mode return the actual Clock class for option validation
    from flipdot.mode.Clock import Clock # Import the actual class
    mock_get_mode_cls.return_value = Clock

    # Missing 'format' option
    invalid_opts_data = {"mode_name": "Clock", "opts": {"font": "somefont"}} 
    
    response = client.patch("/api/mode", json=invalid_opts_data)
    assert response.status_code == 422 # Pydantic validation error
    # Check some part of the error detail if necessary, e.g. "field required" for "format"
    assert "detail" in response.json()
    # Example check, structure might vary slightly based on FastAPI/Pydantic version
    assert any("format" in err["loc"] and "Missing" in err["type"] for err in response.json()["detail"])


def test_set_mode_empty_payload(client: TestClient):
    response = client.patch("/api/mode", json={})
    assert response.status_code == 422 # mode_name is required


@pytest.mark.asyncio
async def test_display_loop_task_creation():
     # Test that the display loop is started
     # This requires a bit more involved setup if we want to test it properly.
     # For now, we'll just check if create_task was called in the client fixture.
     # The client fixture already patches create_task.
     # We need to access the mock from there, or re-patch here.
    with patch('flipdot.create_app.asyncio.create_task') as mock_create_task_in_test:
        default_mode_opts_obj = ClockOptions(font="telematrix", format="%H:%M")
        default_mode_ref = DisplayModeRef(mode_name="Clock", opts=default_mode_opts_obj.model_dump())
        app = create_app(
            panel=mock_panel, 
            serial_conn=mock_serial_conn, 
            default_mode=default_mode_ref,
            dev=True # Corrected dev_mode to dev
        )
        # Check that asyncio.create_task was called with state.display_loop
        # This assumes state_instance is accessible or the one created inside create_app
        # For this test, it's simpler to check if it was called at all
        # as the client fixture already does this.
        # If we need to check arguments, we'd need the state instance from app.state
        
        # A simple check that create_task is called when create_app is invoked
        assert mock_create_task_in_test.called
        # To check arguments, you would do:
        # state_instance_from_app = app.dependency_overrides[get_state]() # if using FastAPI dependencies this way
        # mock_create_task_in_test.assert_called_once_with(state_instance_from_app.display_loop())
        # However, direct access to state like app.state might be easier if create_app sets it.
        # The provided code structure implies app.state.display_loop() is what gets called.
        # Let's assume create_app makes the state available, e.g., app.state = State(...)
        # For the current structure of create_app, it creates State internally.
        
        # The client fixture already has a mock_create_task.
        # This test is a bit redundant with the fixture but shows intent.
        # To properly test this without the client fixture's patch,
        # we'd need to call create_app directly here.
        pass # The assertion is implicitly in the client fixture setup if it's broad enough.
             # The client fixture's mock_create_task will catch the call when TestClient(app) is made.
             # No direct assertion here unless we want to be more specific about the call args.

# Example of how to test if the display_loop was started (from client fixture)
# This test doesn't run on its own but illustrates the check
# def test_display_loop_started_via_fixture(client_fixture_mock_create_task):
#     assert client_fixture_mock_create_task.called

# Note: Testing the display_loop functionality itself (what it does)
# would be more complex and might require more targeted async testing utilities.
# The current test just ensures it's initiated.
