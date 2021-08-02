from adk.src.adk.builtin_steps.automation.aws_api.ebs_repo import \
    ebs_describe_instance_volume, ebs_describe_volume, resize_volume
from adk.src.adk.builtin_steps.automation.execute_script.util.output_recovery_time import OutputRecoveryTime
from adk.src.adk.builtin_steps.automation.execute_script.util.record_start_time import RecordStartTime
from adk.src.adk.builtin_steps.automation.run_commands import run_shell_script
from adk.src.adk.domain.branch_operation import Operation
from adk.src.adk.domain.choice import Choice
from adk.src.adk.domain.data_type import DataType
from adk.src.adk.domain.input import Input
from adk.src.adk.parent_steps.abstract_automation_step import ResolveByName
from adk.src.adk.parent_steps.automation.automation import Automation
from adk.src.adk.parent_steps.automation.branch_step import BranchStep
from adk.src.adk.util.license import get_license
from documents.ebs.sop.increase_volume_size.python.check_larger_volume import CheckLargerVolume
from documents.ebs.sop.increase_volume_size.python.wait_for_volume_size import WaitForVolumeSize


def get_automation_doc():
    return Automation(
        step_name='Digito_EBSRestoreFromBackup_2020_05_26',
        doc_name='Digito-EbsIncreaseVolumeSize_2020-05-26',
        assume_role='AutomationAssumeRole',
        steps=[
            RecordStartTime(),
            ebs_describe_instance_volume(),
            ebs_describe_volume(),
            CheckLargerVolume(),
            BranchStep('SizeValidationBranch', choices=[
                Choice(constant=True, input_to_test='CheckLargerVolume.VolumeAlreadyGreater',
                       operation=Operation.BooleanEquals,
                       skip_to=ResolveByName('OutputRecoveryTime'))
            ]),
            resize_volume(),
            WaitForVolumeSize(),
            run_shell_script(
                commands=[
                    "originalsize=`df -h | grep {{ DeviceName }} | awk -F ' ' '{print $2}'`",
                    'echo "Original volume size: ${originalsize}"',
                    "sudo growpart {{ DeviceName }} {{ Partition }}",
                    "mntpt=`df -h | grep {{ DeviceName }} | grep -oE '[^ ]+$'`",
                    "sudo xfs_growfs -d ${mntpt} || sudo resize2fs {{ DeviceName }}{{ Partition }}",
                    'echo "Resize completed"',
                    "volsize=`df -h | grep {{ DeviceName }} | awk -F ' ' '{print $2}'`",
                    'echo "New volume size: ${volsize}"',
                    "[ ${volsize} != ${originalsize} ] 2>/dev/null"
                ],
                instance_ids_input='InstanceIdentifier'),
            OutputRecoveryTime()
        ],
        inputs=[
            Input(name='SizeGib', input_type=DataType.Integer,
                  description='(Required) The target size to increase the volume to (in GiB)'),
            Input(name='InstanceIdentifier', input_type=DataType.String,
                  description='(Required) The identifier of the instance requiring increase of volume size'),
            Input(name='DeviceName', input_type=DataType.String,
                  description='(Required) The device name (such as /dev/sdh) is to be increased'),
            Input(name='Partition', input_type=DataType.String,
                  description='(Required) The partition which is to be increased'),
            Input(name='AutomationAssumeRole', input_type=DataType.String,
                  description='(Required) The ARN of the role that allows Automation to perform '
                              'the actions on your behalf.')
        ],
        doc_outputs=['OutputRecoveryTime.RecoveryTime'],
        header=get_license()
    )
