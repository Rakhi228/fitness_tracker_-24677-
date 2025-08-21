 backend_pft.py
import psycopg2
import streamlit as st

class DatabaseManager:
    """
    Manages all database connections and operations.
    """
    def __init__(self, dbname, user, password, host, port):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = None
        self.connect()

    def connect(self):
        """
        Establishes a connection to the PostgreSQL database.
        """
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            st.success("Database connection successful!")
        except psycopg2.OperationalError as e:
            st.error(f"Error: Unable to connect to the database. {e}")
            self.conn = None

    def close(self):
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()

    def _execute_query(self, query, params=None, fetch_results=False):
        """
        Internal method to execute a query.
        """
        if not self.conn:
            st.error("No active database connection.")
            return None if fetch_results else False
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                self.conn.commit()
                if fetch_results:
                    return cur.fetchall()
                return True
        except psycopg2.Error as e:
            st.error(f"Database error: {e}")
            self.conn.rollback()
            return None if fetch_results else False

    # --- CRUD Operations ---

    # --- User Profile CRUD ---
    def create_user(self, name, weight, email):
        query = "INSERT INTO Users (name, weight_kg, email) VALUES (%s, %s, %s) RETURNING user_id;"
        return self._execute_query(query, (name, weight, email), fetch_results=True)

    def read_user(self, user_id):
        query = "SELECT * FROM Users WHERE user_id = %s;"
        return self._execute_query(query, (user_id,), fetch_results=True)

    def update_user(self, user_id, name, weight, email):
        query = "UPDATE Users SET name = %s, weight_kg = %s, email = %s WHERE user_id = %s;"
        return self._execute_query(query, (name, weight, email))

    def delete_user(self, user_id):
        query = "DELETE FROM Users WHERE user_id = %s;"
        return self._execute_query(query, (user_id,))

    # --- Friends CRUD ---
    def add_friend(self, user_id, friend_id):
        query = "INSERT INTO Friends (user_id, friend_id) VALUES (%s, %s);"
        return self._execute_query(query, (user_id, friend_id))

    def get_friends(self, user_id):
        query = """
            SELECT u.user_id, u.name, u.email
            FROM Friends f
            JOIN Users u ON f.friend_id = u.user_id
            WHERE f.user_id = %s;
        """
        return self._execute_query(query, (user_id,), fetch_results=True)

    def remove_friend(self, user_id, friend_id):
        query = "DELETE FROM Friends WHERE user_id = %s AND friend_id = %s;"
        return self._execute_query(query, (user_id, friend_id))

    # --- Workout and Exercise CRUD ---
    def create_workout(self, user_id, workout_date, duration, notes):
        query = "INSERT INTO Workouts (user_id, workout_date, duration_minutes, notes) VALUES (%s, %s, %s, %s) RETURNING workout_id;"
        return self._execute_query(query, (user_id, workout_date, duration, notes), fetch_results=True)

    def create_exercise(self, workout_id, name, sets, reps, weight):
        query = "INSERT INTO Exercises (workout_id, exercise_name, sets, reps, weight_lifted_kg) VALUES (%s, %s, %s, %s, %s);"
        return self._execute_query(query, (workout_id, name, sets, reps, weight))
    
    def read_workouts_with_exercises(self, user_id):
        query = """
            SELECT 
                w.workout_date, w.duration_minutes, w.notes, 
                e.exercise_name, e.sets, e.reps, e.weight_lifted_kg
            FROM Workouts w
            LEFT JOIN Exercises e ON w.workout_id = e.workout_id
            WHERE w.user_id = %s
            ORDER BY w.workout_date DESC;
        """
        return self._execute_query(query, (user_id,), fetch_results=True)

    # --- Goal Setting CRUD ---
    def create_goal(self, user_id, description, target_value, start_date, end_date):
        query = "INSERT INTO Goals (user_id, description, target_value, start_date, end_date) VALUES (%s, %s, %s, %s, %s);"
        return self._execute_query(query, (user_id, description, target_value, start_date, end_date))

    def read_goals(self, user_id):
        query = "SELECT * FROM Goals WHERE user_id = %s ORDER BY end_date ASC;"
        return self._execute_query(query, (user_id,), fetch_results=True)

    def update_goal(self, goal_id, description, target_value, start_date, end_date, is_completed):
        query = """
            UPDATE Goals
            SET description = %s, target_value = %s, start_date = %s, end_date = %s, is_completed = %s
            WHERE goal_id = %s;
        """
        return self._execute_query(query, (description, target_value, start_date, end_date, is_completed, goal_id))

    def delete_goal(self, goal_id):
        query = "DELETE FROM Goals WHERE goal_id = %s;"
        return self._execute_query(query, (goal_id,))
    
    # --- Business Insights Section (using aggregate functions) ---
    def get_weekly_workout_minutes(self, user_id):
        query = """
            SELECT EXTRACT(WEEK FROM workout_date) as week, SUM(duration_minutes) as total_minutes
            FROM Workouts
            WHERE user_id = %s
            GROUP BY week
            ORDER BY week DESC
            LIMIT 1;
        """
        return self._execute_query(query, (user_id,), fetch_results=True)

    def get_average_workout_duration(self, user_id):
        query = """
            SELECT AVG(duration_minutes)
            FROM Workouts
            WHERE user_id = %s;
        """
        return self._execute_query(query, (user_id,), fetch_results=True)
    
    def get_total_workouts(self, user_id):
        query = """
            SELECT COUNT(*)
            FROM Workouts
            WHERE user_id = %s;
        """
        return self._execute_query(query, (user_id,), fetch_results=True)

    def get_max_weight_lifted(self, user_id):
        query = """
            SELECT MAX(weight_lifted_kg), exercise_name
            FROM Exercises e
            JOIN Workouts w ON e.workout_id = w.workout_id
            WHERE w.user_id = %s
            GROUP BY exercise_name
            ORDER BY MAX(weight_lifted_kg) DESC
            LIMIT 1;
        """
        return self._execute_query(query, (user_id,), fetch_results=True)

    def get_friends_leaderboard(self, user_id):
        query = """
            SELECT 
                u.name, 
                SUM(w.duration_minutes) AS total_minutes
            FROM Workouts w
            JOIN Users u ON w.user_id = u.user_id
            WHERE w.user_id IN (
                SELECT friend_id FROM Friends WHERE user_id = %s
            )
            AND w.workout_date >= date_trunc('week', current_date)
            GROUP BY u.name
            ORDER BY total_minutes DESC;
        """
        return self._execute_query(query, (user_id,), fetch_results=True)
