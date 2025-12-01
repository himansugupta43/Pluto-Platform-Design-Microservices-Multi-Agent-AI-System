# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching
# This step is only re-run if requirements.txt changes, saving a lot of time
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container
# This includes your 'app' folder, 'src' folder (with the AI model), and main.py
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# The command to run the Uvicorn server
# We use 0.0.0.0 to make it accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]