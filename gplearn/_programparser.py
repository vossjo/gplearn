"""Genetic Programming in Python, with a scikit-learn inspired API

The :mod:`gplearn._programparser` module implements symbolic simplification
of programs via sympy and optimization of numerical parameters via scipy.
"""

# Author: Johannes Voss <https://stanford.edu/~vossj/main/>
#
# Additions to and based on gplearn by Trevor Stephens <trevorstephens.com>
#
# License: BSD 3 clause

from .functions import _Function, _protected_division

import numpy as np
from scipy import optimize
from sympy import symbols, simplify
import ast

def parseexpr(x, fun_list, params):
    """Recursively parse program as mathematical expression.

    Parameters
    ----------
    x : ast body
        (sub) expression
    fun_list: list
        mapping to gplearn function objects.
    params: list
        list of numerically optimized parameters
        will be empty after parser has completed

    Returns
    -------
    parsed (sub) expression as flattened tree list
    """

    if isinstance(x, ast.BinOp):
        l = parseexpr(x.left, fun_list, params)
        r = parseexpr(x.right, fun_list, params)
        if isinstance(x.op, ast.Add):
            return [fun_list[0]]+l+r
        elif isinstance(x.op, ast.Sub):
            return [fun_list[1]]+l+r
        elif isinstance(x.op, ast.Mult):
            return [fun_list[2]]+l+r
        elif isinstance(x.op, ast.Div):
            return [fun_list[3]]+l+r
        elif isinstance(x.op, ast.Pow):
            # expand powers to products where possible
            if len(r)==1 and (type(r[0])==int or abs(round(r[0])-r[0])<1e-11) and r[0]>0 and fun_list[2] is not None:
                return (([fun_list[2]]+l)*(int(r[0])-1)) + l
            elif fun_list[4] is not None:
                return [fun_list[4]]+l+r
            else:
                raise RuntimeError('simplification introduced power operator with exponent that is not a positive integer, which is not included in function list.'+str(r))
        else:
            raise RuntimeError('unimplemented operation '+str(x.op))
    else:
        if isinstance(x, ast.Name):
            return [int(x.id[1:])]
        elif isinstance(x, ast.Num):
            if type(x.n)==int:
                # integers must be converted to floats here,
                # otherwise gplearn will interpret the integer
                # as a feature index when executing the program
                return [float(x.n)]
            elif len(params)==0:
                return [float(x.n)]
            else:
                return [params.pop(0)]
        elif isinstance(x, ast.UnaryOp):
            o = parseexpr(x.operand, fun_list, params)
            if isinstance(x.op, ast.USub):
                if fun_list[5] is not None:
                    return [fun_list[5]]+o
                elif fun_list[2] is not None:
                    return [fun_list[2],-1.]+o
                elif fun_list[1] is not None:
                    return [fun_list[1],0.]+o
                else:
                    raise RuntimeError('simplifcation introduced negation operator, but function list is not including any of neg, mul, or sub to represent the negation.')
            else:
                raise RuntimeError('unimplemented operation '+str(x.op))
        else:
            raise RuntimeError('unimplemented object '+str(x))

def parseexpr_to_np(x, params):
    """Recursively parse program as mathematical expression.

    Parameters
    ----------
    x : ast body
        (sub) expression
    params: list
        Initially empty list to which numerical parameters found
        are appended

    Returns
    -------
    parsed (sub) expression as flattened tree list
    """

    if isinstance(x, ast.BinOp):
        l = parseexpr_to_np(x.left, params)
        r = parseexpr_to_np(x.right, params)
        if isinstance(x.op, ast.Add):
            return 'np.add('+l+','+r+')'
        elif isinstance(x.op, ast.Sub):
            return 'np.subtract('+l+','+r+')'
        elif isinstance(x.op, ast.Mult):
            return 'np.multiply('+l+','+r+')'
        elif isinstance(x.op, ast.Div):
            return '_protected_division('+l+','+r+')'
        elif isinstance(x.op, ast.Pow):
            return 'np.power('+l+','+r+')'
        else:
            raise RuntimeError('unimplemented operation '+str(x.op))
    else:
        if isinstance(x, ast.Name):
            return 'X[:,k+'+x.id[1:]+']'
        elif isinstance(x, ast.Num):
            # don't treat integers as numerical parameters to be optimized
            if type(x.n)==int or abs(round(float(x.n))-int(x.n))<1e-11:
                return str(x.n)
            else:
                params.append(float(x.n))
                return 'z[%d]' % (len(params)-1)
        elif isinstance(x, ast.UnaryOp):
            o = parseexpr_to_np(x.operand, params)
            if isinstance(x.op, ast.USub):
                return '(-('+o+'))'
            else:
                raise RuntimeError('unimplemented operation '+str(x.op))
        else:
            raise RuntimeError('unimplemented object '+str(x))

