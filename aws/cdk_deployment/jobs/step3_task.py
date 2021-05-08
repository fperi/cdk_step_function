from aws_cdk import aws_batch as batch
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import core


class Step3Task(core.Construct):
    @property
    def starting_point(self):
        return self._starting_point

    @property
    def ending_point(self):
        return self._ending_point

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        branch_name: str,
        queue: batch.IJobQueue,
        job_definition: batch.JobDefinition,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # state machine definition, this does exactly the same job as the defition
        # of step2 but it uses a CumstomState which takes a json as input. This allows
        # to use certain methods that are not available with the python CDK, like for
        # example States.Format('xxxxx-{}', $.parameters.test) will put $.parameters.test
        # inside the {}
        batch_map = sfn.CustomState(
            self,
            "csfeStep3Map",
            state_json={
                "Type": "Map",
                "MaxConcurrency": 0,
                "Parameters": {
                    "parameters.$": "$.parameters",
                    "step3_parameter.$": "$$.Map.Item.Value",
                },
                "ItemsPath": "$.parameters.step3_parameters",
                "Iterator": {
                    "StartAt": "csfeStep3Task",
                    "States": {
                        "csfeStep3Task": {
                            "Type": "Task",
                            "Resource": "arn:aws:states:::batch:submitJob.sync",
                            "Parameters": {
                                "JobDefinition": job_definition.job_definition_arn,
                                "JobName": f"csfe-{branch_name}-step3",
                                "JobQueue": queue.job_queue_arn,
                                "ContainerOverrides": {
                                    "Environment": [
                                        {
                                            "Name": "PARAMETER",
                                            "Value.$": "$.step3_parameter",
                                        }
                                    ],
                                },
                            },
                            "ResultPath": "$.resultData",
                            "End": True,
                        }
                    },
                },
                "OutputPath": "$.[0]",
            },
        )

        self._ending_point = batch_map
        self._starting_point = batch_map
