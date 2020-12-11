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
   RdsAuroraFailoverTestTemplate=3
)


