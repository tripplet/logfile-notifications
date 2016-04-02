import sched
import time
import threading

def test(value):
    print('test: ' + value)


def loop(scheduler):
    while True:
        scheduler.run()


scheduler = sched.scheduler(time.time, time.sleep)

e1 = scheduler.enter(2, 1, test, ('E1',))
e2 = scheduler.enter(3, 1, test, ('E2',))

# Start a thread to run the events
t = threading.Thread(target=loop, args=(scheduler,))
t.start()

# Back in the main thread, cancel the first scheduled event.
scheduler.cancel(e2)

# Wait for the scheduler to finish running in the thread
t.join()
