# SSM Automation Development Kit

This module provides a mechanism to write SSM Automation Documents completely as code.

The same python SSM declaration can be used to both:
1. Generate the SSM Automation YAML
2. Simulate the automation locally (run/test/debug)

## Getting Started

Create an SSM document by initializing the parent_steps.automation.Automation.

The constructor takes in a list of steps. You can leverage one of the existing 8 parent_steps to build SSM.

## Sample

Here is a sample SSM document using a variety of steps:

```python
def sample_ssm() -> Automation:
    final_step = SleepStep(sleep_seconds=1)
    return Automation(inputs=[
            Input(name="InstanceId", input_type=DataType.String, description="Your instance id"),
            Input(name="AutomationAssumeRole", input_type=DataType.String, description="The role to assume"),
            Input(name="DryRun", input_type=DataType.Boolean, description="Dryrun indication")
    ],
        assume_role="AutomationAssumeRole",
        steps=[
            Ec2DescribeInstances(),
            BranchStep(name="BranchForSomething", skip_forward_step=final_step, input_to_test='DryRun'),
            SampleStep().max_attempts(3),
            WaitForInstanceStart(),
            another_ssm(),
            final_step
        ],
        name="SampleStep")
``` 
The first step is an aws:executeAwsApi SSM step. 
As you would expect the outputs from that step are available in the subsequent steps.

The next step is an aws:branch step which branches execution based on the 'input_to_test'.
If the input_to_test is True then the execution will skip forward to the 'skip_forward_step'.
Otherwise the execution will continue with the subsequent step (SampleStep in this case).

You can see the documentation for each of the supported steps in the python code documentation under parent_steps.

### Execution

#### Simulation

Once you have an Automation instance, you can simulate the automation with:
`automation.invoke({'invocation_key', 'invocation_value'})` 
The response is fed through the same input param so declare that dict outside so that you have a handle to it.

You can use the simulation to test your automation.

Take a look at an example test of an ssm automation where we mock out EC2 calls and run the automation:
 `test/adk/steps/test_demo_runner.py`
 
You can also run the simulator without mocking out external calls and letting the automation hit your AWS resources
using local AWS credentials.
(This of course should not be committed to version control, but is a very effective way at testing the automation.)

#### Yaml Generation

You can build the yaml of the Automation instance using:
`automation.get_automation_yaml()`

See an example of the generated yaml in `test/adk/steps/test_demo_yaml.py`

You can deploy that yaml to SSM as is.
(We will provide more tooling for this in the future.)

## Steps

On every step instance, you can modify the `timeout_seconds`, `max_attempts`, `is_end`, `on_cancel` and `on_failure`.
For example: `my_step.max_attempts(4)` etc.
The steps should therefore not be referenced as singletons
(if you use the same step in different automations documents, create a new instance)

### Step Options

`OnFailure, OnCancel, MaxAttempts, TimeoutSeconds` are all supported in simulation as per a real SSM run.

If you reference an `on_failure` step, the failure step will be invoked if any exception is thrown
(aside from CancellationException).

If you reference an `on_cancel` step, the failure step will be invoked if a CancellationException is thrown.

If execution fails with an exception, the execution will be retried up to the `max_attempt`s configured.

If the execution takes longer than is specified by `timeout_seconds` the simulation will
raise an exception AFTER the function returns. (Execution will not be killed during execution of a step.) 

### Implementing a New Step Type

You can subclass `Step` to create a new type of step (if there is an action that is not yet supported
(we currently have 8 supported actions)).

You must implement the `execute_step()` for the python simulation as well as `get_yaml()` which will return the yaml. 

You can add step validation specific to the action by implementing `validations()`
(be sure to call super().validations() first) 

## Testing

Any new step type that is added should have a unit test (as there is for the existing 8 step types).
Be sure to test the `execute_step()` function of the new step type as well as the `get_yaml()` function.
(See examples in `test/adk/steps`).
Also important to ensure that the new step type runs successfully in an uploaded SSM doc.

If you are instantiating an existing step (SleepStep or WaitForResourceStep)
there is not much need to test that since the implementation of the class is already covered by test.

Every automation document should have a test that verifies its behavior.
The mechanism for doing this is described above in the Simulation section. 
