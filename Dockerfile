FROM public.ecr.aws/lambda/python:3.11
COPY runtime_requirements.txt .
RUN pip3 install -r runtime_requirements.txt --target python

