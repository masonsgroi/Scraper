def lambda_handler(event, context):
    """
    AWS Lambda handler function that prints Hello World.
    
    Args:
        event: Event data passed to the function
        context: Runtime information provided by AWS Lambda
        
    Returns:
        dict: Response with statusCode and body
    """
    print("Hello World from Lambda!")
    
    return {
        'statusCode': 200,
        'body': 'Hello World!'
    }

