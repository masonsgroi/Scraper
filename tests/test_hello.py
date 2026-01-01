"""
Unit tests for hello.py Lambda function
"""
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hello import lambda_handler


@patch.dict(os.environ, {'S3_BUCKET': 'test-bucket'})
@patch('hello.boto3')
@patch('hello.get_version')
def test_lambda_handler_success(mock_get_version, mock_boto3, capsys):
    """Test that lambda_handler writes timestamp to S3 successfully"""
    # Mock version
    mock_get_version.return_value = '0.1'
    
    # Mock S3 client
    mock_s3_client = Mock()
    mock_boto3.client.return_value = mock_s3_client
    
    # Call handler
    response = lambda_handler({}, None)
    
    # Verify S3 client was created and put_object was called
    mock_boto3.client.assert_called_once_with('s3')
    assert mock_s3_client.put_object.called
    
    # Verify put_object arguments
    call_args = mock_s3_client.put_object.call_args
    assert call_args[1]['Bucket'] == 'test-bucket'
    assert call_args[1]['Key'].startswith('timestamps/')
    assert call_args[1]['Key'].endswith('.txt')
    assert call_args[1]['ContentType'] == 'text/plain'
    
    # Verify response
    assert response['statusCode'] == 200
    assert 'Timestamp written to s3://test-bucket/timestamps/' in response['body']
    
    # Verify log output includes version
    captured = capsys.readouterr()
    assert "Scraper version 0.1" in captured.out
    assert "Timestamp written to s3://test-bucket/timestamps/" in captured.out


@patch('hello.get_version')
def test_lambda_handler_missing_bucket(mock_get_version, capsys):
    """Test that lambda_handler fails gracefully when S3_BUCKET is not set"""
    # Mock version
    mock_get_version.return_value = '0.1'
    
    # Ensure S3_BUCKET is not set
    with patch.dict(os.environ, {}, clear=True):
        response = lambda_handler({}, None)
    
    # Verify error response
    assert response['statusCode'] == 500
    assert 'S3_BUCKET environment variable not set' in response['body']
    
    # Verify error log
    captured = capsys.readouterr()
    assert "Scraper version 0.1" in captured.out
    assert "ERROR: S3_BUCKET environment variable not set" in captured.out


@patch.dict(os.environ, {'S3_BUCKET': 'test-bucket'})
@patch('hello.boto3')
@patch('hello.get_version')
def test_lambda_handler_s3_error(mock_get_version, mock_boto3, capsys):
    """Test that lambda_handler handles S3 errors gracefully"""
    # Mock version
    mock_get_version.return_value = '0.1'
    
    # Mock S3 client to raise exception
    mock_s3_client = Mock()
    mock_s3_client.put_object.side_effect = Exception("S3 access denied")
    mock_boto3.client.return_value = mock_s3_client
    
    # Call handler
    response = lambda_handler({}, None)
    
    # Verify error response
    assert response['statusCode'] == 500
    assert 'Failed to write to S3: S3 access denied' in response['body']
    
    # Verify error log
    captured = capsys.readouterr()
    assert "Scraper version 0.1" in captured.out
    assert "ERROR: Failed to write to S3: S3 access denied" in captured.out

