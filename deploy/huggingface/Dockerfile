# Hugging Face Spaces requires a non-root user with uid 1000.
FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user . .

# Spaces route traffic to app_port; 7860 is the default.
EXPOSE 7860

CMD ["gunicorn", "app:app", "--workers", "2", "--timeout", "120", "--bind", "0.0.0.0:7860"]
