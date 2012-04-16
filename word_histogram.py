import string

def process_file(filename):
	h = dict()
	fp = open(filename)
	for line in fp:
		process_line(line, h)
	return h

def process_line(line, h):
	line = line.replace('-', ' ')
	
	for word in line.split():
		word = word.strip(string.punctuation + string.whitespace)
		word = word.lower()

		h[word] = h.get(word, 0) + 1
		
# hist = process_file('filename.txt')
# builds a dictionary where keys are words and values are word frequencies,
# i.e. builds a word histogram. To be used to count keyword frequencies
# on pages crawled by bitcrawl.py
