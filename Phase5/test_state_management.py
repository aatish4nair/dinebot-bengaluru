"""
Tests for Phase 5 state management.
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def test_init_session_state():
    """init_session_state sets expected keys (we mock st.session_state)."""
    class MockSt:
        session_state = {}
    st = MockSt()
    from Phase5.state_management import init_session_state
    init_session_state(st)
    assert "place" in st.session_state
    assert "recommendations" in st.session_state
    assert st.session_state["recommendations"] == []
    assert "error_message" in st.session_state
    assert "loading" in st.session_state


def test_set_recommendations():
    class MockSt:
        session_state = {"recommendations": [], "error_message": "old", "loading": True}
    st = MockSt()
    from Phase5.state_management import set_recommendations
    recs = [object()]
    set_recommendations(st, recs)
    assert st.session_state["recommendations"] == recs
    assert st.session_state["error_message"] is None
    assert st.session_state["loading"] is False


def test_set_error():
    class MockSt:
        session_state = {"recommendations": [1], "error_message": None, "loading": False}
    st = MockSt()
    from Phase5.state_management import set_error
    set_error(st, "Something failed")
    assert st.session_state["error_message"] == "Something failed"
    assert st.session_state["recommendations"] == []
