def get_role(role_name):
    return {
        "Role": {
            "Path": "/",
            "RoleName": role_name,
            "RoleId": "XXXXXXXXXXXXXXXXXXX",
            "Arn": "arn:aws:iam::435978235099:role/" + role_name,
            "CreateDate": "2021-04-13T11:59:03+00:00",
            "AssumeRolePolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "ssm.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            },
            "Description": "",
            "MaxSessionDuration": 3600,
            "RoleLastUsed": {}
        }
    }
