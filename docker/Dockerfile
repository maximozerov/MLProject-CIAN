FROM python

RUN apt-get update
RUN apt-get install -y --fix-missing git python3

ADD README.md /README.md

ADD requirements.txt /requirements.txt

RUN pip install -r requirements.txt

ADD main.py /main.py
CMD ["uvicorn", "--host", "0.0.0.0", "main:app", "--port", "8898"]
