from flask import request
from flask_restx import Namespace, Resource, fields

from app.api.model_manager.handler import push_to_s3, download_from_s3, get_all_models
from app.core.auth_utils import token_required

ns = Namespace("Model Manager", description="Model management operations")

get_parser = ns.parser()
get_parser.add_argument("uuid", type=str, required=True, help="The model UUID")

upload_parser = ns.parser()
upload_parser.add_argument(
    "modelFile",
    location="files",
    type="file",
    required=True,
    help="The model file to upload (.tar.gz)",
)
upload_parser.add_argument(
    "modelName", location="form", type=str, required=True, help="The name of the model"
)
upload_parser.add_argument(
    "modelType",
    location="form",
    type=str,
    required=True,
    choices=["tensorflow", "pytorch"],
    help="The type of the model (e.g., TensorFlow, PyTorch)",
)
upload_parser.add_argument(
    "registerModel",
    location="form",
    type=bool,
    required=False,
    default=False,
    help="Whether to register the model after uploading",
)

delete_parser = ns.parser()
delete_parser.add_argument("uuid", type=str, required=True, help="The model UUID")

get_model_fields = ns.model(
    "Model",
    {
        "message": fields.String(description="Response message"),
        "body": fields.Nested(
            ns.model(
                "Body",
                {
                    "uuid": fields.String(description="Model UUID"),
                    "local_filepath_list": fields.List(
                        fields.String,
                        description="Local file path that stores the downloaded model",
                    ),
                },
            )
        ),
    },
)

post_model_fields = ns.model(
    "Model",
    {
        "message": fields.String(description="Response message"),
        "body": fields.Nested(
            ns.model(
                "Body",
                {
                    "uuid": fields.String(description="Model UUID"),
                    "path": fields.String(description="S3 path"),
                },
            )
        ),
    },
)


@ns.route("/")
class ModelManager(Resource):
    @ns.expect(get_parser)
    @ns.response(200, "Success", get_model_fields)
    @ns.doc(security="Bearer")
    @token_required
    def get(user_id, self):
        """
        Get model s3 path by UUID from db
        """
        model_uuid = request.args.get("uuid")
        resp = download_from_s3(model_uuid)
        return {"message": "Model retrieved successfully", "body": resp}, 200

    @ns.expect(upload_parser)
    @ns.response(200, "Success", post_model_fields)
    @ns.doc(security="Bearer")
    @token_required
    def post(user_id, self):
        """
        Upload a model to S3 and return the model UUID and S3 path
        """
        # Extract file and form data from the request
        uploaded_file = request.files.get("modelFile")
        model_name = request.form.get("modelName")
        model_type = request.form.get("modelType")
        register_model = (
            request.form.get("registerModel") == "true"
        )  # Assuming this comes in as a string 'true'/'false'

        if not uploaded_file or not model_name or not model_type:
            return {
                "message": "Missing required fields: modelFile, modelName, modelType"
            }, 400

        try:
            # Call your S3 upload function, passing necessary information
            resp = push_to_s3(user_id, uploaded_file, model_name, model_type)
        except Exception as e:
            return {"message": f"Failed to upload the model to S3: {e}"}, 500

        # Additional logic if 'registerModel' is set to True
        if register_model:
            # Implement registration logic here, as required
            # For example, adding the model to a registry
            pass

        return {"message": "File uploaded successfully", "body": resp}, 200

    @ns.expect(delete_parser)
    @ns.response(200, "Success")
    @ns.doc(security="Bearer")
    @token_required
    def delete(user_id, self):
        """
        Delete a model from s3 and db by UUID
        """
        model_uuid = request.args.get("uuid")

        if model_uuid:
            # Implement model deletion logic here
            return "Model deleted successfully", 200
        else:
            return "Model UUID is missing", 400


register_parser = ns.parser()
register_parser.add_argument("uuid", type=str, required=True, help="The model UUID")

post_register_fields = ns.model(
    "Model",
    {
        "message": fields.String(description="Response message"),
        "body": fields.Nested(
            ns.model(
                "Body",
                {
                    "uuid": fields.String(description="Model UUID"),
                    "path": fields.String(description="S3 path"),
                },
            )
        ),
    },
)


@ns.route("/all")
class ModelManagerInfo(Resource):
    @ns.response(200, "Success", get_model_fields)
    # @ns.doc(security="Bearer")
    # @token_required
    def get(self):
        """
        Get model s3 path by UUID from db
        """
        resp = get_all_models()
        return {"message": "Model retrieved successfully", "body": resp}, 200
