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

metadata_attrs_map = {
    "test": test_meta_required_attrs,
    "sop": sop_meta_required_attrs,
    "alarm": alarm_meta_required_attrs
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
