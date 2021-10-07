sop_meta_required_attrs = [
    "displayName",
    "description",
    "documentName",
    "documentType",
    "minorVersion",
    "documentContentPath",
    "documentFormat",
    "risk",
    "assumeRoleCfnPath",
    "tag",
    "failureType"
]

test_meta_required_attrs = [
    "displayName",
    "description",
    "documentName",
    "documentType",
    "minorVersion",
    "documentContentPath",
    "documentFormat",
    "risk",
    "assumeRoleCfnPath",
    "tag",
    "failureType"
]

alarm_meta_required_attrs = [
    "displayName",
    "description",
    "alarmName",
    "alarmType",
    "alarmContentPath",
    "documentFormat",
    "tag",
    "minorVersion",
    "failureType"
]

util_meta_required_attrs = [
    "documentName",
    "documentType",
    "documentContentPath",
    "documentFormat",
    "tag",
    "minorVersion"
]

metadata_attrs_map = {
    "test": test_meta_required_attrs,
    "sop": sop_meta_required_attrs,
    "alarm": alarm_meta_required_attrs,
    "util": util_meta_required_attrs
}

metadata_valid_values_map = {
    "risk": ["SMALL", "MEDIUM", "HIGH"],
    "failureType": ["REGION", "AZ", "HARDWARE", "SOFTWARE"],
    "documentType": ["Automation", "Command"],
    "documentFormat": ["YAML", "JSON"]
}

metadata_attrs_max_size = {
    "displayName": 200,
    "alarmName": 100,
    "documentName": 100
}

metadata_doc_type_suffix = {
    "sop": "SOP",
    "test": "Test",
    "util": "Util"
}

allowed_service_name_aliases = {
    "api-gw": ["RestApiGw", "HttpWsApiGw"],
    "docdb": ["DocumentDB"],
    "dynamodb": ["DynamoDB"],
    "elasticache": ["Elasticache", "Redis"],
    "kinesis-analytics": ["KinesisDataAnalytics"],
    "load-balancer": ["ApplicationLb", "NetworkGwLb"],
    "nat-gw": ["NatGw"]
}
