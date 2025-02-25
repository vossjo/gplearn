Changes in this fork of Trevor Stephens' gplearn
================================================

.. role:: python(code)
   :language: python

.. role:: raw-html(raw)
    :format: html

This fork extends the original code by three methods:

* There is an option to provide initial guesses for programs in the form of equations with variable names :python:`X0`, :python:`X1`, ... for features (e.g. :python:`'1.5*X0 + 10*X1/X2'`) as a list of strings specified for the optional parameter :python:`previous_programs` of the modified :python:`SymbolicRegressor`.

* Setting the new optional parameter :python:`optimize` to :python:`True` for :python:`SymbolicRegressor` will trigger symbolic program simplification via `sympy <https://www.sympy.org>`_ and optimization of numerical program parameters via `scipy <https://www.scipy.org>`_.

* Setting the new optional parameter :python:`n_program_sum` of :python:`SymbolicRegressor` to integers larger than 1 will trigger interpretation of the first column of the observation input as a weight :python:`w0` and the following :python:`n_features` columns as program feature input, the next column as weight :python:`w1`, etc., such that a program P is evaluated as a sum from :python:`i=1` to :python:`n_program_sum` over :python:`w_i * P(features_i)`.

Additional extensions:

* Optional parameter :python:`penalties` is a dictionary with function-specific weights as program penalties, e.g. :python:`{'add':2.0, 'var':1.0, 'coeff':1.5}` including penalties for variables 'var' and numerical coefficients 'coeff'.

* Optional parameter :python:`force_coeff` inserts factors of one before numerical optimization, so that e.g. sums of features with different physical units with summands without numerical pre-factors can be avoided.

* Use :python:`gplearn._programparser.program_to_math` to convert :python:`list` representation of program to mathematical expression with standard math operators :python:`*`, :python:`/`, :python:`+`, :python:`-`, etc. instead of :python:`mul(...)`, ... etc., e.g. :python:`mathstring=program_to_math(est_gp._program.program)`.

* Implementation of modified `AIC <https://en.wikipedia.org/wiki/Akaike_information_criterion>`_ metric :python:`aic0`. Use together with :python:`parsimony_coefficient=2.0` to properly penalize operators, variables, and numerical coefficients as degrees of freedom.

:raw-html:`<br />`

Original `README` below:

.. image:: https://img.shields.io/pypi/v/gplearn.svg
    :target: https://pypi.python.org/pypi/gplearn/
    :alt: Version
.. image:: https://img.shields.io/pypi/l/gplearn.svg
    :target: https://github.com/trevorstephens/gplearn/blob/master/LICENSE
    :alt: License
.. image:: https://readthedocs.org/projects/gplearn/badge/?version=stable
    :target: http://gplearn.readthedocs.io/
    :alt: Documentation Status
.. image:: https://travis-ci.org/trevorstephens/gplearn.svg?branch=master
    :target: https://travis-ci.org/trevorstephens/gplearn
    :alt: Test Status
.. image:: https://ci.appveyor.com/api/projects/status/wqq9xxaxuyyt7nya?svg=true
    :target: https://ci.appveyor.com/project/trevorstephens/gplearn
    :alt: Windows Test Status
.. image:: https://coveralls.io/repos/trevorstephens/gplearn/badge.svg
    :target: https://coveralls.io/r/trevorstephens/gplearn
    :alt: Test Coverage
.. image:: https://api.codacy.com/project/badge/Grade/19c43d7c42c44d15b1ec512656800d8d
    :target: https://www.codacy.com/app/trevorstephens/gplearn
    :alt: Code Health

|

.. image:: https://raw.githubusercontent.com/trevorstephens/gplearn/master/doc/logos/gplearn-wide.png
    :target: https://github.com/trevorstephens/gplearn
    :alt: Genetic Programming in Python, with a scikit-learn inspired API

|

Welcome to gplearn!
===================

`gplearn` implements Genetic Programming in Python, with a `scikit-learn <http://scikit-learn.org>`_ inspired and compatible API.

While Genetic Programming (GP) can be used to perform a `very wide variety of tasks <http://www.genetic-programming.org/combined.php>`_, gplearn is purposefully constrained to solving symbolic regression problems. This is motivated by the scikit-learn ethos, of having powerful estimators that are straight-forward to implement.

Symbolic regression is a machine learning technique that aims to identify an underlying mathematical expression that best describes a relationship. It begins by building a population of naive random formulas to represent a relationship between known independent variables and their dependent variable targets in order to predict new data. Each successive generation of programs is then evolved from the one that came before it by selecting the fittest individuals from the population to undergo genetic operations.

gplearn retains the familiar scikit-learn `fit/predict` API and works with the existing scikit-learn `pipeline <https://scikit-learn.org/stable/modules/compose.html>`_ and `grid search <http://scikit-learn.org/stable/modules/grid_search.html>`_ modules. The package attempts to squeeze a lot of functionality into a scikit-learn-style API. While there are a lot of parameters to tweak, `reading the documentation <http://gplearn.readthedocs.io/>`_ should make the more relevant ones clear for your problem.

gplearn supports regression through the SymbolicRegressor, binary classification with the SymbolicClassifier, as well as transformation for automated feature engineering with the SymbolicTransformer, which is designed to support regression problems, but should also work for binary classification.

gplearn is built on scikit-learn and a fairly recent copy (0.22.1+) is required for `installation <http://gplearn.readthedocs.io/en/stable/installation.html>`_. If you come across any issues in running or installing the package, `please submit a bug report <https://github.com/trevorstephens/gplearn/issues>`_.

