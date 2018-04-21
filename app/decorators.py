__author__ = 'GrMartin'
import threading

def timedLoopCall(interval):
    def decorator(function):
        def wrapper(*args, **kwargs):
            stopped = threading.Event()

            def loop(): # executed in another thread
                function(*args, **kwargs)
                while not stopped.wait(interval): # until stopped; interval in seconds
                    threading.Thread(target=function, args=args, kwargs=kwargs).start()

            t = threading.Thread(target=loop)
            t.daemon = True # stop if the program exits
            t.start()
            return stopped
        return wrapper
    return decorator