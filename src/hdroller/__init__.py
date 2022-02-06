""" Package for computing dice probabilities. """

__docformat__ = 'google'

# Expose certain names at top-level.

from hdroller.dice.func import Die, standard, d, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, mix, ternary, align, align_range, apply

import hdroller.dice.base

from hdroller.dice.base import BaseDie
from hdroller.dice.zero import ZeroDie
from hdroller.dice.single import SingleDie
from hdroller.dice.multi import MultiDie

min = hdroller.dice.base.BaseDie.min
max = hdroller.dice.base.BaseDie.max
min_outcome = hdroller.dice.base.BaseDie.min_outcome
max_outcome = hdroller.dice.base.BaseDie.max_outcome

from hdroller.pool import Pool, DicePool
from hdroller.eval_pool import EvalPool, SumPool, sum_pool, FindMatchingSets

__all__ = ['Die', 'standard', 'd', '__getattr__', 'bernoulli', 'coin',
    'BaseDie', 'ZeroDie', 'SingleDie', 'MultiDie',
    'from_cweights', 'from_sweights', 'from_rv', 'mix', 'ternary', 'align', 'align_range',
    'min', 'max', 'min_outcome', 'max_outcome',
    'apply',
    'Pool', 'DicePool', 'EvalPool', 'SumPool', 'sum_pool', 'FindMatchingSets',
    'd2', 'd3', 'd4', 'd6', 'd8', 'd10', 'd12', 'd20', 'd100']
