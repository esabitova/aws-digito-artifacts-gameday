@elb @integration @alarm
Feature: Alarm Setup - load-balancer RejectedConnectionCount

  Scenario: Create elb:alarm:application_rejected_connection_count:2020-04-01 based on RejectedConnectionCount metric and check OK status
    Given the cloud formation templates as integration test resources
      | CfnTemplatePath                                                                | ResourceType | VPC                      | Subnet1                                            | Subnet2                                            | Subnet3                                              | VPCCidr                    |
      | resource_manager/cloud_formation_templates/shared/VPC.yml                      | SHARED       |                          |                                                    |                                                    |                                                      |                            |
      | resource_manager/cloud_formation_templates/ApplicationLoadBalancerTemplate.yml | ON_DEMAND    | {{cfn-output:VPC>VPCId}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetOne}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetTwo}} | {{cfn-output:VPC>PrivateSubnetWithoutInternetThree}} | {{cfn-output:VPC>VPCCidr}} |
      | resource_manager/cloud_formation_templates/shared/SnsForAlarms.yml             | SHARED       |                          |                                                    |                                                    |                                                      |                            |

    When alarm "elb:alarm:application_rejected_connection_count:2020-04-01" is installed
      | alarmId    | SNSTopicARN                       | ApplicationLoadBalancerName                                           | Threshold | EvaluationPeriods | DatapointsToAlarm |
      | under_test | {{cfn-output:SnsForAlarms>Topic}} | {{cfn-output:ApplicationLoadBalancerTemplate>ApplicationELBFullName}} | 1000      | 1                 | 1                 |
    # we couldn't trigger rejected connections, it looks like to reproduce this kind of issue, we have to
    # exceed the default connections per second limit for load balancer = 20000
    # so datapoints couldn't be generated
    # https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html
    Then wait until alarm {{alarm:under_test>AlarmName}} becomes OK within 180 seconds, check every 15 seconds
