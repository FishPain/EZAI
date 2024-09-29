from flask_restx import Namespace, Resource, fields
from app.models.models import UserModel

ns = Namespace("User", description="Create Dummy User")

user_modal = ns.model(
    "User",
    {
        "message": fields.String(description="Response message"),
        "uuid": fields.String(description="User UUID"),
    },
)

@ns.route("/dummy")
class User(Resource):
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