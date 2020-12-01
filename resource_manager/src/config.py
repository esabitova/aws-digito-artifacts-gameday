"""
Base folder path for Cloud Formation Templates to be used
to create resources for SSM automation document testing.
NOTE: Every document name should be unique.
"""
base_template_dir = 'resource_manager/cloud_formation_templates/'

"""
  The cloud formation template pool size limit configuration. It is represented 
  as a KEY=VALUE pair. In which case:
  KEY - is cloud formation template name (with no extension), template name should be unique
  VALUE - is number of template cloud formation stack copies should be presented before test execution
"""
pool_size = dict(
   # In case if template name is not listed default pool size applied
   default=1,
   # The pool size configuration for RdsAuroraFailoverTestTemplate.yml (file name with no extension)
   RdsAuroraFailoverTestTemplate=3
)

