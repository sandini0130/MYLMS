from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
import mysql.connector

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure key in production


# Database connection function
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Tharu@2002",
            database="lms",
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        return None


# Existing functions remain the same
def get_workshops():
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT w.workshop_name, w.workshop_description, w.start_time, z.zoom_link
        FROM workshops w
        LEFT JOIN workshop_zoom_links z ON w.workshop_id = z.workshop_id
        """
        cursor.execute(query)
        workshops = cursor.fetchall()
        return workshops
    except mysql.connector.Error as err:
        print(f"Error fetching workshops: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_social_media_groups():
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT course_name, platform, group_link 
        FROM social_media_groups 
        ORDER BY platform, course_name
        """
        cursor.execute(query)
        groups = cursor.fetchall()
        return groups
    except mysql.connector.Error as err:
        print(f"Error fetching social media groups: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


# Study group related functions
def get_available_groups(user_id):
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT sg.*
            FROM study_groups sg
            WHERE sg.group_id NOT IN (
                SELECT group_id 
                FROM study_group_members 
                WHERE user_id = %s
            )
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching available groups: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_joined_groups(user_id):
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT sg.*
            FROM study_groups sg
            JOIN study_group_members sgm ON sg.group_id = sgm.group_id
            WHERE sgm.user_id = %s
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching joined groups: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


def get_group_members(group_id):
    connection = get_db_connection()
    if not connection:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT u.first_name, u.last_name, u.username, sgm.joined_at
            FROM users u
            JOIN study_group_members sgm ON u.user_id = sgm.user_id
            WHERE sgm.group_id = %s
        """
        cursor.execute(query, (group_id,))
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching group members: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


# Routes
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        if not connection:
            flash("Database connection failed. Please try again later.")
            return redirect(url_for("login"))

        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT user_id, username, role, first_name, last_name 
                FROM users 
                WHERE username=%s AND password=%s
            """
            cursor.execute(query, (username, password))
            user = cursor.fetchone()
        except mysql.connector.Error as err:
            print(f"Error during login query: {err}")
            flash("An error occurred. Please try again.")
            user = None
        finally:
            cursor.close()
            connection.close()

        if user:
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["full_name"] = f"{user['first_name']} {user['last_name']}"
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    workshops = get_workshops()
    social_groups = get_social_media_groups()
    available_groups = get_available_groups(session["user_id"])
    joined_groups = get_joined_groups(session["user_id"])

    return render_template(
        "dashboard.html",
        full_name=session.get("full_name", "User"),
        role=session.get("role", "User"),
        workshops=workshops,
        social_groups=social_groups,
        available_groups=available_groups,
        joined_groups=joined_groups,
    )


@app.route("/create_group", methods=["POST"])
def create_group():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    group_name = request.form["group_name"]
    description = request.form["description"]
    created_by = session["user_id"]

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        # Create the group
        query = """
            INSERT INTO study_groups (group_name, description, created_by)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (group_name, description, created_by))
        group_id = cursor.lastrowid

        # Add creator as a member
        query = "INSERT INTO study_group_members (group_id, user_id) VALUES (%s, %s)"
        cursor.execute(query, (group_id, created_by))

        connection.commit()
        flash("Study group created successfully!")
    except mysql.connector.Error as err:
        print(f"Error creating group: {err}")
        flash("An error occurred while creating the group.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


@app.route("/join_group", methods=["POST"])
def join_group():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    group_id = request.form["group_id"]
    user_id = session["user_id"]

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = "INSERT INTO study_group_members (group_id, user_id) VALUES (%s, %s)"
        cursor.execute(query, (group_id, user_id))
        connection.commit()
        flash("Successfully joined the group!")
    except mysql.connector.Error as err:
        print(f"Error joining group: {err}")
        flash("An error occurred while joining the group.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


@app.route("/view_group/<int:group_id>")
def view_group(group_id):
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor(dictionary=True)
        # Get group details
        query = "SELECT * FROM study_groups WHERE group_id = %s"
        cursor.execute(query, (group_id,))
        group = cursor.fetchone()

        if not group:
            flash("Group not found!")
            return redirect(url_for("dashboard"))

        # Get group members
        members = get_group_members(group_id)

        return render_template("viewgroup.html", group=group, members=members)
    except mysql.connector.Error as err:
        print(f"Error viewing group: {err}")
        flash("An error occurred while viewing the group.")
        return redirect(url_for("dashboard"))
    finally:
        cursor.close()
        connection.close()


@app.route("/add_group", methods=["POST"])
def add_group():
    if "user_id" not in session:
        flash("You need to log in first!")
        return redirect(url_for("login"))

    course_name = request.form["course_name"]
    platform = request.form["platform"]
    group_link = request.form["group_link"]
    created_by = session["user_id"]

    connection = get_db_connection()
    if not connection:
        flash("Database connection failed. Please try again later.")
        return redirect(url_for("dashboard"))

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO social_media_groups (course_name, platform, group_link, created_by)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (course_name, platform, group_link, created_by))
        connection.commit()
        flash("New group added successfully!")
    except mysql.connector.Error as err:
        print(f"Error adding new group: {err}")
        flash("An error occurred. Please try again.")
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/get_users", methods=["GET"])
def get_users():
    if "user_id" not in session:
        return jsonify({"error": "You need to log in first!"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed."}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT user_id, first_name, last_name, username
            FROM users
            WHERE user_id != %s
        """
        cursor.execute(query, (session["user_id"],))
        users = cursor.fetchall()
        return jsonify(users), 200
    except mysql.connector.Error as err:
        print(f"Error fetching users: {err}")
        return jsonify({"error": "Failed to fetch users."}), 500
    finally:
        cursor.close()
        connection.close()


@app.route("/get_chat", methods=["GET"])
def get_chat():
    if "user_id" not in session:
        return jsonify({"error": "You need to log in first!"}), 401

    receiver_id = request.args.get("receiver_id")
    sender_id = session["user_id"]

    if not receiver_id:
        return jsonify({"error": "Receiver ID is required!"}), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed."}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT sender_id, receiver_id, message_text, created_at
            FROM messages
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
            ORDER BY created_at ASC
        """
        cursor.execute(query, (sender_id, receiver_id, receiver_id, sender_id))
        chat = cursor.fetchall()
        return jsonify(chat), 200
    except mysql.connector.Error as err:
        print(f"Error fetching chat: {err}")
        return jsonify({"error": "Failed to fetch chat."}), 500
    finally:
        cursor.close()
        connection.close()


@app.route("/send_message", methods=["POST"])
def send_message():
    if "user_id" not in session:
        return jsonify({"error": "You need to log in first!"}), 401

    data = request.json
    sender_id = session["user_id"]
    receiver_id = data.get("receiver_id")
    message_text = data.get("message_text")

    if not receiver_id or not message_text:
        return (
            jsonify({"error": "Receiver ID and message text are required!"}),
            400,
        )

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed."}), 500

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO messages (sender_id, receiver_id, message_text)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (sender_id, receiver_id, message_text))
        connection.commit()
        return jsonify({"success": "Message sent successfully!"}), 201
    except mysql.connector.Error as err:
        print(f"Error sending message: {err}")
        return jsonify({"error": "Failed to send message."}), 500
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    app.run(debug=True)
