from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.input import Input
from adk.src.adk.parent_steps.automation import Automation
from adk.src.adk.steps.execute_script.ebs.calculate_iops_and_vol_type import CalculateIopsAndVolType
from adk.src.adk.steps.execute_script.ebs.create_ebs_volume import CreateEbsVolume
from adk.src.adk.steps.execute_script.ebs.ebs_describe_snapshot import EbsDescribeSnapshot
from adk.src.adk.steps.util_repo import get_output_recovery_time, get_record_start_time_step
from adk.src.adk.steps.wait_for_resource.ebs_repo import get_wait_for_volume_start
from adk.src.adk.util.license import get_license


def get_automation_doc():
    return Automation(
        name='Digito-EBSRestoreFromBackup_2020-05-26',
        assume_role='AutomationAssumeRole',
        steps=[
            get_record_start_time_step(),
            EbsDescribeSnapshot(),
            CalculateIopsAndVolType(),
            CreateEbsVolume(),
            get_wait_for_volume_start(),
            get_output_recovery_time(),

        ],
        inputs=[
            Input(name='EBSSnapshotIdentifier', input_type=DataType.String,
                  description='(Required) The identifier of the snapshot to restore'),
            Input(name='TargetAvailabilityZone', input_type=DataType.String,
                  description='(Required) Availability Zone in which to create the volume'),
            Input(name='VolumeType', input_type=DataType.String, default='',
                  description='(Optional) The Volume Type. (If omitted the default would be gp2)'),
            Input(name='VolumeIOPS', input_type=DataType.Integer, default=0,
                  description='(Optional) The number of I/O operations per second (IOPS). Not used for gp2. '
                              'Setting at 0 will use default value.'),
            Input(name='AutomationAssumeRole', input_type=DataType.String,
                  description='(Required) The ARN of the role that allows Automation to perform '
                              'the actions on your behalf.')
        ],
        doc_outputs=['CreateEbsVolume.CreatedVolumeId',
                     'OutputRecoveryTime.RecoveryTime',
                     'EbsDescribeSnapshot.RecoveryPoint'],
        header=get_license()
    )
