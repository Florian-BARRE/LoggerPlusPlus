from __future__ import annotations
import time

from loggerplusplus import loggerplusplus, LoggerClass

# ---- CATCH (decorator + context manager) ---------------------------------
@loggerplusplus.catch(identifier="CATCH_DECOR", level="ERROR", reraise=False)
def boom_decor():
    raise RuntimeError("Boom via decorator")

def boom_context():
    with loggerplusplus.catch(identifier="CATCH_CTX", level="WARNING"):
        raise ValueError("Boom via context manager")

# ---- OPT ------------------------------------------------------------------
def opt_with_identifier():
    loggerplusplus.opt(identifier="OPT_ONE", colors=True).info("Using opt() with identifier")

def opt_with_bound_logger():
    bound = loggerplusplus.bind(identifier="OPT_BOUND")
    loggerplusplus.opt(logger=bound, depth=1).warning("Using opt() with pre-bound logger")

# ---- LOG_TIMING -----------------------------------------------------------
@loggerplusplus.log_timing(identifier="TIMER_ENTER", enter_message="Entering {func}...", exit_message="Done {func} in {duration:.2f}s", show_enter=True)
def slow_a():
    time.sleep(0.2)

@loggerplusplus.log_timing(identifier="TIMER_EXIT", exit_message="Finished {func} in {duration:.3f}s", show_enter=False)
def slow_b():
    time.sleep(0.1)

# ---- LOG_IO ---------------------------------------------------------------
@loggerplusplus.log_io(identifier="IO_BOTH", log_args=True, log_return=True)
def add(a, b):
    return a + b

@loggerplusplus.log_io(identifier="IO_ARGS_ONLY", log_args=True, log_return=False)
def mul(a, b):
    return a * b

@loggerplusplus.log_io(identifier="IO_RET_ONLY", log_args=False, log_return=True)
def sub(a, b):
    return a - b

# ---- CLASS + DECORATORS ---------------------------------------------------
class Service(LoggerClass):
    @loggerplusplus.log_timing(identifier="SERVICE_TIMING", exit_message="Service.run took {duration:.2f}s")
    @loggerplusplus.log_io(identifier="SERVICE_IO", log_args=True, log_return=True)
    @loggerplusplus.catch(identifier="SERVICE_CATCH", level="ERROR", reraise=False)
    def run(self, x: int, y: int) -> int:
        if x < 0:
            raise ValueError("x must be >= 0")
        time.sleep(0.05)
        return x + y
