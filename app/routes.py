from datetime import datetime, date, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Task

main = Blueprint('main', __name__)


@main.route('/')
def index():
    status_filter = request.args.get('status', '')
    priority_filter = request.args.get('priority', '')

    query = Task.query
    if status_filter and status_filter in Task.STATUSES:
        query = query.filter_by(status=status_filter)
    if priority_filter and priority_filter in Task.PRIORITIES:
        query = query.filter_by(priority=priority_filter)

    tasks = query.order_by(Task.created_at.desc()).all()

    # Stats for Chart.js
    status_counts = {s: Task.query.filter_by(status=s).count() for s in Task.STATUSES}
    priority_counts = {p: Task.query.filter_by(priority=p).count() for p in Task.PRIORITIES}

    return render_template(
        'index.html',
        tasks=tasks,
        status_filter=status_filter,
        priority_filter=priority_filter,
        status_counts=status_counts,
        priority_counts=priority_counts,
        statuses=Task.STATUSES,
        priorities=Task.PRIORITIES,
    )


@main.route('/tasks/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        status = request.form.get('status', 'todo')
        due_date_str = request.form.get('due_date', '').strip()

        errors = []

        if not title:
            errors.append('Title is required.')
        elif len(title) > 100:
            errors.append('Title must be 100 characters or fewer.')

        if len(description) > 1000:
            errors.append('Description must be 1000 characters or fewer.')

        if priority not in Task.PRIORITIES:
            errors.append('Invalid priority value.')

        if status not in Task.STATUSES:
            errors.append('Invalid status value.')

        parsed_due_date = None
        if due_date_str:
            try:
                parsed_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid due date format.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'create.html',
                priorities=Task.PRIORITIES,
                statuses=Task.STATUSES,
                form_data=request.form,
            )

        task = Task(
            title=title,
            description=description or None,
            priority=priority,
            status=status,
            due_date=parsed_due_date,
        )
        db.session.add(task)
        db.session.commit()
        flash(f'Task "{task.title}" created successfully.', 'success')
        return redirect(url_for('main.index'))

    return render_template(
        'create.html',
        priorities=Task.PRIORITIES,
        statuses=Task.STATUSES,
        form_data={},
    )


@main.route('/tasks/<int:task_id>')
def view(task_id):
    task = db.get_or_404(Task, task_id)
    return render_template('view.html', task=task)


@main.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
def edit(task_id):
    task = db.get_or_404(Task, task_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', 'medium')
        status = request.form.get('status', 'todo')
        due_date_str = request.form.get('due_date', '').strip()

        errors = []

        if not title:
            errors.append('Title is required.')
        elif len(title) > 100:
            errors.append('Title must be 100 characters or fewer.')

        if len(description) > 1000:
            errors.append('Description must be 1000 characters or fewer.')

        if priority not in Task.PRIORITIES:
            errors.append('Invalid priority value.')

        if status not in Task.STATUSES:
            errors.append('Invalid status value.')

        parsed_due_date = None
        if due_date_str:
            try:
                parsed_due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                errors.append('Invalid due date format.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'edit.html',
                task=task,
                priorities=Task.PRIORITIES,
                statuses=Task.STATUSES,
                form_data=request.form,
            )

        task.title = title
        task.description = description or None
        task.priority = priority
        task.status = status
        task.due_date = parsed_due_date
        task.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash(f'Task "{task.title}" updated successfully.', 'success')
        return redirect(url_for('main.view', task_id=task.id))

    return render_template(
        'edit.html',
        task=task,
        priorities=Task.PRIORITIES,
        statuses=Task.STATUSES,
        form_data={},
    )


@main.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete(task_id):
    task = db.get_or_404(Task, task_id)
    title = task.title
    db.session.delete(task)
    db.session.commit()
    flash(f'Task "{title}" deleted successfully.', 'success')
    return redirect(url_for('main.index'))
