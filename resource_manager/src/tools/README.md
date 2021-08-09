## Resource Tool (resource_tool.py)
Here is a need to have a tool to manipulate integration test resources without executing integration tests which can serve following goals:
* Destroy integration test resource for specific templates 
* List integration test templates which are deployed
* Fix integration test resources in case of failures (not implemented yet)
For this purpose we have cerated tool which you can execute using following command:
> PYTHONPATH=. python3.8 resource_manager/src/tools/resource_tool.py -t <template_name_a, tempolate_name_b> -c <command>
* -c, --command (required): Command to perform against cloud formation resources for given template names (DESTROY | DESTROY_ALL | LIST).
  * DESTROY - destroys resources by given template names (--cfn_templates)
  * DESTROY_ALL - destroys all resources, not need to provide template name
  * LIST - lists templates which are deployed with associated stacks  
* -t, --cfn_templates (required): Comma separated list of cloud formation templates. Example: -t RdsCfnTemplate,S3Template (no file path/extension).
* -s, --status (optional): Comma separated list of resource statuses to perform operation against. Example: -s EXECUTE_FAILED,CREATE_FAILED,UPDATE_FAILED,AVAILABLE
* -a, --age (optional): Age in minutes of resource in latest resource status to perform operation against.
* -p, --aws_profile (optional): AWS profile name for boto3 session creation.
NOTE: More information about how to use this tool you can execure command: ```python3.8 resource_manager/src/tools/resource_tool.py --help``` 
#### Credentials
In order to execute tool you will have to configure AWS profile on which you would like to execute this resource tool, more about AWS profiles you can find here:
* https://docs.aws.amazon.com/sdk-for-php/v3/developer-guide/guide_credentials_profiles.html
###### Roles
# TODO (semiond): Add list of permissions.