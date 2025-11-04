# Base image resmi Apache Airflow (Python 3.10)
FROM apache/airflow:2.9.1-python3.10

# Jalankan sebagai root dulu untuk install dependency sistem
USER root

# Install Java & dependencies untuk Pyzxing + OpenCV + ZBar
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless \
    libzbar0 \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME agar Pyzxing bisa jalan
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Copy file requirements
COPY requirements.txt /tmp/requirements.txt

# Pindah ke user airflow 
USER airflow

# Install dependencies Python ke dalam environment Airflow
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy semua DAG, script, dsb ke folder Airflow
COPY --chown=airflow:root . /opt/airflow/
