import numpy as np

import matplotlib.pyplot as plt

def plot_data(columns):
	columns = test_load()
	plt.plot(columns)
	plt.show()

# plt.plot('yourdata') plots your data, plt.show() displays the figure.
# Json data needs to be transposed.
# plt.xlabel('some text') = adds label on x axis
# plt.ylabel('some text') = adds label on y axis
# plt.title('Title') = adds title