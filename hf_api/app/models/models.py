import uuid, os, bcrypt
from datetime import datetime
from pymongo import MongoClient, DESCENDING
from types import SimpleNamespace

def add_indexing():
    # UserModel Indexing
    db["user_model"].create_index([("email", DESCENDING)], unique=True)
    db["user_model"].create_index([("username", DESCENDING)], unique=True)

    # MLModel Indexing
    db["ml_model"].create_index([("model_name", DESCENDING)], unique=True)
    db["model_registry_model"].create_index([("model_uuid", DESCENDING)], unique=True)

    # InferenceModel Indexing
    db["inference_model"].create_index([("model_registry_uuid", DESCENDING)], unique=True)
    db["jobs_model"].create_index([("job_uuid", DESCENDING)], unique=True)


client = MongoClient(os.getenv("DATABASE_URI"))
db = client.get_database()
add_indexing()

def to_namespace(data):
    if data:
        return SimpleNamespace(**data)
    return None


class UserModel:
    collection = db["user_model"]

    def __init__(self, username, email, password, user_uuid=None):
        self.user_uuid = str(uuid.uuid4()) if not user_uuid else user_uuid
        self.username = username
        self.email = email
        self.password = password

    def to_dict(self):
        return {
            "user_uuid": self.user_uuid,
            "username": self.username,
            "email": self.email,
        }

    @classmethod
    def from_dict(cls, data):
        if data:
            return cls(
                user_uuid=data.get("user_uuid"),
                username=data.get("username"),
                email=data.get("email"),
                password=data.get("password"),
            )
        return None

    @staticmethod
    def create_user(username, email, password):
        if UserModel.get_user_by_email(email) or UserModel.get_user_by_username(
            username
        ):
            raise Exception("User already exists")
        new_user = UserModel(username=username, email=email, password=password)
        UserModel.collection.insert_one(new_user.__dict__)
        return new_user.user_uuid

    @staticmethod
    def get_user_by_email(email):
        return UserModel.from_dict(UserModel.collection.find_one({"email": email}))

    @staticmethod
    def get_user_by_username(username):
        return UserModel.from_dict(
            UserModel.collection.find_one({"username": username})
        )

    @staticmethod
    def get_user_record_by_uuid(user_uuid):
        return UserModel.from_dict(
            UserModel.collection.find_one({"user_uuid": user_uuid})
        )

    @staticmethod
    def get_contributors_with_contributions(top_n=None):
        pipeline = [
            {
                "$lookup": {
                    "from": "jobs_model",
                    "localField": "user_uuid",
                    "foreignField": "user_uuid",
                    "as": "jobs",
                }
            },
            {
                "$project": {
                    "username": 1,
                    "contribution_count": {"$size": "$jobs"},
                    "last_contribution_date": {"$max": "$jobs.job_datetime"},
                }
            },
            {"$sort": {"contribution_count": -1}},
        ]
        if top_n:
            pipeline.append({"$limit": int(top_n)})
        count = list(UserModel.collection.aggregate(pipeline))
        return [to_namespace(user) for user in count]


