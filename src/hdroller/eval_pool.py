__docformat__ = 'google'

import hdroller

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from functools import cached_property
import itertools
import math

class EvalPool(ABC):
    """ An abstract, immutable, callable class for evaulating one or more `DicePool`s.
    
    You can pretend that evaluation occurs on individual rolls of the pool as follows:
    
    1. First, specify the `initial_state()`. The state is usually some sort of running total.
    2. Then, you will be given one outcome at a time,
        along with how many dice in each pool rolled that outcome.
        Update the state using `next_state()` using that information.
    
    `final_outcome()`, `reroll()` provide further options.
    
    Instances cache all intermediate state distributions.
    You should therefore reuse instances when possible.
    
    Instances should not be modified after construction
    in any way that affects the return values of these methods.
    Otherwise, values in the cache may be incorrect.
    """
    
    @abstractmethod
    def next_state(self, prev_state, outcome, *counts):
        """ State transition function.
        
        This should produce a state given the previous state, an outcome, and the number of dice in each pool rolling that outcome.
        
        Make sure to handle the base case where `prev_state is None`.
        
        Args:
            prev_state: A hashable object indicating the state before rolling the current outcome.
                If there was no previous state, this will be `None`.
            outcome: The current outcome.
            counts: One `int` for each pool indicating how many dice in that pool rolled the current outcome.
                If there are multiple pools, it's possible that some outcomes will not appear in all pools.
                In this case, the count for the pool(s) that do not have the outcome will be `None`. 
                Zero-weight outcomes count having that outcome (with 0 count).
        
        Returns:
            A hashable object indicating the next state.
        """
    
    def reroll(self, prev_state, outcome, *counts):
        """ Optional function to trigger rerolls.
        
        Given the same arguments as `next_state()`, if this returns `True`,
        the state will immediately be dropped from consideration.
        This effectively performs a reroll of the entire pool.
        
        By default, this is `False`, i.e. all states will be retained.
        """
        return False
    
    def final_outcome(self, final_state, *pools):
        """ Optional function to generate a final outcome from a final state.
        
        By default, the final outcome is equal to the final state.
        
        Args:
            final_state: A state after all outcomes have been processed.
            *pools: One or more `DicePool`s being evaluated.
            
        Returns:
            A final outcome that will be used as part of constructing a die.
            This should be hashable and comparable.
            Alternatively, a return value of `None` will drop the state from consideration,
            effectively performing a full reroll.
        """
        return final_state
    
    def direction(self, *pools):
        """ Optional function to determine the direction in which this evaluator will give outcomes to `next_state()`.
        
        * If > 0, this will be ascending order. This is not compatible with pools with `min_outcomes`.
        * If < 0, this will be descending order. This is not compatible with pools with `max_outcomes`.
        * Otherwise, `next_state()` is assumed to not care about the order in which it sees outcomes.
        
        The default is 0.
        
        Args:
            *pools: One or more `DicePool`s being evaluated.
        """
        return 0
    
    def ndim(self, *pools):
        """ Optional function to specify the number of dimensions of the output die.
        
        The priority to determine ndim is as follows.
        
        1. The `ndim` argument to `eval()`, if not `None`.
        2. This method, if not `None`.
        3. Automatically determined by `die()`.
        
        Args:
            *pools: One or more `DicePool`s being evaluated.
        
        Returns:
            The number of dimensions that the output die should have,
            or `None` if this should be determined automatically by `die()`.
        """
        return None
    
    @cached_property
    def _cache(self):
        return {}
    
    def eval(self, *pools, ndim=None):
        """ Evaluates pools.
        
        You can call the `EvalPool` object directly for the same effect,
        e.g. `sum_pool(pool)` is an alias for `sum_pool.eval(pool)`.
        
        Args:
            *pools: One or more `DicePool`s to evaluate.
                Most evaluators will expect a fixed number of pools.
                The outcomes of the pools must be mutually comparable.
                Pools with `max_outcomes` and pools with `min_outcomes` are not compatible.
            ndim: The number of dimensions of the resulting die.
                If omitted, this will be determined automatically.
        
        Returns:
            A die representing the distribution of the final score.
        """
        has_max_outcomes = any(pool.max_outcomes() is not None for pool in pools)
        has_min_outcomes = any(pool.min_outcomes() is not None for pool in pools)
        if has_max_outcomes and has_min_outcomes:
            raise ValueError('Pools cannot be evaluated if they have both max_outcomes and min_outcomes.')
        
        direction = self.direction(*pools)
        
        if direction > 0:
            if has_min_outcomes:
                raise ValueError('Cannot iterate in ascending order for pools with min_outcomes.')
        elif direction < 0:
            if has_max_outcomes:
                raise ValueError('Cannot iterate in descending order for pools with max_outcomes.')
        else:
            if has_min_outcomes:
                direction = -1
            else:
                direction = 1
        
        dist = self._eval_internal(direction, *pools)
        
        final_dist = defaultdict(int)
        for state, weight in dist.items():
            outcome = self.final_outcome(state, *pools)
            if outcome is not None:
                final_dist[outcome] += weight
        
        if ndim is None:
            ndim = self.ndim(*pools)
        
        return hdroller.Die(final_dist, ndim=ndim)
    
    __call__ = eval
    
    def bind_dice(self, *dice):
        """ Binds one die for each pool.
        
        For example, `sum_d6s = sum_pool.bind_dice(hdroller.d6)` would produce
        a function that takes one argument and sums that many d6s.
        `sum_d6s(3)` would then be the same as `3 @ hdroller.d6`.
        
        Args:
            *dice: One die for each pool taken by this `EvalPool`.
        
        Returns:
            A function that takes in one `num_dice` per pool,
            then runs this `EvalPool` for pools of that size using the bound dice.
        """
        def bound_eval(*num_dices):
            pools = (die.pool(num_dice) for die, num_dice in zip(dice, num_dices))
            return self.eval(*pools)
        
        return bound_eval
    
    def _eval_internal(self, direction, *pools):
        """ Internal algorithm.
        
        All intermediate return values are cached in the instance.
        
        Arguments:
            direction: The direction in which to send outcomes to `next_state()`.
            *pools: One or more `DicePool`s to evaluate.
                Values of `None` indicate that pool has no remaining outcomes to process.
                This *does* change recursively.
            
        Returns:
            A dict `{ state : weight }` describing the probability distribution over states.
        """
        cache_key = (direction, pools)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = defaultdict(int)
        
        if all(pool.num_outcomes() == 0 for pool in pools):
            result[None] = 1
        else:
            outcome, iterators = _pop_pools(direction, pools)
            for p in itertools.product(*iterators):
                prev_pools, counts, weights = zip(*p)
                prod_weight = math.prod(weights)
                prev = self._eval_internal(direction, *prev_pools)
                for prev_state, prev_weight in prev.items():
                    if self.reroll(prev_state, outcome, *counts):
                        continue
                    state = self.next_state(prev_state, outcome, *counts)
                    result[state] += prev_weight * prod_weight
        
        self._cache[cache_key] = result
        return result
    
