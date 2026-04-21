import os
import json
import yaml

# Create a sample OpenAPI spec for testing
openapi_spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Pet Store API",
        "version": "1.0.0",
        "description": "A simple pet store API for testing"
    },
    "servers": [
        {"url": "https://api.petstore.com/v1"}
    ],
    "paths": {
        "/pets": {
            "get": {
                "summary": "List all pets",
                "description": "Retrieve a list of all pets in the store",
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Pet"}
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "summary": "Create a new pet",
                "description": "Add a new pet to the store",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Pet"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Pet created successfully"
                    }
                }
            }
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Get pet by ID",
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Pet details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Pet"}
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Pet": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "integer", "format": "int64"},
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["available", "pending", "sold"]}
                }
            }
        }
    }
}

# Save as JSON
with open('petstore-api.json', 'w') as f:
    json.dump(openapi_spec, f, indent=2)

# Also save as YAML
with open('petstore-api.yaml', 'w') as f:
    yaml.dump(openapi_spec, f, default_flow_style=False)

print('Generated OpenAPI spec files: petstore-api.json and petstore-api.yaml')