
"""
Static cloud formation template path for assume roles. We want to combine all defined roles into single template.
Reason - reduce number of CFN stacks to be deployed to avoid reaching a limit of CFN stacks.
NOTE: DO NOT CHANGE IT!
"""
ssm_assume_role_cfn_s3_path = 'resource_manager/cloud_formation_templates/AutomationAssumeRoleTemplate.yml'

"""
  The cloud formation template pool size limit configuration. It is represented
  as a KEY=VALUE pair. In which case:\n
  KEY - is cloud formation template name (with no extension), template name should be unique\n
  VALUE - is number of template cloud formation stack copies should be presented before test execution\n
  NOTE: For SSM 'ASSUME_ROLE' templates we don't need to specify pool size, it is using default\n
  (multiple SSM documents can use same role at the same time)
"""
pool_size = dict(
 # In case if template name is not listed default pool size applied
 default=1,
 # The pool size configuration for RdsAuroraFailoverTestTemplate.yml (file name with no extension)
 RdsAuroraFailoverTestTemplate=3,
 EC2WithCWAgentCfnTemplate=1
)
