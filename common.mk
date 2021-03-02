SHELL := /bin/bash


clean:
	rm -rf venv

venv: clean
	python3 -m virtualenv venv

pip_install:
	source venv/bin/activate && \
	pip3 install -r requirements.txt && \
	deactivate