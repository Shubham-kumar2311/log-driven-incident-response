from queues import processed_event_queue


def publish(event):

    processed_event_queue.put(event)