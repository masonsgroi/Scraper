# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Copy the Lambda function code to the task root
COPY src/hello.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (lambda_handler function in hello.py)
CMD ["hello.lambda_handler"]
