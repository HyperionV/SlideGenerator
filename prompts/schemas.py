
CONTENT_REASONING_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "slide": {
            "type": "NUMBER",
        },
        "description": {
            "type": "STRING",
        },
        "content": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "uuid": {
                        "type": "STRING",
                    },
                    "content_description": {
                        "type": "STRING",
                    }
                }
            }
        }
    },
}

CONTENT_GENERATION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "slide": {"type": "NUMBER"},
        "description": {"type": "STRING"},
        "content": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "uuid": {"type": "STRING"},
                    "content": {}  # Can be STRING (text) or ARRAY (list/table)
                },
                "required": ["uuid", "content"]
            }
        },
        "charts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "uuid": {"type": "STRING"},
                    "content": {
                        "type": "OBJECT",
                        "properties": {
                            "series": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "name": {"type": "STRING"},
                                        "values": {
                                            "type": "ARRAY",
                                            "items": {"type": "NUMBER"}
                                        }
                                    },
                                    "required": ["name", "values"]
                                }
                            }
                        },
                        "required": ["series"]
                    },
                    "categories": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["uuid", "content", "categories"]
            }
        }
    },
    "required": ["slide", "description", "content"]
}

PRESENTATION_PLANNER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "overall_theme": {"type": "STRING"},
        "target_audience": {"type": "STRING"},
        "slides": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "position": {"type": "INTEGER"},
                    "description": {"type": "STRING"},
                    "content_guidelines": {"type": "STRING"}
                },
                "required": ["position", "description", "content_guidelines"]
            }
        }
    },
    "required": ["overall_theme", "target_audience", "slides"]
}


CONTENT_GENERATION_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "slide": {"type": "NUMBER"},
        "description": {"type": "STRING"},
        "content": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "uuid": {"type": "STRING"},
                    "content": {}  # Can be STRING (text) or ARRAY (list/table)
                },
                "required": ["uuid", "content"]
            }
        },
        "charts": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "uuid": {"type": "STRING"},
                    "content": {
                        "type": "OBJECT",
                        "properties": {
                            "series": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "name": {"type": "STRING"},
                                        "values": {
                                            "type": "ARRAY",
                                            "items": {"type": "NUMBER"}
                                        }
                                    },
                                    "required": ["name", "values"]
                                }
                            }
                        },
                        "required": ["series"]
                    },
                    "categories": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["uuid", "content", "categories"]
            }
        }
    },
    "required": ["slide", "description", "content"]
}