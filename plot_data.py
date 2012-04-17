import numpy as np

import matplotlib.pyplot as plt

columns = test_load()

plt.plot(columns)

# Creates a plot. Json data needs to be transposed.

plt.xlabel('some text')

plt.ylabel('some text')

plt.title('Title')

plt.show()

# Actually displays the figure created by plt.plot
