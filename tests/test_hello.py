"""
Unit tests for hello.py Lambda function
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hello import lambda_handler


def test_lambda_handler(capsys):
    """Test that lambda_handler returns correct response and logs message"""
    response = lambda_handler({}, None)
    
    assert response == {
        'statusCode': 200,
        'body': 'Hello World!'
    }
    
    captured = capsys.readouterr()
    assert "Hello World from Lambda!" in captured.out

