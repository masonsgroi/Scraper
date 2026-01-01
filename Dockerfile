# Use AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements file and install dependencies
COPY requirements-lambda.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir --only-binary=:all: -r ${LAMBDA_TASK_ROOT}/requirements-lambda.txt

# Copy the Lambda function code to the task root
COPY src/scraper.py ${LAMBDA_TASK_ROOT}

# Copy version file
COPY VERSION ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (lambda_handler function in scraper.py)
CMD ["scraper.lambda_handler"]
