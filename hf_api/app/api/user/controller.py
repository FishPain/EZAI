from flask import request
from flask_restx import Namespace, Resource, fields

from app.models.models import UserModel

ns = Namespace("User", description="Create Dummy User")

user_parser = ns.parser()
user_parser.add_argument("username", type=str, required=True, help="Username")
user_parser.add_argument("email", type=str, required=True, help="Email")
user_parser.add_argument("password", type=str, required=True, help="Password")

user_modal = ns.model(
    "User",
    {
        "message": fields.String(description="Response message"),
        "uuid": fields.String(description="User UUID"),
    },
)

@ns.route("/")
class User(Resource):
    @ns.expect(user_parser)
    @ns.response(200, "Success", user_modal)
    def post(self):
        """Create User"""
        try:

            username = request.args.get("username")
            email = request.args.get("email")
            password = request.args.get("password")
            user_uuid = UserModel.create_user(username, email, password)

        except Exception as e:
            return {"message": f"Failed to create user: {e}"}, 500

        return {"message": "User created successfully", "body": user_uuid}, 200


@ns.route("/dummy")
class DummyUser(Resource):
    @ns.response(200, "Success", user_modal)
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