def _pop_pools(side, pools):
    """ Pops a single outcome from the pools.
    
    Returns:
        * The popped outcome.
        * A tuple of iterators over the possible resulting pools, counts, and weights.
    """
    if side >= 0:
        outcome = max(pool.die().max_outcome() for pool in pools if pool.num_outcomes() > 0)
        iterators = tuple(_pop_pool_max(outcome, pool) for pool in pools)
    else:
        outcome = min(pool.die().min_outcome() for pool in pools if pool.num_outcomes() > 0)
        iterators = tuple(_pop_pool_min(outcome, pool) for pool in pools)
    
    return outcome, iterators

def _pop_pool_max(outcome, pool):
    """ Iterates over possible numbers of dice that could roll an outcome.
    
    Args:
        outcome: The max outcome.
        pool: The `DicePool` under consideration.
    
    Yields:
        prev_pool: The remainder of the pool after taking out the dice that rolled the current outcome.
        count: How many dice rolled the current outcome, or `None` if the outcome is not in this pool.
        weight: The weight of that many dice rolling the current outcome.
    """
    if outcome not in pool.die():
        yield pool, None, 1
    else:
        yield from pool.pop_max()
        
def _pop_pool_min(outcome, pool):
    """ Iterates over possible numbers of dice that could roll an outcome.
    
    Args:
        outcome: The min outcome.
        pool: The `DicePool` under consideration.
    
    Yields:
        prev_pool: The remainder of the pool after taking out the dice that rolled the current outcome.
        count: How many dice rolled the current outcome, or `None` if the outcome is not in this pool.
        weight: The weight of that many dice rolling the current outcome.
    """
    if outcome not in pool.die():
        yield pool, None, 1
    else:
        yield from pool.pop_min()

class SumPool(EvalPool):
    """ A simple `EvalPool` that just sums the dice in a pool. """
    def next_state(self, prev_state, outcome, count):
        """ Add the dice to the running total. """
        if prev_state is None:
            return outcome * count
        else:
            return prev_state + outcome * count

""" A shared `SumPool` object for caching results. """
sum_pool = SumPool()

class FindMatchingSets(EvalPool):
    """ A `EvalPool` that takes the best matching set in a pool.
    
    This prioritizes set size, then the outcome.
    
    The outcomes are `(set_size, outcome)`.
    """
    
    def next_state(self, prev_state, outcome, count):
        """ Replace the last best set if this one is better. 
        
        Note the use of tuple comparison, which priortizes elements to the left.
        """
        if prev_state is None:
            return count, outcome
        else:
            return max(prev_state, (count, outcome))
        
        