class MLModel:
    collection = db["ml_model"]

    def __init__(self, user_uuid, model_name, model_type, s3_url):
        self.model_uuid = str(uuid.uuid4())
        self.user_uuid = user_uuid
        self.upload_datetime = datetime.now()
        self.model_name = model_name
        self.model_type = model_type
        self.s3_url = s3_url

    def to_dict(self):
        return {
            "model_uuid": self.model_uuid,
            "user_uuid": self.user_uuid,
            "upload_datetime": self.upload_datetime.isoformat(),
            "model_name": self.model_name,
            "model_type": self.model_type,
            "s3_url": self.s3_url,
        }

    @staticmethod
    def save_model_to_db(user_uuid, model_name, model_type, s3_url):
        model = MLModel(
            user_uuid=user_uuid,
            model_name=model_name,
            model_type=model_type,
            s3_url=s3_url,
        )
        MLModel.collection.insert_one(model.__dict__)
        return model.model_uuid

    @staticmethod
    def get_record_by_uuid(model_uuid):
        return to_namespace(MLModel.collection.find_one({"model_uuid": model_uuid}))

    @staticmethod
    def get_all_models_by_user_uuid(user_uuid):
        return list(to_namespace(MLModel.collection.find({"user_uuid": user_uuid})))

    @staticmethod
    def get_all_models():
        return list(to_namespace(MLModel.collection.find()))

    # allow user to update model type
    @staticmethod
    def update_model_type(model_uuid: str, new_model_type: str, current_version: int) -> Optional[Dict[str, Any]]:
        result = MLModel.collection.update_one(
            {"model_uuid": model_uuid, "version": current_version},
            {"$set": {"model_type": new_model_type}, "$inc": {"version": 1}}
        )
        if result.matched_count == 0:
            raise Exception("Version mismatch or model not found. Retry the update.")

        # Fetch and return the updated model
        updated_model = MLModel.collection.find_one({"model_uuid": model_uuid})
        return updated_model


class ModelRegistryModel:
    collection = db["model_registry_model"]

    def __init__(
        self,
        model_uuid,
        model_version,
        model_status,
        model_endpoint,
        model_registry_uuid=None,
    ):
        self.model_registry_uuid = (
            str(uuid.uuid4()) if not model_registry_uuid else model_registry_uuid
        )
        self.model_uuid = model_uuid
        self.model_version = model_version
        self.model_status = model_status
        self.model_endpoint = model_endpoint

    @classmethod
    def from_dict(cls, data):
        if data:
            return cls(
                model_registry_uuid=data.get("model_registry_uuid"),
                model_uuid=data.get("model_uuid"),
                model_version=data.get("model_version"),
                model_status=data.get("model_status"),
                model_endpoint=data.get("model_endpoint"),
            )
        return None

    @staticmethod
    def register_model(model_uuid, model_version, model_status, model_endpoint):
        model = ModelRegistryModel(
            model_uuid=model_uuid,
            model_version=model_version,
            model_status=model_status,
            model_endpoint=model_endpoint,
        )
        ModelRegistryModel.collection.insert_one(model.__dict__)
        return model.model_registry_uuid

    @staticmethod
    def get_record_by_uuid(model_registry_uuid):
        return to_namespace(
            ModelRegistryModel.collection.find_one(
                {"model_registry_uuid": model_registry_uuid}
            )
        )

    @staticmethod
    def update_record_by_uuid(model_registry_uuid, **kwargs):
        ModelRegistryModel.collection.update_one(
            {"model_registry_uuid": model_registry_uuid}, {"$set": kwargs}
        )
        return model_registry_uuid

    @staticmethod
    def delete_record_by_uuid(model_registry_uuid):
        ModelRegistryModel.collection.delete_one(
            {"model_registry_uuid": model_registry_uuid}
        )
        return model_registry_uuid


class InferenceModel:
    collection = db["inference_model"]

    def __init__(
        self,
        user_uuid,
        model_registry_uuid,
        inference_status,
        inference_uuid=None,
        inference_datetime=None,
    ):
        self.inference_uuid = (
            str(uuid.uuid4()) if not inference_uuid else inference_uuid
        )
        self.user_uuid = user_uuid
        self.model_registry_uuid = model_registry_uuid
        self.inference_datetime = (
            datetime.now() if not inference_datetime else inference_datetime
        )
        self.inference_status = inference_status

    @classmethod
    def from_dict(cls, data):
        if data:
            return cls(
                inference_uuid=data.get("inference_uuid"),
                user_uuid=data.get("user_uuid"),
                model_registry_uuid=data.get("model_registry_uuid"),
                inference_datetime=data.get("inference_datetime"),
                inference_status=data.get("inference_status"),
            )
        return None

    @staticmethod
    def save_inference_to_db(user_uuid, model_registry_uuid, inference_status):
        inference = InferenceModel(
            user_uuid=user_uuid,
            model_registry_uuid=model_registry_uuid,
            inference_status=inference_status,
        )
        InferenceModel.collection.insert_one(inference.__dict__)
        return inference.inference_uuid

    @staticmethod
    def get_record_by_uuid(inference_uuid):
        return to_namespace(
            InferenceModel.collection.find_one({"inference_uuid": inference_uuid})
        )

    @staticmethod
    def get_record_by_model_registry_uuid(model_registry_uuid):
        return to_namespace(
            InferenceModel.collection.find_one(
                {"model_registry_uuid": model_registry_uuid}
            )
        )

    @staticmethod
    def delete_record_by_uuid(inference_uuid):
        InferenceModel.collection.delete_one({"inference_uuid": inference_uuid})
        return inference_uuid

    @staticmethod
    def count_model_runs():
        pipeline = [
            {"$group": {"_id": "$model_registry_uuid", "run_count": {"$sum": 1}}},
            {"$project": {"model_registry_uuid": "$_id", "run_count": 1}},
        ]
        return list(to_namespace(InferenceModel.collection.aggregate(pipeline)))


