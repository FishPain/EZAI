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
<<<<<<< Updated upstream
            "message": "Inference Results retrieved successfully",
            "inference_result": inference_result,
        }, 200

    # flask status code 200
    @ns.expect(upload_parser)
    @ns.response(200, "Success", inference_model)
    @ns.doc(security="Bearer")
    @token_required
    def post(user_id, self):
        """Post an inference job"""
        # Process the JSON data here
        # You can perform any required operations
        # json data in the format of {"inputs": ndarray.tolist()}
        json_data = request.files.get("inference_data")
        model_registry_uuid = request.args.get("uuid")
        sm = SagemakerManager(
            role=sm_constants.ROLE,
            bucket_name=sm_constants.BUCKET_NAME,
        )
        
        if json_data and model_registry_uuid and json_data.filename.endswith(".json"):
            model_endpoint = ModelRegistryModel.get_record_by_uuid(
                model_registry_uuid
            ).model_endpoint

            base = "https://"
            host = "runtime.sagemaker.ap-southeast-1.amazonaws.com"
            canonical_uri = f"/endpoints/{model_endpoint}/invocations"

            inference_endpoint = base + host + canonical_uri

            # load the json data from the file
            json_data = json.load(json_data)

            if "inputs" not in json_data:
                return "Invalid JSON data provided", 400

            json_string = json.dumps(json_data)

            header = get_header(payload=json_string, endpoint=model_endpoint)

            response = sm.invoke_endpoint(
                endpoint=inference_endpoint, payload=json_string, header=header
            )

            dummy_user_uuid = UserModel.get_user_by_email(
                "dummyUser@dummy.com"
            ).user_uuid
            if dummy_user_uuid is None:
                raise Exception("User does not exist")

            inference_status = "pending"

            if response.status_code == 200:
                inference_status = "completed"

            inference_uuid = InferenceModel.save_inference_to_db(
                user_uuid=dummy_user_uuid,
                model_registry_uuid=model_registry_uuid,
                inference_status=inference_status,
            )

            response_data = {
                "message": "Inference job posted successfully",
                "body": {
                    "uuid": inference_uuid,
                    "status": response.status_code,
                    "inference_result": json.loads(response.text),
                },
            }
            return response_data, 200
        else:
            return "No JSON data provided", 400

    @ns.expect(delete_parser)
    @ns.response(200, "Success")
    @ns.doc(security="Bearer")
    @token_required
    def delete(user_id, self):
        """Delete the inference based on inference id and returns 200 if success"""
        inference_uuid = request.args.get("uuid")

        if inference_uuid:
            # Implement model deletion logic here
            return "Inference job stopped successfully", 200
        else:
            return "Inference job not found", 400
=======
            "message": "User info fetched successfully",
            "user_info": user.to_dict(),
        }, 200
>>>>>>> Stashed changes
