"""
Lightweight benchmarking utilities: a timing decorator plus a
cProfile-based profiler for identifying pipeline bottlenecks.
"""
import time
import cProfile
import pstats
import io
import functools
import logger_setup

log = logger_setup.get_logger(__name__)


def timed(func):
    """Decorator that logs execution time of any function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        log.info(f"[BENCHMARK] {func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper


def profile(func, *args, top_n: int = 15, **kwargs):
    """Run a function under cProfile and print the top N slowest calls."""
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(top_n)
    log.info("Profiling results:\n" + stream.getvalue())
    return result