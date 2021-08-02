@elb @integration @alarm
Feature: Alarm Setup - load-balancer LambdaUserError

  Scenario: Alarm is not triggered when count of lambda user errors from lambda targets is less than a threshold
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | Subnet1Cidr                           |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                                       |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnet1Cidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                                       |

    When alarm "elb:alarm:application_lambda_user_error:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | LambdaTargetFullName                                                 | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>LambdaTargetFullName}}  | 1000      | 1                 | 1                 |
    And invoke lambda "{{cfn-output:ApplicationLoadBalancerTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBUrl}} |
      | path             | /invoke_lambda/trigger_error                            |
      | request_count    | 5                                                       |
      | request_interval | 1                                                       |
    And sleep for "60" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Report when count of lambda user errors from lambda targets is greater than or equal to a threshold - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | Subnet1Cidr                           |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                                       |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnet1Cidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                                       |

    When alarm "elb:alarm:application_lambda_user_error:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | LambdaTargetFullName                                                 | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>LambdaTargetFullName}}  | 1         | 1                 | 1                 |
    And invoke lambda "{{cfn-output:ApplicationLoadBalancerTemplate>ProxyLambdaArn}}" with parameters
      | host             | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBUrl}} |
      | path             | /invoke_lambda/trigger_error                            |
      | request_count    | 5                                                       |
      | request_interval | 1                                                       |
    And sleep for "60" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds


