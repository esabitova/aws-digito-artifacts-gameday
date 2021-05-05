## Resource Tool (resource_tool.py)
Here is a need to have a tool to manipulate integration test resources without executing integration tests which can serve following goals:
* Destroy integration test resource for specific templates 
* List integration test templates which are deployed
* Fix integration test resources in case of failures (not implemented yet)
For this purpose we have cerated tool which you can execute using following command:
> python3.8 resource_manager/src/tools/resource_tool.py -t <template_name_a, tempolate_name_b> -c <command>
* -c, --command (required): Command to perform against cloud formation resources for given template names (DESTROY | DESTROY_ALL | LIST).
  * DESTROY - destroys resources by given template names (--cfn_templates)
  * DESTROY_ALL - destroys all resources, not need to provide template name
  * LIST - lists templates which are deployed with associated stacks  
* -t, --cfn_templates (required): Comma separated list of cloud formation templates. Example: -t RdsCfnTemplate,S3Template (no file path/extension).
* -p, --aws_profile (optional): AWS profile name for boto3 session creation.
NOTE: More information about how to use this tool you can execure command: ```python3.8 resource_manager/src/tools/resource_tool.py --help``` 
