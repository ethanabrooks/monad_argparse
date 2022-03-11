mypy:
	mypy --show-error-codes --exclude=readme.py dollar_lambda

test:
	python -m unittest test.py

readme: readme.py
	rm -rf readme.rst
	jupytext --sync readme.py
	DOLLAR_LAMBDA_TESTING=1 jupyter nbconvert --to markdown --execute readme.ipynb

docs: dollar_lambda/
	rm -rf docs/
	pdoc3 --html dollar_lambda --force
	mv html/dollar_lambda docs/
	rm -rf html

.PHONY: docs
