SHELL := /bin/bash
include private.env
export $(shell sed 's/=.*//' private.env)


clean:
	rm -rf venv

venv: clean
	python3 -m virtualenv venv
