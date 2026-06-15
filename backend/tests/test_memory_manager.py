from backend.agent.memory_manager import MemoryManager

def test_memory_manager_truncation():
    manager = MemoryManager(max_turns=2)
    history = [
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "1a"},
        {"role": "user", "content": "2"},
        {"role": "assistant", "content": "2a"},
        {"role": "user", "content": "3"},
        {"role": "assistant", "content": "3a"}
    ]
    
    # Should only keep the last 2 turns (4 messages)
    context = manager.get_context_window(history)
    
    assert "User: 1" not in context
    assert "User: 2" in context
    assert "Assistant: 2a" in context
    assert "User: 3" in context
    assert "Assistant: 3a" in context

def test_memory_manager_empty():
    manager = MemoryManager(max_turns=2)
    assert manager.get_context_window([]) == ""