def add(x,y):
    return x+y

def sub(x,y):
    return x-y

def mul(x,y):
    return x*y

def dv(x,y):
    return x/y

def pw(x,y):
    return x**y

def neg(x):
    return -x

def program_to_str(program, format='%.15e', skip_nmax_feature=True):
    """Convert program in list representation to string.
       Based on __str__ method in _program.py."""
    terminals = [0]
    output = ''
    maxfeature = 0
    for i, node in enumerate(program):
        if isinstance(node, _Function):
            terminals.append(node.arity)
            output += node.name + '('
        else:
            if isinstance(node, int):
                output += 'X%s' % node
                maxfeature = max(maxfeature,node)
            else:
                output += format % node
            terminals[-1] -= 1
            while terminals[-1] == 0:
                terminals.pop()
                terminals[-1] -= 1
                output += ')'
            if i != len(program) - 1:
                output += ', '
    if skip_nmax_feature:
        return output
    else:
        return output, maxfeature


def program_to_math(program, feature_names=None, format='%.8g'):
    """Convert program as math expression with standard operators +, -, *, /

    Parameters
    ----------
    program : list
        The program to be optimized.

    n_features : int
        Number of features

    feature_names : list, optional
        Variable names of features

    format : str, optional
        format str for numerical values

    Returns
    -------
    str with mathematical expression
    """

    # convert program to string of mathematical expression
    s, maxf = program_to_str(program, format=format, skip_nmax_feature=False)
    # substitute reserved names for division and power
    s = s.replace('div', 'dv').replace('pow', 'pw')

    # generate symbol names for features for use with sympy
    gpvars0 = ''
    gpvars1 = ''
    for i in range(maxf):
        gpvars0 += 'X%d,' % i
        gpvars1 += 'X%d ' % i
    gpvars0 += 'X%d' % maxf
    gpvars1 += 'X%d' % maxf
    exec(gpvars0 + '=symbols("' + gpvars1 +'")')

    u = str(eval(s))

    # use optional feature variable names
    if feature_names is not None:
        for i in range(len(feature_names)-1,-1,-1):
            u = u.replace('X%d' % i, feature_names[i])

    return u


