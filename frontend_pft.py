# frontend_pft.py
import streamlit as st
import datetime
from backend_pft import DatabaseManager

# Database connection details
DB_DETAILS = {
    "dbname": "personal fitness tracker",
    "user": "postgres",
    "password": "Rakhi@224",
    "host": "localhost",
    "port": "5432"
}

# Initialize database manager
db = DatabaseManager(**DB_DETAILS)

st.title("💪 Personal Fitness Tracker")

# Hardcoded user for this single-user application
USER_ID = 1

# --- User Management (Simulated for a single user) ---
def setup_user_profile():
    st.header("👤 Your Profile")
    if st.button("Create Sample User Profile"):
        db.create_user("John Doe", 80.5, "john.doe@example.com")
        st.success("Sample user created! You can now use the application.")

# --- Frontend Sections ---

def user_profile_section():
    st.header("👤 User Profile")
    if st.session_state.get('user_data'):
        user = st.session_state['user_data'][0]
        st.write(f"**Name:** {user[1]}")
        st.write(f"**Weight:** {user[2]} kg")
        st.write(f"**Email:** {user[3]}")

        # Update Profile
        st.subheader("Update Your Profile")
        with st.form("update_profile_form"):
            new_name = st.text_input("Name", value=user[1])
            new_weight = st.number_input("Weight (kg)", value=user[2], format="%.2f")
            new_email = st.text_input("Email", value=user[3])
            submit_button = st.form_submit_button("Update Profile")
            if submit_button:
                db.update_user(USER_ID, new_name, new_weight, new_email)
                st.session_state['user_data'] = db.read_user(USER_ID)
                st.success("Profile updated successfully!")

def workout_tracking_section():
    st.header("🏋️ Workout and Progress Tracking")

    # CREATE: Log New Workout
    st.subheader("Log a New Workout")
    with st.form("new_workout_form"):
        date = st.date_input("Date", datetime.date.today())
        duration = st.number_input("Duration (minutes)", min_value=1)
        notes = st.text_area("Notes")

        st.subheader("Add Exercises")
        exercises = []
        num_exercises = st.number_input("Number of Exercises", min_value=1, value=1)
        for i in range(num_exercises):
            st.markdown(f"**Exercise {i+1}**")
            ex_name = st.text_input(f"Exercise Name {i+1}")
            sets = st.number_input(f"Sets {i+1}", min_value=1, value=3)
            reps = st.number_input(f"Reps {i+1}", min_value=1, value=10)
            weight = st.number_input(f"Weight Lifted (kg) {i+1}", min_value=0.0, value=0.0)
            exercises.append({'name': ex_name, 'sets': sets, 'reps': reps, 'weight': weight})
        
        submit_button = st.form_submit_button("Log Workout")
        if submit_button:
            workout_id_tuple = db.create_workout(USER_ID, date, duration, notes)
            if workout_id_tuple and workout_id_tuple[0]:
                workout_id = workout_id_tuple[0][0]
                for ex in exercises:
                    if ex['name']:
                        db.create_exercise(workout_id, ex['name'], ex['sets'], ex['reps'], ex['weight'])
                st.success("Workout and exercises logged successfully!")
            else:
                st.error("Failed to log workout.")

    # READ: View Workout History
    st.subheader("Workout History")
    workout_history = db.read_workouts_with_exercises(USER_ID)
    if workout_history:
        # Group exercises by workout
        workouts = {}
        for row in workout_history:
            date_str = row[0].strftime("%Y-%m-%d")
            if date_str not in workouts:
                workouts[date_str] = {
                    'duration': row[1],
                    'notes': row[2],
                    'exercises': []
                }
            if row[3]: # Check if exercise data exists
                workouts[date_str]['exercises'].append({
                    'name': row[3], 'sets': row[4], 'reps': row[5], 'weight': row[6]
                })

        for date, data in workouts.items():
            with st.expander(f"**Workout on {date}** - {data['duration']} minutes"):
                st.write(f"**Notes:** {data['notes']}")
                st.write("---")
                for ex in data['exercises']:
                    st.markdown(f"**{ex['name']}**")
                    st.write(f"Sets: {ex['sets']}, Reps: {ex['reps']}, Weight: {ex['weight']} kg")
    else:
        st.info("No workouts logged yet.")

