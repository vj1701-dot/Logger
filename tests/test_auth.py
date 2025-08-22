import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from src.auth.jwt_handler import JWTHandler

@pytest.fixture
def jwt_handler():
    return JWTHandler()

def test_create_token(jwt_handler):
    """Test JWT token creation"""
    user_data = {
        "telegram_id": 12345,
        "name": "Test User",
        "username": "testuser",
        "role": "user"
    }
    
    token = jwt_handler.create_token(user_data)
    
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_token_valid(jwt_handler):
    """Test JWT token verification with valid token"""
    user_data = {
        "telegram_id": 12345,
        "name": "Test User",
        "username": "testuser",
        "role": "user"
    }
    
    token = jwt_handler.create_token(user_data)
    payload = jwt_handler.verify_token(token)
    
    assert payload is not None
    assert payload["telegram_id"] == 12345
    assert payload["name"] == "Test User"
    assert payload["role"] == "user"

def test_verify_token_invalid(jwt_handler):
    """Test JWT token verification with invalid token"""
    invalid_token = "invalid.token.here"
    
    payload = jwt_handler.verify_token(invalid_token)
    
    assert payload is None

def test_verify_token_expired(jwt_handler):
    """Test JWT token verification with expired token"""
    # Create a handler with very short TTL
    with patch('src.auth.jwt_handler.settings') as mock_settings:
        mock_settings.JWT_TTL_MIN = -1  # Already expired
        mock_settings.JWT_SIGNING_KEY = "test-key"
        
        expired_handler = JWTHandler()
        user_data = {
            "telegram_id": 12345,
            "name": "Test User",
            "role": "user"
        }
        
        token = expired_handler.create_token(user_data)
        
        # Token should be expired immediately
        payload = expired_handler.verify_token(token)
        assert payload is None

def test_create_magic_link_token(jwt_handler):
    """Test magic link token creation"""
    telegram_id = 12345
    
    token = jwt_handler.create_magic_link_token(telegram_id)
    
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_magic_link_token_valid(jwt_handler):
    """Test magic link token verification with valid token"""
    telegram_id = 12345
    
    token = jwt_handler.create_magic_link_token(telegram_id)
    result = jwt_handler.verify_magic_link_token(token)
    
    assert result == telegram_id

def test_verify_magic_link_token_invalid(jwt_handler):
    """Test magic link token verification with invalid token"""
    invalid_token = "invalid.token.here"
    
    result = jwt_handler.verify_magic_link_token(invalid_token)
    
    assert result is None

def test_verify_magic_link_token_wrong_type(jwt_handler):
    """Test magic link token verification with regular token"""
    user_data = {
        "telegram_id": 12345,
        "name": "Test User",
        "role": "user"
    }
    
    # Create regular token, not magic link token
    regular_token = jwt_handler.create_token(user_data)
    result = jwt_handler.verify_magic_link_token(regular_token)
    
    # Should return None because it's not a magic link token
    assert result is None

if __name__ == "__main__":
    pytest.main([__file__])