from flask import request, session, jsonify
from flask_restx import Namespace, Resource, fields

from app.models.models import UserModel
from app.core.auth_utils import (
    set_password,
    check_password,
    generate_token,
    token_required,
)

ns = Namespace("User", description="User Authentication Endpoints")

user_signup_parser = ns.parser()
user_signup_parser.add_argument("username", type=str, required=True, help="Username")
user_signup_parser.add_argument("email", type=str, required=True, help="Email")
user_signup_parser.add_argument("password", type=str, required=True, help="Password")

user_login_parser = ns.parser()
user_login_parser.add_argument("email", type=str, required=True, help="Email")
user_login_parser.add_argument("password", type=str, required=True, help="Password")

response_model = ns.model(
    "Response",
    {
        "message": fields.String(description="Response message"),
        "uuid": fields.String(description="User UUID", required=False),
    },
)


@ns.route("/signup")
class UserSignup(Resource):
    @ns.expect(user_signup_parser)
    @ns.response(200, "Success", response_model)
    @ns.response(
        400, "Email already registered"
    )  # New response code for email conflict
    def post(self):
        """Sign up a new user"""
        try:
            # Extract data from query parameters
            data = request.args
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            hashed_password = set_password(password)

            # Create a new user
            user_uuid = UserModel.create_user(username, email, hashed_password)

        except Exception as e:
            return {"message": f"Failed to create user: {e}"}, 500

        # Store the user UUID in session cookies to manage logged-in status
        session["user_uuid"] = user_uuid
        return {"message": "User created successfully", "uuid": user_uuid}, 200


@ns.route("/login")
class UserLogin(Resource):
    @ns.expect(user_login_parser)
    @ns.response(200, "Success", response_model)
    def post(self):
        """Login a user"""
        try:
            # Extract data from JSON body
            data = request.args
            email = data.get("email")
            password = data.get("password")

            # Fetch the user by email
            user = UserModel.get_user_by_email(email)

            if not user:
                return {"message": "User not found"}, 404

            # Verify the password
            if not check_password(password, user.password):
                return {"message": "Incorrect password"}, 401

        except Exception as e:
            return {"message": f"Failed to log in: {e}"}, 500

        token = generate_token(user.user_uuid)

        return {
            "message": "Login successful",
            "uuid": user.user_uuid,
            "token": token,
        }, 200


@ns.route("/dummy")
class DummyUser(Resource):
    @ns.response(200, "Success", response_model)
    def post(self):
        """Create Dummy User"""
        try:
            dummy_username = "dummyUser"
            dummy_email = "dummyUser@dummy.com"
            dummy_pwd = "dummyHexPwd"

            user_uuid = UserModel.create_user(dummy_username, dummy_email, dummy_pwd)
        except Exception as e:
            return {"message": f"Failed to create dummy user: {e}"}, 500

        return {"message": "Dummy user created successfully", "body": user_uuid}, 200


@ns.route("/info")
class UserInfo(Resource):
    @ns.response(200, "Success", response_model)
    @ns.doc(security="Bearer")
    @token_required
    def get(user_id, self):
        """Get user info"""
        user = UserModel.get_user_record_by_uuid(user_id)
        return {
            "message": "User info fetched successfully",
            "user_info": user.to_dict(),
        }, 200


get_contributors_parser = ns.parser()
get_contributors_parser.add_argument(
    "top_n", type=int, required=False, help="Get top n contributors"
)


@ns.expect(get_contributors_parser)
@ns.route("/contributors")
class UserContributors(Resource):
    @ns.response(200, "Success", response_model)
    def get(self):  # Correctly get user_id from the decorator
        """Get contributor list with name, contribution count, and last contribution date"""
        try:
            top_n = request.args.get("top_n")

            # Query the database to get contributors' data
            contributors = UserModel.get_contributors_with_contributions(top_n)

            # Formatting the response data
            contributor_list = []

            for contributor in contributors:
                contributor_list.append(
                    {
                        "contributor_name": contributor.username,
                        "contribution_count": contributor.contribution_count,
                        "last_contribution_date": contributor.last_contribution_date.isoformat(),
                    }
                )

            return {
                "message": "Contributor list retrieved successfully",
                "contributors": contributor_list,
            }, 200

        except Exception as e:
            return {"message": f"Failed to fetch contributors: {str(e)}"}, 500
