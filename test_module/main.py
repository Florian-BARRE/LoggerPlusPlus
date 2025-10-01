import threading
import multiprocessing

from loggerplusplus import loggerplusplus
from test_module.config import configure_logging
from test_module.worker import Worker, external_function
from test_module import decorators as D

configure_logging()

@loggerplusplus.catch()
def decorated_task():
    loggerplusplus.bind(identifier="DECORATED").debug("Inside decorated function")

def thread_target():
    loggerplusplus.bind(identifier="THREAD").info("Hello from thread")

def process_target():
    # Must reconfigure logger in subprocess to have sinks!
    from test_module.config import configure_logging
    configure_logging()
    loggerplusplus.bind(identifier="PROCESS").info("Hello from process")

if __name__ == "__main__":
    loggerplusplus.bind(identifier="MAIN").info("Main starting...")

    # Class usage
    w = Worker()
    w.do_work()

    # External function
    external_function()

    # Thread test
    t = threading.Thread(target=thread_target, daemon=True)
    t.start()
    t.join()

    # Process test
    p = multiprocessing.Process(target=process_target)
    p.start()
    p.join()

    # Decorated function
    # CATCH
    D.boom_decor()
    try:
        D.boom_context()
    except Exception:
        # boom_context uses context manager; here we let it bubble to show contrast
        pass

    # OPT
    D.opt_with_identifier()
    D.opt_with_bound_logger()

    # TIMING
    D.slow_a()
    D.slow_b()

    # IO
    D.add(3, 5)
    D.mul(4, 7)
    D.sub(10, 8)

    # CLASS + DECORATORS
    svc = D.Service()
    svc.run(2, 3)
    svc.run(-1, 3)  # triggers catch

    loggerplusplus.bind(identifier="MAIN").info("Main completed.")
