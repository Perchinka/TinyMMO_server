FROM python:3.11-buster

RUN pip install poetry 

WORKDIR /chat_service

COPY . .

RUN poetry install --no-root \
    && poetry config virtualenvs.create false

ENV PYTHONPATH=${WORKDIR}:${PYTHONPATH}

CMD ["poetry", "run", "python3", "-m", "src.main"]