class JobsModel:
    collection = db["jobs_model"]

    def __init__(
        self,
        job_uuid,
        user_uuid,
        job_type,
        job_status,
        reference_uuid,
        job_datetime=None,
    ):
        self.job_uuid = job_uuid
        self.user_uuid = user_uuid
        self.job_type = job_type
        self.job_datetime = datetime.now() if not job_datetime else job_datetime
        self.job_status = job_status
        self.reference_uuid = reference_uuid

    @classmethod
    def from_dict(cls, data):
        if data:
            return cls(
                job_uuid=data.get("job_uuid"),
                user_uuid=data.get("user_uuid"),
                job_type=data.get("job_type"),
                job_datetime=data.get("job_datetime"),
                job_status=data.get("job_status"),
                reference_uuid=data.get("reference_uuid"),
            )
        return None

    @staticmethod
    def save_job_to_db(job_uuid, user_uuid, job_type, job_status, reference_uuid):
        job = JobsModel(
            job_uuid=job_uuid,
            user_uuid=user_uuid,
            job_type=job_type,
            job_status=job_status,
            reference_uuid=reference_uuid,
        )
        JobsModel.collection.insert_one(job.__dict__)
        return job.job_uuid

    @staticmethod
    def get_record_by_uuid(job_uuid):
        return to_namespace(JobsModel.collection.find_one({"job_uuid": job_uuid}))

    @staticmethod
    def update_task_status(job_uuid, job_status):
        JobsModel.collection.update_one(
            {"job_uuid": job_uuid}, {"$set": {"job_status": job_status}}
        )
        return job_uuid

    @staticmethod
    def update_task_reference(job_uuid, reference_uuid):
        JobsModel.collection.update_one(
            {"job_uuid": job_uuid}, {"$set": {"reference_uuid": reference_uuid}}
        )
        return job_uuid


def get_model_run_counts_with_details():
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "ModelRegistryModel",
                    "localField": "model_uuid",
                    "foreignField": "model_uuid",
                    "as": "registry_details",
                }
            },
            {
                "$lookup": {
                    "from": "InferenceModel",
                    "localField": "registry_details.model_registry_uuid",
                    "foreignField": "model_registry_uuid",
                    "as": "inference_details",
                }
            },
            {
                "$unwind": {
                    "path": "$registry_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$group": {
                    "_id": {
                        "model_uuid": "$model_uuid",
                        "model_registry_uuid": "$registry_details.model_registry_uuid",
                        "model_version": "$registry_details.model_version",
                        "model_name": "$model_name",
                        "model_type": "$model_type",
                        "upload_datetime": "$upload_datetime",
                    },
                    "run_count": {
                        "$sum": {
                            "$cond": {
                                "if": {"$ne": ["$inference_details", []]},
                                "then": 1,
                                "else": 0,
                            }
                        }
                    },
                    "registered": {
                        "$max": {
                            "$cond": {
                                "if": {"$ne": ["$registry_details", None]},
                                "then": 1,
                                "else": 0,
                            }
                        }
                    },
                }
            },
        ]

        model_run_counts = list(MLModel.collection.aggregate(pipeline))
    except Exception as e:
        raise Exception(f"Failed to fetch all models: {e}")

    resp = []
    for model in model_run_counts:
        details = model["_id"]
        model_dict = {
            "model_registry_uuid": details.get("model_registry_uuid"),
            "model_version": details.get("model_version"),
            "run_count": model["run_count"] if model["registered"] else 0,
            "model_name": details["model_name"],
            "model_type": details["model_type"],
            "upload_datetime": (
                details["upload_datetime"].isoformat()
                if details["upload_datetime"]
                else None
            ),
            "registered": bool(model["registered"]),
        }
        resp.append(model_dict)

    return resp


