# Failover RDS Cluster

## Notes

Failover an RDS cluster if it is not already failing-over. Wait for the cluster status to become available afterwards.


## Document Design

Refer to schema.json

Document Steps:
1. aws:waitForAwsResourceProperty - Wait for the cluster statue to become available if needed
   * Inputs:
     * DBClusterIdentifier: {{ClusterId}} - the RDS cluster Id
2. aws:branch - Branch to either default fail-over or fail-over with primary specified
3. aws:executeAwsApi - Fail-over with primary specified
      * Inputs:
        * DBClusterIdentifier: {{ClusterId}} - the Aurora cluster Id
        * TargetDBInstanceIdentifier: '{{InstanceId}}' - the DB instance to promote to the primary instance
4. aws:executeAwsApi - Default fail-over
      * Inputs:
        * DBClusterIdentifier: {{ClusterId}} - the Aurora cluster Id
5. aws:waitForAwsResourceProperty - Wait for the cluster to become available
   * Inputs:
     * DBClusterIdentifier: {{ClusterId}} - the RDS cluster Id

## Test script
Python script will:
  1. Create a test stack with an automation assumed role and a Aurora cluster. Create Digito-AuroraFailoverCluster document in SSM.
  2. Run Aurora fail-over SSM document with cluster Id, and verify that fail-over happens
  3. Run Aurora fail-over SSM document with cluster Id and instance Id, and verify that the specified instance becomes primary.
  4. Clean up Digito-AuroraFailoverCluster document in SSM and delete test stack.