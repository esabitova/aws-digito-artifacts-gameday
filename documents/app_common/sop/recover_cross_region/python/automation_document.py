from adk.src.adk.builtin_steps.automation.execute_script.util.output_recovery_time import OutputRecoveryTime
from adk.src.adk.builtin_steps.automation.execute_script.util.record_start_time import RecordStartTime
from adk.src.adk.domain.branch_operation import Operation
from adk.src.adk.domain.choice import Choice
from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.input import Input
from adk.src.adk.parent_steps.abstract_automation_step import ResolveByName, AutomationStepReference
from adk.src.adk.parent_steps.automation.automation import Automation
from adk.src.adk.parent_steps.automation.branch_step import BranchStep
from adk.src.adk.parent_steps.automation.pause_step import PauseStep
from adk.src.adk.util.license import get_license


def link_document(name):
    return f"[{name}](https://us-west-2.console.aws.amazon.com/systems-manager/documents/{name})"


describe_cross_region_recovery_script = """

# Cross Region Application Recovery
This is a skeleton for a script for cross region application recovery. It is intended as a starting point for writing a
fully automated script.
This script is intended to be placed in the region you plan to recover to.
Out of the box it is a manual process that breaks down the recovery process into a set of common steps. Each step can
be replaced by an automation script fully automating the process.

### Overview of common steps for Cross Region Recovery
1. **Fence source region**

   Often you would want to make sure that the system in the Source Region is in a consistent known state before
   starting the recovery efforts in the failover region

   In systems that have a mutating state and a single primary region you want to avoid the possibility of a split brain.

2. **Recover state in failover Region**

   Per stateful system used by the app. Start the recovery process based on the plan:
   * Promote Replica to primary
   * Recover from Backup

3. **Scale up capacity in failover Region**

   Per stateless system used by the app. Execute the recovery process based on the plan:
   * Scale up aws services/resources as needed
   * Setup & Configure aws services/resources as needed

4. **Verification**

   Verify that the new system is running.

5. **Update DNS and other Global Services**

   Final updates maybe needed to global services to direct traffic to the new region

6. **Setup infrastructure for fail back to original region**

   Some systems may need additional setup to allow a future return to the source region when the original problem is
   fixed. (I.E. make sure changes in the new target system are properly replicated back to the old source region)

### Moving from Manual Process to Automatic

This initial script is just a skeleton that pauses at each step and waits for an engineer to complete it manually.

This document accepts an Input Parameter for each step.

To move to a fully automated script you will have to write an SSM Automation Document for each one of the steps.

We also publish SSM Automation Documents for common recovery processes (Recover from Snapshot / Promotion of Replica)
that can be used to help write these scripts.
"""

describe_fence_source_region = """
## Manually Fence the Source Region Nodes
Before the recovery processes can begin in the target region. You should make sure that the source region is in
a known controllable state.

The exact requirements will vary by app. Mostly we want to make sure that two things statements are true:
1. There are no ongoing transactions that can result in customer data loss
2. There are no recovery attempts in the source region that can lead to a split brain
"""

describe_recover_state = f"""
## Recover state in failover Region
For every system that holds state a recovery plan was created and is maintained.

* Systems that use a multi-region multi-writer setup may require no work
* Systems that use replication cross-region will need to promote the replica to primary
* Systems that use backups cross-region will need to recover from backup

Examples:
* EBS: {link_document("Digito-EBSRestoreFromBackup_2020-05-26")}
* EFS: {link_document("Digito-RestoreBackupInAnotherRegion_2020-10-26")}
* DynamoDb: {link_document("Digito-RestoreFromBackup_2020-04-01")}
* S3: {link_document("Digito-RestoreFromBackup_2020-09-21")}
* RDS: {link_document("Digito-RdsRestoreFromBackup_2020-04-01")}
* DocDb: {link_document("Digito-DocDbRestoreFromBackup_2020-09-21")}
"""


describe_scale_up = f"""
## Scale up Components
For every system/service the app uses has a recovery plan.

* System set up as full Active-Active may require no scale up
* System set up as pilot-light require scaling up tp full size
* The plan for some systems might be to build from scratch when needed

Examples:
* DynamoDb: {link_document("Digito-UpdateProvisionedCapacity_2020-04-01")}
* ASG: {link_document("Digito-ASG-ScaleOut_2020-07-01")}
* Lambda: {link_document("Digito-ChangeConcurrencyLimit_2020-10-26")}
* DocDb: {link_document("Digito-ScalingUp_2020-09-21")}
"""

describe_update_global = """
## Update DNS and other Global Services
Update the state of the fallback region and direct incoming traffic to it
"""

describe_verification = """
## Verification
Verify that the system is working in the new region.
"""

