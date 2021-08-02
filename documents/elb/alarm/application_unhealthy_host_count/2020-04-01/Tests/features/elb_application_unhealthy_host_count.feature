@elb @integration @alarm
Feature: Alarm Setup - application load-balancer UnHealthyHostCount

  Scenario: Alarm is not triggered when count of application load balancer unhealthy hosts less than a threshold - green
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | Subnet1Cidr                           |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                                       |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnet1Cidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                                       |

    When alarm "elb:alarm:application_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | LambdaTargetFullName                                                   | ApplicationELBFullName                                                | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>UnhealthyTargetFullName}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | 1000      | 1                 | 1                 |
    And sleep for "60" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds

  Scenario: Report when count of application load balancer unhealthy hosts greater than or equal to a threshold - red
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | Subnet1Cidr                           |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                                       |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>PrivateSubnet1Cidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                                       |

    When alarm "elb:alarm:application_unhealthy_host_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | LambdaTargetFullName                                                   | ApplicationELBFullName                                                | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>UnhealthyTargetFullName}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | 1         | 1                 | 1                 |
    And sleep for "60" seconds
    Then assert metrics for all alarms are populated
    And wait until alarm {{alarm:under_test>AlarmName}} becomes ALARM within 180 seconds, check every 15 seconds


