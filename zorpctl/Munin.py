from Instances import ZorpHandler

def sumThreads():
    results = ZorpHandler.status()
    running_thread_sum = 0
    for result in results:
        if result:
            running_thread_sum += result.threads
    return running_thread_sum

print sumThreads()
