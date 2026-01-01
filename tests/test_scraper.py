"""
Unit tests for scraper.py Lambda function
"""
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scraper import lambda_handler, scrape_lift_data, upload_df_to_s3


@patch.dict(os.environ, {'S3_BUCKET': 'test-bucket'})
@patch('scraper.scrape_lift_data')
@patch('scraper.upload_df_to_s3')
@patch('scraper.get_version')
def test_lambda_handler_success(mock_get_version, mock_upload, mock_scrape, capsys):
    """Test that lambda_handler scrapes and uploads to S3 successfully"""
    # Mock version
    mock_get_version.return_value = '0.4'
    
    # Mock scrape_lift_data to return sample DataFrames
    status_df = pd.DataFrame([
        {"Lift": "Lift 1", "Status": "Open"},
        {"Lift": "Lift 2", "Status": "Closed"}
    ])
    wait_time_df = pd.DataFrame([
        {"Lift": "Lift 1", "Wait Time": 5},
        {"Lift": "Lift 2", "Wait Time": "N/A"}
    ])
    mock_scrape.return_value = (status_df, wait_time_df)
    
    # Call handler
    response = lambda_handler({}, None)
    
    # Verify scrape was called
    mock_scrape.assert_called_once()
    
    # Verify upload was called twice (status and wait_time)
    assert mock_upload.call_count == 2
    
    # Verify response
    assert response['statusCode'] == 200
    assert 'Scraper completed' in response['body']
    assert '2 lifts' in response['body']
    
    # Verify log output includes version
    captured = capsys.readouterr()
    assert "Scraper version 0.4" in captured.out
    assert "Starting scrape..." in captured.out


@patch('scraper.get_version')
def test_lambda_handler_missing_bucket(mock_get_version, capsys):
    """Test that lambda_handler fails gracefully when S3_BUCKET is not set"""
    # Mock version
    mock_get_version.return_value = '0.4'
    
    # Ensure S3_BUCKET is not set
    with patch.dict(os.environ, {}, clear=True):
        response = lambda_handler({}, None)
    
    # Verify error response
    assert response['statusCode'] == 500
    assert 'S3_BUCKET environment variable not set' in response['body']
    
    # Verify error log
    captured = capsys.readouterr()
    assert "Scraper version 0.4" in captured.out
    assert "ERROR: S3_BUCKET environment variable not set" in captured.out


@patch.dict(os.environ, {'S3_BUCKET': 'test-bucket'})
@patch('scraper.scrape_lift_data')
@patch('scraper.get_version')
def test_lambda_handler_scrape_error(mock_get_version, mock_scrape, capsys):
    """Test that lambda_handler handles scraping errors gracefully"""
    # Mock version
    mock_get_version.return_value = '0.4'
    
    # Mock scrape_lift_data to raise exception
    mock_scrape.side_effect = Exception("Network error")
    
    # Call handler
    response = lambda_handler({}, None)
    
    # Verify error response
    assert response['statusCode'] == 500
    assert 'Scraper failed: Network error' in response['body']
    
    # Verify error log
    captured = capsys.readouterr()
    assert "Scraper version 0.4" in captured.out
    assert "ERROR: Scraper failed: Network error" in captured.out


@patch('scraper.fetch_json_from_url')
def test_scrape_lift_data(mock_fetch, capsys):
    """Test that scrape_lift_data fetches and parses data correctly"""
    # Mock API responses
    mock_fetch.side_effect = [
        {
            "lifts": [
                {"name": "Lift A", "status": "Open", "waitTime": 5},
                {"name": "Lift B", "status": "Closed", "waitTime": "N/A"}
            ]
        },
        {
            "lifts": [
                {"name": "Lift C", "status": "Open", "waitTime": 10}
            ]
        }
    ]
    
    # Call scrape_lift_data
    status_df, wait_time_df = scrape_lift_data()
    
    # Verify DataFrames have correct structure
    assert len(status_df) == 3
    assert len(wait_time_df) == 3
    assert list(status_df.columns) == ["Lift", "Status"]
    assert list(wait_time_df.columns) == ["Lift", "Wait Time"]
    
    # Verify data
    assert status_df.iloc[0]["Lift"] == "Lift A"
    assert status_df.iloc[0]["Status"] == "Open"
    assert wait_time_df.iloc[0]["Wait Time"] == 5
    
    # Verify logs
    captured = capsys.readouterr()
    assert "Lift: Lift A, Status: Open, Wait Time: 5 minutes" in captured.out


@patch('scraper.boto3')
def test_upload_df_to_s3(mock_boto3, capsys):
    """Test that upload_df_to_s3 uploads DataFrame as CSV"""
    # Mock S3 client
    mock_s3_client = Mock()
    mock_boto3.client.return_value = mock_s3_client
    
    # Create test DataFrame
    df = pd.DataFrame([
        {"Lift": "Test Lift", "Status": "Open"}
    ])
    
    # Call upload_df_to_s3
    upload_df_to_s3(df, 'test-bucket', 'test/file.csv')
    
    # Verify S3 client was called correctly
    mock_boto3.client.assert_called_once_with('s3')
    mock_s3_client.put_object.assert_called_once()
    
    # Verify put_object arguments
    call_args = mock_s3_client.put_object.call_args
    assert call_args[1]['Bucket'] == 'test-bucket'
    assert call_args[1]['Key'] == 'test/file.csv'
    assert call_args[1]['ContentType'] == 'text/csv'
    assert 'Test Lift' in call_args[1]['Body']
    
    # Verify log
    captured = capsys.readouterr()
    assert "Uploaded test/file.csv to s3://test-bucket/test/file.csv" in captured.out

