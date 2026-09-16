"""AppTest harness testing the Streamlit UI and AI Assistant drawer for Mateo Garza.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest
from basin_core.data import CachedSource
from basin_core.engine import ScenarioParams
from basin_core.workspace import Workspace

print("Starting AppTest UI harness...")
source = CachedSource()
names = {s["id"]: s["name"].title().replace(" Intl Ap", "").replace(" Rgnl Ap", "") for s in source.manifest["stations"]}
params = ScenarioParams(tuple(names.keys()), (90, 180, 270), (1, 4, 7, 10), 0.35, 0.85, "All stations", 300, 22)
workspace = Workspace(source, params, 6)

app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
app.session_state.workspace = workspace
app.session_state.inspect_id = workspace.selected[0]
app.session_state.page = "Review"
app.session_state.assistant_open = False
app.run()

print(f"Page loaded: {app.session_state.page}")
print("Opening assistant drawer via tab button...")
open_btn = app.button(key="assistant_open_tab_btn")
assert open_btn is not None, "Assistant open tab button should exist"
open_btn.click().run()

print(f"Assistant Open State: {app.session_state.assistant_open}")
assert app.session_state.assistant_open is True

# Verify chat input is present by default without clicking presets!
chat_inputs = [ci for ci in app.chat_input if ci.key == "assistant_chat_input"]
print(f"Chat input widgets found: {len(chat_inputs)}")
assert len(chat_inputs) == 1, "Chat input should be visible by default without preset clicks"
print("Verified: Chat input is visible by default!")

# Test clicking 'Crop deficit' (quick_crop_et)
print("Clicking 'Crop deficit' button (quick_crop_et)...")
crop_btn = app.button(key="quick_crop_et")
assert crop_btn is not None, "Crop deficit button should exist"
crop_btn.click().run()

# Check message generated
messages = app.session_state["assistant_messages"] if "assistant_messages" in app.session_state else []
print(f"Assistant messages in state: {len(messages)}")
assert len(messages) >= 2, "Expected at least user query and assistant response"
last_user_msg = messages[-2]["content"]
last_assistant_msg = messages[-1]["content"]

print(f"\nLast User Action: {last_user_msg}")
print(f"Assistant Response Snippet:\n{last_assistant_msg[:250]}...")

# Send a domain question via chat input
print("\nSubmitting domain question into chat input...")
app.chat_input(key="assistant_chat_input").set_value("What happens at 35% combined storage in Choke Canyon?").run()
messages_after = app.session_state["assistant_messages"] if "assistant_messages" in app.session_state else []
print(f"Messages count after query: {len(messages_after)}")
print(f"Assistant Response to 35% storage:\n{messages_after[-1]['content'][:300]}...")

print("\nUI AppTest verification complete: All checks passed!")
