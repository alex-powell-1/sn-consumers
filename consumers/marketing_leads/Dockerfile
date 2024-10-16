FROM python:3
# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1
# Set the working directory in the container.
ENV PYTHONPATH=/app

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt

# Install the dependencies.
RUN apt-get update && apt-get install -y unixodbc unixodbc-dev

WORKDIR /app

# Copy the source code into the container.
COPY . .





CMD [ "python", "consumers/marketing_leads/consumer.py" ]
