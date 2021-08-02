@elb @integration @alarm
Feature: Alarm Setup - load-balancer LambdaInternalError

  Scenario: Alarm is not triggered when count of lambda internal errors from lambda targets is less than a threshold
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | Subnet1Cidr                           |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                                       |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnet1Cidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                                       |

    When alarm "elb:alarm:application_lambda_internal_error:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationLoadBalancerName                                           | Threshold | EvaluationPeriods | DatapointsToAlarm  |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | 1000      | 1                 | 1                  |
    # we couldn't reproduce AWS Lambda Service internal error
    # so datapoints couldn't be generated
    # https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
