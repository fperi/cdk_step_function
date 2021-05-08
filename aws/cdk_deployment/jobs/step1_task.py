from aws_cdk import aws_batch as batch
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as sfn_tasks
from aws_cdk import core


class Step1Task(core.Construct):
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

        # task to submit an AWS Batch job from a job definition
        batch_task = sfn_tasks.BatchSubmitJob(
            self,
            "csfeStep1Task",
            job_name=f"csfe-{branch_name}-step1",
            job_definition=job_definition,
            job_queue=queue,
            integration_pattern=sfn.IntegrationPattern.RUN_JOB,
            container_overrides=sfn_tasks.BatchContainerOverrides(
                environment={
                    "PARAMETER": sfn.JsonPath.string_at("$.parameters.step1_parameter"),
                }
            ),  # passing the correct parameter to the container
            result_path="$.resultData",  # if not set the output of this step
            # will overwrite the input for step2
        )

        self._ending_point = batch_task
        self._starting_point = batch_task
