from .resource_model import ResourceModel

"""
Static cloud formation template path for assume roles. We want to combine all defined roles into single template.
Reason - reduce number of CFN stacks to be deployed to avoid reaching a limit of CFN stacks.
NOTE: DO NOT CHANGE IT!
"""
ssm_assume_role_cfn_s3_path = 'resource_manager/cloud_formation_templates/AutomationAssumeRoleTemplate.yml'

"""
  The cloud formation template pool size limit configuration. It is represented 
  as a KEY=VALUE pair. In which case:\n
  KEY - is cloud formation template name (with no extension), template 
  name should be unique\n
  VALUE - is a map of resource type and pool size (we can use same template for different 
  resource types). For example: 
  - TemplateA={ON_DEMAND:3, DEDICATED:2}
  - TemplateB={ON_DEMAND:3}  
 
  NOTE: For 'ASSUME_ROLE' and 'DEDICATED' templates we don't need to specify 
  pool size, it is using default\n 
  (multiple SSM documents can use same role at the same time)
"""
pool_size = dict(
 # In case if template name is not listed default pool size applied
 default=1,
 # The pool size configuration for RdsAuroraFailoverTestTemplate.yml (file name with no extension)
 RdsAuroraFailoverTestTemplate={ResourceModel.Type.ON_DEMAND: 2},
 RdsCfnTemplate={ResourceModel.Type.ON_DEMAND: 3},
 # We have 8 tests which are using EC2WithCWAgentCfnTemplate.yml template
 EC2WithCWAgentCfnTemplate={ResourceModel.Type.ON_DEMAND: 4},
 RdsAuroraWithBacktrackTemplate={ResourceModel.Type.ON_DEMAND: 1},
 # We have 7 tests which are using DocDbTemplate.yml template
 DocDbTemplate={ResourceModel.Type.ON_DEMAND: 4},
 # We have 10 tests which are using AsgCfnTemplate.yml template,
 # however we cannot create many templates since it creates VPC,
 # to fix this issues need to work on: https://issues.amazon.com/issues/Digito-1741
 AsgCfnTemplate={ResourceModel.Type.ON_DEMAND: 1},
 # We have 22 tests which are using SqsTemplate.yml template
 SqsTemplate={ResourceModel.Type.ON_DEMAND: 8},
 # We have 6 tests which are using S3Template.yml template
 S3Template={ResourceModel.Type.ON_DEMAND: 3}
)
