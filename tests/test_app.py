import pytest
import app
from app import database
from app.worker import Worker


@pytest.fixture
def client():
    """Fixture of slack app for client"""
    api_app = app.create_app()
    api_app.config['TESTING'] = True
    database.init_database(api_app)
    yield api_app.test_client()


@pytest.fixture
def task_factory():
    def create_task(title="Task title", description="Task description",
                    command="echo hello world", image="ubuntu",
                    status=database.Task.Status.pending.value, logs=None):
        task = database.Task.create(
            title=title,
            description=description,
            command=command,
            image=image,
            status=status,
            logs=logs,
        )
        return task
    return create_task


def test_list_tasks(client):
    """Test listing task."""
    response = client.get('/tasks')
    assert response.status_code == 200
    assert response.json == {'data': []}


def test_create_tak(client):
    """Test creating a task."""
    req = {
        "data": {
            "attributes": {
                "title": "hello wold ubuntu",
                "description": "Run hello world in ubuntu",
                "command": "echo hello world",
                "image": "ubuntu"
            }
        }
    }

    response = client.post('/tasks', json=req)
    assert response.status_code == 201


def test_get_task(client, task_factory):
    """Test retrieving a task by ID."""
    task = task_factory()
    response = client.get(f'/tasks/{task.id}')
    assert response.status_code == 200


def test_get_task_not_found(client):
    """Test retrieving a task by non-existent ID."""
    response = client.get('/tasks/999')
    assert response.status_code == 404
    assert response.json == {'error': 'task with id 999 not found'}


def test_update_task_missing_data(client, task_factory):
    """Test updating a task with missing data."""
    task = task_factory()
    req = {}
    response = client.patch(f'/tasks/{task.id}', json=req)
    assert response.status_code == 400
    assert response.json == {'error': 'data is required'}


def test_update_task_missing_attributes(client, task_factory):
    """Test updating a task with missing attributes."""
    task = task_factory()
    req = {
        "data": {}
    }
    response = client.patch(f'/tasks/{task.id}', json=req)
    assert response.status_code == 400
    assert response.json == {'error': 'data.attributes is required'}


def test_delete_task(client, task_factory):
    """Test deleting a task."""
    task = task_factory()
    response = client.delete(f'/tasks/{task.id}')
    assert response.status_code == 204
    with pytest.raises(database.Task.DoesNotExist):
        database.Task.get(database.Task.id == task.id)


def test_delete_task_running(client, task_factory):
    """Test deleting a running task."""
    task = task_factory(status=database.Task.Status.running)
    response = client.delete(f'/tasks/{task.id}')
    assert response.status_code == 400
    assert response.json == {'error': 'running tasks could not be deleted'}


def test_get_task_logs(client, task_factory):
    """Test retrieving task logs."""
    task = task_factory(logs='Test logs')
    response = client.get(f'/tasks/{task.id}/logs/')
    assert response.status_code == 200
    assert response.json == {'data': 'Test logs'}


def test_get_task_logs_not_found(client, task_factory):
    """Test retrieving logs for a task with no logs."""
    task = task_factory(logs=None)
    response = client.get(f'/tasks/{task.id}/logs/')
    assert response.status_code == 404
    assert response.json == {'error': f'task with id {task.id} has no logs'}


@pytest.fixture
def worker():
    return Worker(num_of_workers=1, max_concurrent_tasks=2)
