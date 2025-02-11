#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.


import json
import logging
from datetime import datetime, timezone
from typing import Type, Optional, Dict, Any

import dateutil.parser
from fbpcs.pl_coordinator.pl_graphapi_utils import (
    PLGraphAPIClient,
)
from fbpcs.pl_coordinator.pl_instance_runner import (
    run_instance,
)
from fbpcs.private_computation.entity.private_computation_instance import (
    AttributionRule,
    AggregationType,
    PrivateComputationGameType,
)
from fbpcs.private_computation.entity.private_computation_status import (
    PrivateComputationInstanceStatus,
)
from fbpcs.private_computation.stage_flows.private_computation_base_stage_flow import (
    PrivateComputationBaseStageFlow,
)


class LoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger: logging.Logger, prefix: str) -> None:
        super(LoggerAdapter, self).__init__(logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        return "[%s] %s" % (self.prefix, msg), kwargs


# dataset information fields
AD_OBJECT_ID = "ad_object_id"
TARGET_OBJECT_TYPE = "target_object_type"
DATASETS_INFORMATION = "datasets_information"
INSTANCES = "instances"
NUM_SHARDS = "num_shards"
NUM_CONTAINERS = "num_containers"

# instance fields
TIMESTAMP = "timestamp"
ATTRIBUTION_RULE = "attribution_rule"
STATUS = "status"

"""
The input to this function will be the input path, the dataset_id as well as the following params to choose
a specific dataset range to create and run a PA instance on
1) start_date - start date of the FB Opportunity data
2) end_date - end date of the FB Opportunity data
3) attribution_rule - attribution rule for the selected data
4) result_type - result type for the selected data
"""


def run_attribution(
    config: Dict[str, Any],
    dataset_id: str,
    input_path: str,
    timestamp: str,
    attribution_rule: AttributionRule,
    aggregation_type: AggregationType,
    concurrency: int,
    num_files_per_mpc_container: int,
    k_anonymity_threshold: int,
    stage_flow: Type[PrivateComputationBaseStageFlow],
    logger: logging.Logger,
    num_tries: Optional[int] = 2,  # this is number of tries per stage
) -> None:

    ## Step 1: Validation. Function arguments and  for private attribution run.
    # obtain the values in the dataset info vector.
    client = PLGraphAPIClient(config["graphapi"]["access_token"], logger)
    datasets_info = _get_attribution_dataset_info(client, dataset_id, logger)
    datasets = datasets_info[DATASETS_INFORMATION]
    matched_data = {}
    attribution_rule_str = attribution_rule.name
    attribution_rule_val = attribution_rule.value
    instance_id = None

    # Validate if input is datetime or timestamp
    is_date_format = _iso_date_validator(timestamp)
    if is_date_format:
        dt = datetime.fromisoformat(timestamp)
    else:
        dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    print(dt)
    return

    dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    # Verify that input has matching dataset info:
    # a. attribution rule
    # b. timestamp
    if len(datasets) == 0:
        raise ValueError("Dataset for given parameters and dataset invalid")
    for data in datasets:
        if data["key"] == attribution_rule_str:
            matched_attr = data["value"]

    for m_data in matched_attr:
        m_time = dateutil.parser.parse(m_data[TIMESTAMP])
        if m_time == dt:
            matched_data = m_data
            break
    if len(matched_data) == 0:
        raise ValueError("No dataset matching to the information provided")

    # Step 2: Validate what instances need to be created vs what already exist
    dataset_instance_data = _get_existing_pa_instances(client, dataset_id)
    existing_instances = dataset_instance_data["data"]
    for inst in existing_instances:
        inst_time = dateutil.parser.parse(inst[TIMESTAMP])
        print(inst[STATUS])
        if (
            inst[ATTRIBUTION_RULE] == attribution_rule_val
            and inst_time == dt
            and inst[STATUS]
            != PrivateComputationInstanceStatus.POST_PROCESSING_HANDLERS_COMPLETED
        ):
            instance_id = inst["id"]
            break

    if instance_id is None:
        instance_id = _create_new_instance(
            dataset_id,
            int(timestamp),
            attribution_rule_val,
            client,
            logger,
        )

    instance_data = _get_pa_instance_info(client, instance_id, logger)
    num_pid_containers = instance_data[NUM_CONTAINERS]
    num_mpc_containers = instance_data[NUM_SHARDS]

    ## Step 3. Run Instances. Run maximum number of instances in parallel
    logger.info(f"Start running instance {instance_id}.")
    run_instance(
        config,
        instance_id,
        input_path,
        num_pid_containers,
        num_mpc_containers,
        stage_flow,
        logger,
        PrivateComputationGameType.ATTRIBUTION,
        attribution_rule,
        AggregationType.MEASUREMENT,
        concurrency,
        num_files_per_mpc_container,
        k_anonymity_threshold,
        num_tries,
    )
    logger.info(f"Finished running instances {instance_id}.")


def _create_new_instance(
    dataset_id: str,
    timestamp: int,
    attribution_rule: str,
    client: PLGraphAPIClient,
    logger: logging.Logger,
) -> str:
    instance_id = json.loads(
        client.create_pa_instance(
            dataset_id,
            timestamp,
            attribution_rule,
            2,
        ).text
    )["id"]
    logger.info(
        f"Created instance {instance_id} for dataset {dataset_id} and attribution rule {attribution_rule}"
    )
    return instance_id


def get_attribution_dataset_info(
    config: Dict[str, Any], dataset_id: str, logger: logging.Logger
) -> str:
    client = PLGraphAPIClient(config["graphapi"]["access_token"], logger)

    return json.loads(
        client.get_attribution_dataset_info(
            dataset_id,
            [AD_OBJECT_ID, TARGET_OBJECT_TYPE, DATASETS_INFORMATION],
        ).text
    )


def _get_pa_instance_info(
    client: PLGraphAPIClient, instance_id: str, logger: logging.Logger
) -> Any:
    return json.loads(client.get_instance(instance_id).text)


def _iso_date_validator(timestamp: str) -> Any:
    try:
        datetime.strptime(timestamp, "%Y-%m-%d")
        return True
    except Exception:
        pass
    else:
        return False


def _get_attribution_dataset_info(
    client: PLGraphAPIClient, dataset_id: str, logger: logging.Logger
) -> Any:
    return json.loads(
        client.get_attribution_dataset_info(
            dataset_id,
            [AD_OBJECT_ID, TARGET_OBJECT_TYPE, DATASETS_INFORMATION],
        ).text
    )


def _get_existing_pa_instances(client: PLGraphAPIClient, dataset_id: str) -> Any:
    return json.loads(client.get_existing_pa_instances(dataset_id).text)
