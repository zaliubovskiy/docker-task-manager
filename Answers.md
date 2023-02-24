Extra Questions (If you have a time)

1. If we need to limit task in compute resources: e.g. CPU / Memory, how would you do it?

I would use container runtime flags in order to do that. For example, adjust the function _run_task() like so:

def _run_task(task):
    command = ["docker", "run", "--rm", "--cpus", "1", "--memory", "6m", task.image, task.command]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # In this way, I limited the CPU to 1 only, and memory to 6 MB.
    ...


2. How to limit task execution time?

I would pass a timeout argument to my function to set a maximum amount of time.

def _run_task(task):
    ...
    timeout_value = 30 #  in seconds
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_value)
    except subprocess.TimeoutExpired:
        task.logs = f"Task timed out after {timeout_value} seconds"
    ...

3. How would you approach task cancellation?

I would add a new endpoint and a new status to the Task.Status enum.

@blueprint.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    if task.status == Task.Status.running.value:
        container = worker.client.containers.get(task.container_id)
        container.stop()
        task.status = Task.Status.cancelled.value
        task.save()
        return flask.jsonify({"success": "task has been cancelled"}), 200
    elif task.status == Task.Status.cancelled.value:
        return flask.jsonify({"error": "task is already cancelled"}), 400
    else:
        return flask.jsonify({"error": "only running tasks can be cancelled"}), 400


4. How would you add authorization to the API? What authz type would you pick and why?

I would need to add new endpoints (register, login, etc.). In order to protect the url from security breaches. 
On all of the other urls, add middleware to check if the token isn't expired. 

I would use token-based authorization, specifically JWT. 
Because it's a good and secure approach, and I have worked with it earlier, I liked it a lot.

5. What kind of test levels do you think this system needs and why?

At this stage of the project, it is hard to determine waht types of testing I would pick, since it is a Test project.
There is no authorization and authentication, so "Security" is not valid. "Performance" could be an option, but we limited
the load on CPU and Memory earlier. I would probably stick to traditional "Integration" + "Unit" tandem. 

6. When you'll be ready to ship this code to production, how would you deploy it?

I could say that containerize app using Docker, build an image and store in on AWS, then set-up environment variables, and setup CI/CD.
But that's just general image of this process, I have no experience with it. 