describe_fail_back = """
## Setup infra for fail back
In this step you would verify that the new region replicates its changes to the old source region.

This is critical to be able to revert back to the old source region in the future.
"""


def execute_doc_or_show_documentation(name: str,
                                      description: str,
                                      input_to_test: str,
                                      finish_on: AutomationStepReference):
    return [
        BranchStep(name,
                   choices=[Choice(constant="",
                                   input_to_test=input_to_test,
                                   operation=Operation.StringEquals,
                                   skip_to=ResolveByName(f"{name}_Describe"))],
                   default_step=ResolveByName(f"{name}_ExecuteAutomation")
                   ),
        Automation(step_name=f"{name}_ExecuteAutomation",
                   doc_name="{{" + input_to_test + "}}",
                   inputs=[
                       Input(name='AutomationAssumeRole', input_type=DataType.String, description="")
                   ],
                   steps=[PauseStep(name="Dummy", pause_runtime=False, description="")],
                   assume_role=""),
        BranchStep(f'{name}_SkipDescribe', choices=[
            Choice(constant="",
                   input_to_test=input_to_test,
                   operation=Operation.StringEquals,
                   skip_to=finish_on)
        ],
            default_step=finish_on),
        PauseStep(name=f"{name}_Describe", pause_runtime=False,
                  description=description),
    ]


def get_automation_doc():
    return Automation(
        step_name='Digito_AppCommonRecoverCrossRegion',
        doc_name='Digito-AppCommonRecoverCrossRegion_2021-04-01',
        doc_description=describe_cross_region_recovery_script,
        assume_role='AutomationAssumeRole',
        steps=[
            RecordStartTime(),
            *execute_doc_or_show_documentation(name="FenceSourceRegion",
                                               description=describe_fence_source_region,
                                               input_to_test="FenceSourceRegionAutomation",
                                               finish_on=ResolveByName("RecoverState")),
            *execute_doc_or_show_documentation(name="RecoverState",
                                               description=describe_recover_state,
                                               input_to_test="RecoverStateAutomation",
                                               finish_on=ResolveByName("ScaleUpComponents")),
            *execute_doc_or_show_documentation(name="ScaleUpComponents",
                                               description=describe_scale_up,
                                               input_to_test="ScaleUpComponentsAutomation",
                                               finish_on=ResolveByName("Verification")),
            *execute_doc_or_show_documentation(name="Verification",
                                               description=describe_verification,
                                               input_to_test="VerificationAutomation",
                                               finish_on=ResolveByName("UpdateGlobalServices")),
            *execute_doc_or_show_documentation(name="UpdateGlobalServices",
                                               description=describe_update_global,
                                               input_to_test="UpdateGlobalServicesAutomation",
                                               finish_on=ResolveByName("FailBack")),
            *execute_doc_or_show_documentation(name="FailBack",
                                               description=describe_fail_back,
                                               input_to_test="FailBackAutomation",
                                               finish_on=ResolveByName("OutputRecoveryTime")),

            OutputRecoveryTime(),

        ],
        inputs=[
            Input(name='FenceSourceRegionAutomation', input_type=DataType.String,
                  description='An Automation Document to fence the source region before recovery process is started. '
                              'If it is not provided the assumption is that the process will be done manually.',
                  default=''),

            Input(name='RecoverStateAutomation', input_type=DataType.String,
                  description='An Automation Document to recover state of all stateful components. '
                              'If it is not provided the assumption is that the process will be done manually.',
                  default=''),

            Input(name='ScaleUpComponentsAutomation', input_type=DataType.String,
                  description='An Automation to create/scale-up all necessary components in the target region. '
                              'If it is not provided the assumption is that the process will be done manually.',
                  default=''),

            Input(name='UpdateGlobalServicesAutomation', input_type=DataType.String,
                  description='An Automation Document to direct traffic to the service in the new region. '
                              'If it is not provided the assumption is that the process will be done manually.',
                  default=''),

            Input(name='VerificationAutomation', input_type=DataType.String,
                  description='An Automation Document to verify recovery.'
                              'If it is not provided the assumption is that the process will be done manually.',
                  default=''),
            Input(name='FailBackAutomation', input_type=DataType.String,
                  description='An Automation Document to setup any needed replication to allow future migration '
                              'back to original primary region'
                              'If it is not provided the assumption is that the process will be done manually.',
                  default=''),

            Input(name='AutomationAssumeRole', input_type=DataType.String,
                  description='(Required) The ARN of the role that allows Automation to perform '
                              'the actions on your behalf.')
        ],
        doc_outputs=[
            'OutputRecoveryTime.RecoveryTime'
        ],
        header=get_license()
    )
