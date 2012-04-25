:mod:`bitcrawl` --  BitCoin financial Data Miner
================================================

.. module:: bitcrawl
   :synopsis: Crawl webpages recording a log of extracted numerical values, 
              calculate statistics, and display statistics plus grpahical plots.
.. sectionauthor:: Hobson Lane <hobson@totalgood.com>

.. index::
   single: web
   single: bitcrawl
   single: plot
   single: data miner
   single: data mining

This module provides a functions to extract data from webpages (ASCII text,
usually HTML) and API responses (ususally json, xml, or csv). Other functions
calculate statistics intended for forecasting or dipslay graphs of data
and their statistics.

.. class:: Bot()

   This class provides a urllib interface for retrieving webpages through
   GET and POST actions (while maintaining session information?).

   .. method:: GET(url,retries,delay,len)

      Gets the page at the URL requested (similar to the wget application).
      Return a string containing the contents of the web page (page source).

   .. method:: POST(url,params)

      Reads the response of a `url` to the `params` (POST named parameters).
      Returns a string containing the webpage response to the POST request.

The following examples demonstrate some uses of the bitcrawl module.

   >>> import bitcrawl as bc
   >>> fp = bc.FILEPATH
   >>> data = bc.load_json(filepath = fp, verbose=False)
   >>> rows = bc.retrieve_data( sites  = ['mtgox'  ,'bitcoin'],                                values = ['average','visits' ],                                filepath = fp)
   >>> rows = bc.query_data('mtgox.average date:2012-04-18') # date:2012-04-23')
   >>> print bc.lag_correlate(A=rows, B=rows, lead=-1)
   [[[[1.0...]]]]
   >>> rows = bc.plot_data(columns=bc.transpose_lists(rows),normalize=False)
   A plot titled ... Close it to procede.

.. _linear-algebra:

Linear algebra functions
------------------------------

.. function:: cov(A, B)

   Compute and return the covariance between *A* and *B*. If *A* and *B* are
   multidimensional, e.g. lists of lists then presume the longest dimension
   is the timeseries dimension and calculate the covariance matrix for all 
   `N**2` combinations of *A* and *B*, where `N` `max(len(A),len(B)`.
   
   function:: size(x)
   
   Compute and return the size of *x*, a multidimensional (nested) list.
   Returns a tuple of integers giving the maximum length of the lists
   (or tuples or sets) at each dimension, e.g., 

   >>> import bitcrawl as bc
   >>> bc.size([[0, 1, 2, 3],[4, 5]])
   (2, 4)

   .. _plotting:

Plotting functions
------------------------------


   .. _crawling:

Crawling and Mining functions
------------------------------

