import pytest
from backend.game_logic import evaluate_guess

def test_exact_match():
    result = evaluate_guess("CRANE", "CRANE")
    assert result == ["green", "green", "green", "green", "green"]

def test_partial_match():
    # Word = CRANE, Guess = CANOE
    result = evaluate_guess("CRANE", "CANOE")
    # C (green), A (orange), N (green), O (grey), E (green)
    assert result == ["green", "orange", "green", "grey", "green"]

def test_no_match():
    result = evaluate_guess("CRANE", "MOUTH")
    assert result == ["grey", "grey", "grey", "grey", "grey"]

def test_case_insensitive():
    result = evaluate_guess("CRANE", "crane")
    assert all(color == "green" for color in result)
