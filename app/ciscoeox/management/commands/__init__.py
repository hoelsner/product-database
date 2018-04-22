from django_project.celery import app as celery


def get_task_state_message(task_id):
    if task_id is None:
        return "Task ID not found, the initial import was not executed or the results are already deleted"

    result = "(Task not found)"

    task = celery.AsyncResult(task_id)
    if task.status != "PENDING":
        result = "State:   %s\nMessage: %s" % (
            task.state,
            task.info.get("status_message", "Status not found")
        )

    return result
