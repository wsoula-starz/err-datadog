clean:
	rm -rf __pycache__
	rm -rf .cache
	rm -rf .tox

test:
	tox
