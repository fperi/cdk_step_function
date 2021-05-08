from aws_cdk import aws_batch as batch
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import core
from cdk_deployment.jobs.step1_task import Step1Task
from cdk_deployment.jobs.step2_task import Step2Task
from cdk_deployment.jobs.step3_task import Step3Task


class MainStack(core.Stack):
    def __init__(
        self,
        scope: core.Construct,  # parent of this stack, usually an App
        id: str,  # a name for this stack
        ecr_repository_name: str,
        branch_name: str,
        account: str,
        region: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # the launch template contains the parameters to launch an host instance
        # AMIs available at
        # https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-optimized_AMI.html
        launch_template = ec2.CfnLaunchTemplate(
            self,
            "csfeLaunchTemplate",
            launch_template_name=f"csfe-{branch_name}-ec2-lt",
            launch_template_data=ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
                image_id="ami-096dbf55319e44970",  # optimised linux AMI for ECS
                # # the following adds more disk space
                # block_device_mappings=[
                #     ec2.CfnLaunchTemplate.BlockDeviceMappingProperty(
                #         device_name="/dev/xvda",
                #         ebs=ec2.CfnLaunchTemplate.EbsProperty(
                #             volume_size=300, volume_type="gp2",
                #         ),
                #     )
                # ],
            ),
        )

        # role for the following compute environment
        # this appears to be default for the task we need
        # https://github.com/aws-samples/aws-cdk-examples/pull/323/files
        batch_service_role = iam.Role(
            self,
            "csfeBatchServiceRole",
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSBatchServiceRole"
                )
            ],
        )

        # role for the following compute environment instance role
        # this appears to be default for the task we need
        batch_compute_role = iam.Role(
            self,
            "csfeBatchComputeRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"),
                iam.ServicePrincipal("ecs.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonECS_FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                ),
            ],
        )
        # If you use the AWS Management Console to create a role for Amazon EC2,
        # the console automatically creates an instance profile and gives
        # it the same name as the role. If you manage your roles from the AWS
        # CLI or the AWS API, you create roles and instance profiles as separate actions.
        # see https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html
        batch_compute_instance_profile = iam.CfnInstanceProfile(
            self,
            "csfeBatchInstanceProfile",
            instance_profile_name=f"csfe-{branch_name}-batch-ip",
            roles=[batch_compute_role.role_name],
        )

        # vpc for the following compute env instance role
        # setting up default vpc
        # no inward connections if not from the same vpc, all outwards connections
        vpc = ec2.Vpc.from_lookup(self, "csfeVpc", is_default=True)

        # compute environments contain the Amazon ECS container instances that
        # are used to run containerized batch jobs.
        # under instance_types we wouldn't need such big machines but the very small
        # ones are not supported by ecs
        compute_environment = batch.ComputeEnvironment(
            self,
            "csfeComputeEnvironment",
            compute_environment_name=f"csfe-{branch_name}-batch-ce",
            service_role=batch_service_role,  # defined above
            compute_resources=batch.ComputeResources(
                image=ec2.MachineImage.generic_linux(
                    {region: "ami-096dbf55319e44970"}  # match the ami above
                ),
                maxv_cpus=10,  # this is the total across all machines
                type=batch.ComputeResourceType.SPOT,  # spot are cheaper than on demand
                allocation_strategy=batch.AllocationStrategy.SPOT_CAPACITY_OPTIMIZED,
                launch_template=batch.LaunchTemplateSpecification(
                    launch_template_name=launch_template.launch_template_name,
                    version="$Latest",  # defined above
                ),
                minv_cpus=0,
                instance_role=batch_compute_instance_profile.instance_profile_name,
                instance_types=[
                    ec2.InstanceType("r4.large"),
                    ec2.InstanceType("r5.large"),
                ],
                desiredv_cpus=0,  # so that we don't keep stuff running if not needed
                vpc=vpc,  # defined above
            ),
        )

        # compute_environment cannot be created until the launch is there
        compute_environment.node.add_dependency(launch_template)

        # creating the job queue
        # jobs are submitted to a job queue where they reside until
        # they can be scheduled to run in a compute environment
        job_queue = batch.JobQueue(
            self,
            "csfeJobQueue",
            compute_environments=[
                batch.JobQueueComputeEnvironment(
                    compute_environment=compute_environment, order=1
                )  # defined above
            ],
            job_queue_name=f"csfe-{branch_name}-batch-jq",
            priority=100,
            enabled=True,
        )

        # retrieve ecr repo where our image is stored
        repo = ecr.Repository.from_repository_name(
            self, "csfeEcrRepo", ecr_repository_name
        )

        # job definitions specify how jobs are to be run
        batch_job = batch.JobDefinition(
            self,
            "csfeJobDef",
            job_definition_name=f"csfe-{branch_name}",
            container=batch.JobDefinitionContainer(
                image=ecs.EcrImage(repo, branch_name), memory_limit_mib=2000, vcpus=1,
            ),  # which image to use
            retry_attempts=1,
        )

        # tasks, these is where we define the tasks that will compose our step function
        step1_task = Step1Task(
            self,
            "step1Task",
            branch_name=branch_name,
            queue=job_queue,
            job_definition=batch_job,
        )

        step2_task = Step2Task(
            self,
            "step2Task",
            branch_name=branch_name,
            queue=job_queue,
            job_definition=batch_job,
        )

        step3_task = Step3Task(
            self,
            "step3Task",
            branch_name=branch_name,
            queue=job_queue,
            job_definition=batch_job,
        )

        # step function policies
        # these appears to be default for the task we need
        # https://docs.aws.amazon.com/step-functions/latest/dg/batch-job-notification.html
        step_function_policies = iam.PolicyDocument()
        step_function_policies.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["batch:SubmitJob", "batch:DescribeJobs", "batch:TerminateJob"],
                resources=["*"],
            )
        )
        step_function_policies.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["events:PutTargets", "events:PutRule", "events:DescribeRule"],
                resources=[
                    f"arn:aws:events:{region}:{account}:"
                    + "rule/StepFunctionsGetEventsForBatchJobsRule",
                ],
            )
        )
        step_function_policies.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                    "xray:GetSamplingRules",
                    "xray:GetSamplingTargets",
                ],
                resources=["*"],
            )
        )  # not really needed, helps developers analyze and debug

        # step function role
        step_function_role = iam.Role(
            self,
            "csfeJStepFunctionRole",
            role_name=f"csfe-{branch_name}-func",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies=[step_function_policies],  # defined above
        )

        # State machine definition
        # this is the logic (very simple) of the step function
        # step 1 followed by 2 followed by 3
        (step2_task.ending_point).next(step3_task.starting_point)
        (step1_task.ending_point).next(step2_task.starting_point)
        state_machine_def = step1_task.starting_point

        state_machine_name = f"csfe-{branch_name}-stepfunction"
        graph = sfn.StateGraph(
            state_machine_def.start_state,
            f"State Machine {state_machine_name} definition",
        )

        # render state machine
        sfn.CfnStateMachine(
            self,
            "csfeStateMachine",
            definition_string=core.Stack.of(self).to_json_string(graph.to_graph_json()),
            state_machine_name=state_machine_name,
            role_arn=step_function_role.role_arn,
        )