def social_connections_section():
    st.header("👫 Social Connections")
    all_users = db.read_user(None) # Get all users to find friends
    if all_users:
        all_users = [user for user in all_users if user[0] != USER_ID]
        user_names = {user[0]: user[1] for user in all_users}
    else:
        user_names = {}

    st.subheader("Add Friend")
    if user_names:
        friend_name = st.selectbox("Select a user to add as a friend", options=list(user_names.values()))
        if st.button("Add Friend"):
            friend_id = [k for k, v in user_names.items() if v == friend_name][0]
            db.add_friend(USER_ID, friend_id)
            st.success(f"You are now friends with {friend_name}!")
    else:
        st.info("No other users found to add as friends.")

    st.subheader("Remove Friend")
    current_friends = db.get_friends(USER_ID)
    if current_friends:
        friend_names = [f[1] for f in current_friends]
        friend_to_remove = st.selectbox("Select a friend to remove", options=friend_names)
        if st.button("Remove Friend"):
            friend_id_to_remove = next((f[0] for f in current_friends if f[1] == friend_to_remove), None)
            if friend_id_to_remove:
                db.remove_friend(USER_ID, friend_id_to_remove)
                st.success(f"{friend_to_remove} has been removed from your friends list.")
                st.rerun() # Refresh to update the list
    else:
        st.info("You don't have any friends yet.")

    st.subheader("Leaderboard")
    leaderboard = db.get_friends_leaderboard(USER_ID)
    if leaderboard:
        st.write("🏆 **Workout Minutes This Week**")
        for i, (name, total_minutes) in enumerate(leaderboard):
            st.write(f"{i+1}. {name}: {total_minutes} minutes")
    else:
        st.info("No leaderboard data available for your friends.")

def goal_setting_section():
    st.header("🎯 Goal Setting")

    # CREATE Goal
    st.subheader("Set a New Goal")
    with st.form("new_goal_form"):
        description = st.text_input("Goal Description")
        target_value = st.number_input("Target Value")
        start_date = st.date_input("Start Date", datetime.date.today())
        end_date = st.date_input("End Date", datetime.date.today() + datetime.timedelta(days=30))
        submit_button = st.form_submit_button("Set Goal")
        if submit_button:
            db.create_goal(USER_ID, description, target_value, start_date, end_date)
            st.success("Goal set successfully!")
            
    # READ/UPDATE/DELETE Goals
    st.subheader("Your Current Goals")
    goals = db.read_goals(USER_ID)
    if goals:
        for goal in goals:
            with st.expander(f"Goal: {goal[2]}"):
                goal_id = goal[0]
                current_description = st.text_input("Description", value=goal[2], key=f"desc_{goal_id}")
                current_target_value = st.number_input("Target Value", value=float(goal[3]), key=f"target_{goal_id}")
                current_start_date = st.date_input("Start Date", value=goal[4], key=f"start_{goal_id}")
                current_end_date = st.date_input("End Date", value=goal[5], key=f"end_{goal_id}")
                current_is_completed = st.checkbox("Completed?", value=goal[6], key=f"completed_{goal_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Goal", key=f"update_{goal_id}"):
                        db.update_goal(goal_id, current_description, current_target_value, current_start_date, current_end_date, current_is_completed)
                        st.success("Goal updated!")
                with col2:
                    if st.button("Delete Goal", key=f"delete_{goal_id}"):
                        db.delete_goal(goal_id)
                        st.success("Goal deleted.")
                        st.rerun() # Refresh to update the list
    else:
        st.info("No goals set yet.")

def business_insights_section():
    st.header("📊 Business Insights")

    # Insights using COUNT, SUM, AVG, MIN, MAX
    total_workouts = db.get_total_workouts(USER_ID)
    avg_duration = db.get_average_workout_duration(USER_ID)
    max_weight = db.get_max_weight_lifted(USER_ID)
    weekly_minutes = db.get_weekly_workout_minutes(USER_ID)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Workouts", total_workouts[0][0] if total_workouts else 0)
    with col2:
        st.metric("Avg. Workout Duration", f"{avg_duration[0][0]:.2f} mins" if avg_duration and avg_duration[0][0] else "N/A")
    with col3:
        st.metric("Max Weight Lifted", f"{max_weight[0][0]} kg ({max_weight[0][1]})" if max_weight and max_weight[0][0] else "N/A")

    if weekly_minutes:
        st.subheader("This Week's Progress")
        st.write(f"You have worked out for **{weekly_minutes[0][1]}** minutes this week.")
    else:
        st.info("No workout data for this week.")

# --- Main App Logic ---

# Check if a user exists, if not, prompt to create one
user_exists = db.read_user(USER_ID)
if not user_exists:
    st.warning("No user found. Please create a sample user profile to start.")
    setup_user_profile()
    st.session_state['user_data'] = db.read_user(USER_ID)
else:
    st.session_state['user_data'] = user_exists
    
    # Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Profile", "Workouts", "Social", "Goals", "Insights"])

    if page == "Profile":
        user_profile_section()
    elif page == "Workouts":
        workout_tracking_section()
    elif page == "Social":
        social_connections_section()
    elif page == "Goals":
        goal_setting_section()
    elif page == "Insights":
        business_insights_section()