def get_model_run_counts_with_details_filter(top_n):
    top_n = int(top_n)
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "ModelRegistryModel",
                    "localField": "model_uuid",
                    "foreignField": "model_uuid",
                    "as": "registry_details",
                }
            },
            {
                "$lookup": {
                    "from": "InferenceModel",
                    "localField": "registry_details.model_registry_uuid",
                    "foreignField": "model_registry_uuid",
                    "as": "inference_details",
                }
            },
            {
                "$unwind": {
                    "path": "$registry_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$group": {
                    "_id": {
                        "model_uuid": "$model_uuid",
                        "model_registry_uuid": "$registry_details.model_registry_uuid",
                        "model_version": "$registry_details.model_version",
                        "model_name": "$model_name",
                        "model_type": "$model_type",
                        "upload_datetime": "$upload_datetime",
                    },
                    "run_count": {
                        "$sum": {
                            "$cond": {
                                "if": {"$ne": ["$inference_details", []]},
                                "then": 1,
                                "else": 0,
                            }
                        }
                    },
                    "registered": {
                        "$max": {
                            "$cond": {
                                "if": {"$ne": ["$registry_details", None]},
                                "then": 1,
                                "else": 0,
                            }
                        }
                    },
                }
            },
            {"$sort": {"run_count": DESCENDING}},
            {"$limit": top_n},
        ]

        model_run_counts = list(MLModel.collection.aggregate(pipeline))
    except Exception as e:
        raise Exception(f"Failed to fetch all models: {e}")

    resp = []
    for model in model_run_counts:
        details = model["_id"]
        model_dict = {
            "model_registry_uuid": details.get("model_registry_uuid"),
            "model_version": details.get("model_version"),
            "run_count": model["run_count"] if model["registered"] else 0,
            "model_name": details["model_name"],
            "model_type": details["model_type"],
            "upload_datetime": (
                details["upload_datetime"].isoformat()
                if details["upload_datetime"]
                else None
            ),
            "registered": bool(model["registered"]),
        }
        resp.append(model_dict)

    return resp


def search_for_models(search_term):
    search_regex = {"$regex": search_term, "$options": "i"}
    models = to_namespace(MLModel.collection.find({"model_name": search_regex}))
    return [model for model in models]


def get_registered_model_by_user_uuid(user_uuid):
    pipeline = [
        {"$match": {"user_uuid": user_uuid}},
        {
            "$lookup": {
                "from": "model_registry_model",
                "localField": "model_uuid",
                "foreignField": "model_uuid",
                "as": "registry",
            }
        },
        {"$unwind": "$registry"},
        {
            "$project": {
                "model_registry_uuid": "$registry.model_registry_uuid",
                "model_uuid": "$model_uuid",
                "model_name": 1,
                "model_type": 1,
                "model_version": "$registry.model_version",
                "model_status": "$registry.model_status",
                "model_endpoint": "$registry.model_endpoint",
            }
        },
    ]
    records = list(MLModel.collection.aggregate(pipeline))

    resp = []

    for record in records:
        resp.append(
            {
                "model_uuid": record["model_uuid"],
                "model_version": record["model_version"],
                "model_registry_uuid": record["model_registry_uuid"],
                "model_name": record["model_name"],
                "model_type": record["model_type"],
                "model_endpoint": record["model_endpoint"],
                "model_status": record["model_status"],
            }
        )

    return resp