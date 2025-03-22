FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

# Copy source code
COPY . .

# Expose the port that uvicorn will use
EXPOSE 80

# Command to run the app (adjust as needed)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
