import flask
from peewee import DoesNotExist

from .database import Task


blueprint = flask.Blueprint("tasks", __name__)


@blueprint.route('/tasks', methods=['GET'])
def get_tasks():
    """List all tasks.py."""
    tasks = Task.select()
    return flask.jsonify({
        "data": [task.to_response(flask.request.base_url) for task in tasks]
    })


@blueprint.route('/tasks', methods=['POST'])
def create_task():
    """Create the new docker task"""
    if "data" not in flask.request.json:
        return flask.jsonify({"error": "data is required"}), 400

    if "attributes" not in flask.request.json["data"]:
        return flask.jsonify({"error": "data.attributes is required"}), 400

    if "title" not in flask.request.json["data"]["attributes"]:
        return flask.jsonify({"error": "data.attributes.title is required"}), 400

    task = Task.create(
        title=flask.request.json["data"]["attributes"]["title"],
        command=flask.request.json["data"]["attributes"]["command"],
        image=flask.request.json["data"]["attributes"]["image"],
        description=flask.request.json["data"]["attributes"]["description"],
    )

    return flask.jsonify({"data": task.to_response(flask.request.base_url)}), 201


@blueprint.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """Retrieve the docker task by ID"""

    if Task.count() >= 100:  # Max amount of tasks that can be created
        return flask.jsonify({"error": f"maximum number of tasks reached, skipping task creation"}), 400

    try:
        task = Task.get(Task.id == task_id)
    except DoesNotExist:
        return flask.jsonify({"error": f"task with id {task_id} not found"}), 404
    return flask.jsonify({"data": task.to_response(flask.request.base_url)}), 200


@blueprint.route('/tasks/<task_id>', methods=['PATCH'])
def update_task(task_id):
    """Update the docker task"""
    if "data" not in flask.request.json:
        return flask.jsonify({"error": "data is required"}), 400

    if "attributes" not in flask.request.json["data"]:
        return flask.jsonify({"error": "data.attributes is required"}), 400

    if "description" not in flask.request.json["data"]["attributes"]:
        return flask.jsonify({"error": "data.attributes.description is required"}), 400

    qry = Task.update({Task.description: flask.request.json["data"]["attributes"]["description"]})\
        .where(Task.id == task_id)
    qry.execute()

    return flask.jsonify({"data": Task.get(Task.id == task_id).to_response(flask.request.base_url)}), 200


@blueprint.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete the docker task"""
    task = Task.get(Task.id == task_id)
    if task.status == Task.Status.running.value:
        return flask.jsonify({"error": "running tasks could not be deleted"}), 400

    task.delete_instance()
    return flask.jsonify({"success": "task has been deleted"}), 204


@blueprint.route('/tasks/<task_id>/logs/', methods=['GET'])
def get_task_logs(task_id):
    """Get the logs of the docker task"""
    task = Task.get(Task.id == task_id)
    if task.logs is None:
        return flask.jsonify({"error": f"task with id {task_id} has no logs"}), 404
    return flask.jsonify({"data": task.logs}), 200