def _optimizer(program, fun_list, force_coeff, n_features, n_program_sum,
    metric, X, y, weight):
    """Simplify a program and then optimize its numerical parameters.

    Parameters
    ----------
    program : list
        The program to be optimized.

    fun_list : list of length 6
        List mapping the operations in order add, sub, mul, div, pow, neg
        to the corresponding gplearn function objects.

    force_coeff : bool
        If true, insert factors of 1 before numerical optimization for
        whole program and all summands, minuends and subtrahends

    n_features : int
        number of features

    n_program_sum : int
        number of programs to be summed up for cost function

    metric : instance of gplearn metric
        metric to be optimized

    X : array-like, shape = [n_samples, n_features*(n_program_sum+1)]
        Training vectors, where n_samples is the number of samples and
        n_features is the number of features.

    y : array-like, shape = [n_samples]
        Target values.

    weight : array-like, shape = [n_samples]
        Weights applied to individual samples.

    Returns
    -------
    Simplified and numerically optimized program

    """

    # generate symbol names for features for use with sympy
    gpvars0 = ''
    gpvars1 = ''
    for i in range(n_features-1):
        gpvars0 += 'X%d,' % i
        gpvars1 += 'X%d ' % i
    gpvars0 += 'X%d' % (n_features-1)
    gpvars1 += 'X%d' % (n_features-1)
    exec(gpvars0 + '=symbols("' + gpvars1 +'")')

    # convert program to string of mathematical expression
    # substitute reserved names for division and power
    s = program_to_str(program, format='%.12g').replace('div', 'dv').replace('pow', 'pw')
    # symplify
    u = str(simplify(eval(s)))

    #Add factors of one before numerical optization if requested
    if force_coeff:
        u = '1.0*('+u.replace(' - ', '*1.0-1.0*').replace(' + ', '*1.0+1.0*')+')'

    # If simplification detects division by zero (which _protected_divide would catch)
    # or other overflows, it will introduce variable oo (or complex zoo or nan).
    # program is likely not particularly good: simply replace zoo, oo, and nan with 1
    # here, then optimize as much as possible
    uast = ast.parse(u.replace('zoo','1.').replace('oo','1.').replace('nan','1.'),
        mode='eval').body

    # convert back to numpy expression
    params = []
    num = parseexpr_to_np(uast, params)

    if len(params)>0:
        # define cost function to be minimized with scipy
        if hasattr(metric.function, '_obj'):
            metr = metric.function._obj
        else:
            metr = metric.function
        sign = -metric.sign
        if weight is None:
            weights = np.ones_like(y)
        else:
            weights = weight
        local = {'X': X, 'y': y, 'w': weights, 'sign': sign,
            'metr': metr, 'n': n_program_sum, 'nf': n_features+1, 'np': np,
            '_protected_division': _protected_division}
        if n_program_sum>1:
            funstr = """def fun(z):
                y_pred = np.zeros_like(y)
                for k in range(1,n*nf+1,nf):
                    y_pred += X[:,k-1] * (%s)
                return sign*metr(y, y_pred, w)
                """ % num
        else:
            funstr = """def fun(z):
                k = 0
                return sign*metr(y, %s, w)
                """ % num

        exec(funstr, local)

        #optimize numerical parameters params
        newparams = optimize.fmin(local['fun'], params, disp=0, xtol=1e-8, ftol=1e-8)

        numpar = list(newparams)
    else:
        numpar = []

    #if simplification failed due to e.g. introduction of
    #new operators not included in the original function list that
    #cannot be resolved, return original program
    try:
        pro = parseexpr(uast, fun_list, numpar)
        #if factors of one were inserted, symbolically simplify once more
        if force_coeff:
            s = program_to_str(pro, format='%.12g').replace('div', 'dv').replace('pow', 'pw')
            # symplify
            u = str(simplify(eval(s)))
            uast = ast.parse(u, mode='eval').body
            pro = parseexpr(uast, fun_list, [])
    except RuntimeError:
        pro = program

    return pro


def _convert_function(fun, fun_set, n_features):
    """Convert mathematical expression to program in flattened tree list

    Parameters
    ----------
    fun : str
        The mathematical expression to be converted to a program.
        Variable for features must be X0, X1, X2, ...

    fun_set : gp function set

    n_features : int
        number of features

    Returns
    -------
    Program as list

    """

    fun_list = [None]*6
    parser_implemented = ('add','sub','mul','div','pow','neg')
    for func in fun_set:
        if func.name in parser_implemented:
            fun_list[parser_implemented.index(func.name)] = func
        else:
            raise ValueError('function %s not implemented in optimization parser.'
                             % func.name)

    # generate symbol names for features for use with sympy
    gpvars0 = ''
    gpvars1 = ''
    for i in range(n_features-1):
        gpvars0 += 'X%d,' % i
        gpvars1 += 'X%d ' % i
    gpvars0 += 'X%d' % (n_features-1)
    gpvars1 += 'X%d' % (n_features-1)
    exec(gpvars0 + '=symbols("' + gpvars1 +'")')

    # replace overflows, if any and convert to ast for further parsing
    funast = ast.parse(fun, mode='eval').body

    return parseexpr(funast, fun_list, [])
