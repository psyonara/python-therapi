from therapi import BaseAPIConsumer, Endpoint
from therapi.authentication import TokenBearerAuthentication


class Endpoints:
    GET_THING = Endpoint(url_path="/things/<thing_id>/", method="GET", required_url_params=["thing_id"])
    GET_FILES = Endpoint(url_path="/things/<thing_id>/files/", method="GET", required_url_params=["thing_id"])
    CREATE_COLLECTION = Endpoint(url_path="/collections/", method="POST")


class ThingiverseClient(BaseAPIConsumer):
    def __init__(self, bearer_token):
        super().__init__(
            base_url="https://api.thingiverse.com/",
            request_modifiers=[TokenBearerAuthentication(token=bearer_token)]
        )

    def get_thing(self, thing_id: int):
        return self.call_endpoint(Endpoints.GET_THING, params={"thing_id": thing_id})

    def get_thing_files(self, thing_id: int):
        file_info = self.call_endpoint(Endpoints.GET_FILES, params={"thing_id": thing_id})
        return [info["download_url"] for info in file_info]

    def create_collection(self, name: str, description: str):
        payload = {"name": name, "description": description}
        return self.call_endpoint(Endpoints.CREATE_COLLECTION, payload=payload)
