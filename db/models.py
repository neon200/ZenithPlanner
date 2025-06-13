# ZenithPlanner/db/models.py

import sqlalchemy
from sqlalchemy import create_engine, text
from datetime import datetime
from config import DATABASE_URL

class TaskDatabase:
    def __init__(self, db_url=DATABASE_URL):
        # Create a database engine
        self.engine = create_engine(db_url)
        # Create tables if they don't exist
        self.create_tables()

    def _execute_query(self, query, params=None):
        """
        Helper function to execute a query with connection handling.
        This version is robustly designed to handle all types of SQL queries.
        """
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params or {})

            # If a query modifies data (INSERT, UPDATE, DELETE, CREATE, etc.), it needs a commit.
            if any(keyword in query.upper() for keyword in ["INSERT", "UPDATE", "DELETE", "CREATE"]):
                connection.commit()

            # The crucial check: only try to fetch rows if the result object actually contains them.
            # This works for SELECT statements and DML statements with a RETURNING clause.
            # It correctly handles statements like CREATE TABLE which don't return rows, preventing the error.
            if result.returns_rows:
                return result.fetchall()
            else:
                # For statements like CREATE TABLE, or UPDATE/DELETE without a RETURNING clause.
                return None

    def create_tables(self):
        """Creates the 'users' and 'tasks' tables using raw SQL for simplicity."""
        user_table_query = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """
        task_table_query = """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                due_time TIMESTAMPTZ,
                category TEXT DEFAULT 'Others',
                is_completed BOOLEAN DEFAULT FALSE,
                is_recurring BOOLEAN DEFAULT FALSE,
                repeat_pattern TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                user_notes TEXT
            );
        """
        self._execute_query(user_table_query)
        self._execute_query(task_table_query)

    def get_or_create_user(self, email: str, name: str = None) -> dict:
        """Finds a user by email or creates a new one."""
        select_query = "SELECT * FROM users WHERE email = :email"
        users = self._execute_query(select_query, {"email": email})
        
        if users:
            # Convert SQLAlchemy Row to dictionary
            return dict(users[0]._mapping)
        else:
            insert_query = "INSERT INTO users (email, name) VALUES (:email, :name) RETURNING *"
            new_user = self._execute_query(insert_query, {"email": email, "name": name})
            return dict(new_user[0]._mapping)

    def add_task(self, task_data: dict, user_id: int) -> int:
        """Adds a new task for a specific user."""
        query = """
            INSERT INTO tasks (user_id, title, due_time, category, is_recurring, repeat_pattern, user_notes)
            VALUES (:user_id, :title, :due_time, :category, :is_recurring, :repeat_pattern, :user_notes)
            RETURNING id
        """
        # Ensure default values are set for optional fields
        task_data.setdefault('due_time', None)
        task_data.setdefault('category', 'Others')
        task_data.setdefault('is_recurring', False)
        task_data.setdefault('repeat_pattern', None)
        task_data.setdefault('user_notes', None)
        task_data['user_id'] = user_id

        result = self._execute_query(query, task_data)
        # The result is now a list, so result[0] gets the first row, and result[0][0] gets the id
        return result[0][0]

    def get_tasks(self, user_id: int, completed: bool = None):
        """Retrieves tasks for a specific user, converting them to dicts."""
        query = "SELECT * FROM tasks WHERE user_id = :user_id"
        params = {"user_id": user_id}
        if completed is not None:
            query += " AND is_completed = :is_completed"
            params["is_completed"] = completed
        query += " ORDER BY created_at DESC"
        
        rows = self._execute_query(query, params)
        return [dict(row._mapping) for row in rows]

    def get_task_by_id(self, task_id: int, user_id: int):
        """Retrieves a single task, ensuring it belongs to the correct user."""
        query = "SELECT * FROM tasks WHERE id = :task_id AND user_id = :user_id"
        rows = self._execute_query(query, {"task_id": task_id, "user_id": user_id})
        return dict(rows[0]._mapping) if rows else None

    def update_task_status(self, task_id: int, user_id: int, is_completed: bool):
        """Updates a task's status."""
        query = "UPDATE tasks SET is_completed = :is_completed WHERE id = :task_id AND user_id = :user_id"
        self._execute_query(query, {"is_completed": is_completed, "task_id": task_id, "user_id": user_id})

    def reset_recurring_task(self, task_id: int, user_id: int, new_due_time: str):
        """Resets a recurring task."""
        query = "UPDATE tasks SET due_time = :new_due_time, is_completed = false WHERE id = :task_id AND user_id = :user_id"
        self._execute_query(query, {"new_due_time": new_due_time, "task_id": task_id, "user_id": user_id})

    def update_task_due_time(self, task_id: int, user_id: int, new_due_time: str):
        """Updates a task's due time."""
        query = "UPDATE tasks SET due_time = :new_due_time WHERE id = :task_id AND user_id = :user_id"
        self._execute_query(query, {"new_due_time": new_due_time, "task_id": task_id, "user_id": user_id})

    def delete_task(self, task_id: int, user_id: int):
        """Deletes a task."""
        query = "DELETE FROM tasks WHERE id = :task_id AND user_id = :user_id"
        self._execute_query(query, {"task_id": task_id, "user_id": user_id})
