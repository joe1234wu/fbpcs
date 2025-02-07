# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

# pyre-strict


import re
from typing import Dict, List, Pattern

INPUT_DATA_VALIDATOR_NAME = "Input Data Validator"
BINARY_FILE_VALIDATOR_NAME = "Binary File Validator"

INPUT_DATA_TMP_FILE_PATH = "/tmp"

ID_FIELD = "id_"
CONVERSION_VALUE_FIELD = "conversion_value"
CONVERSION_TIMESTAMP_FIELD = "conversion_timestamp"
CONVERSION_METADATA_FIELD = "conversion_metadata"
VALUE_FIELD = "value"
EVENT_TIMESTAMP_FIELD = "event_timestamp"

PA_FIELDS: List[str] = [
    ID_FIELD,
    CONVERSION_VALUE_FIELD,
    CONVERSION_TIMESTAMP_FIELD,
    CONVERSION_METADATA_FIELD,
]
PL_FIELDS: List[str] = [
    ID_FIELD,
    VALUE_FIELD,
    EVENT_TIMESTAMP_FIELD,
]
REQUIRED_FIELDS: List[str] = [
    ID_FIELD,
    EVENT_TIMESTAMP_FIELD,
    CONVERSION_TIMESTAMP_FIELD,
]
ALL_FIELDS: List[str] = [
    ID_FIELD,
    VALUE_FIELD,
    EVENT_TIMESTAMP_FIELD,
    CONVERSION_METADATA_FIELD,
    CONVERSION_VALUE_FIELD,
    CONVERSION_TIMESTAMP_FIELD,
]

INTEGER_REGEX: Pattern[str] = re.compile(r"^[0-9]+$")
TIMESTAMP_REGEX: Pattern[str] = re.compile(r"^[0-9]{10}$")
BASE64_REGEX: Pattern[str] = re.compile(r"^[A-Za-z0-9+/]+={0,2}$")

VALIDATION_REGEXES: Dict[str, Pattern[str]] = {
    ID_FIELD: BASE64_REGEX,
    CONVERSION_VALUE_FIELD: INTEGER_REGEX,
    CONVERSION_TIMESTAMP_FIELD: TIMESTAMP_REGEX,
    CONVERSION_METADATA_FIELD: INTEGER_REGEX,
    VALUE_FIELD: INTEGER_REGEX,
    EVENT_TIMESTAMP_FIELD: TIMESTAMP_REGEX,
}

VALID_LINE_ENDING_REGEX: Pattern[str] = re.compile(r".*(\S|\S\n)$")

BINARY_REPOSITORY = "https://one-docker-repository-prod.s3.us-west-2.amazonaws.com"
BINARY_PATHS = [
    "data_processing/attribution_id_combiner/latest/attribution_id_combiner",
    "data_processing/lift_id_combiner/latest/lift_id_combiner",
    "data_processing/pid_preparer/latest/pid_preparer",
    "data_processing/sharder_hashed_for_pid/latest/sharder_hashed_for_pid",
    "pid/private-id-client/latest/cross-psi-client",
    "pid/private-id-client/latest/cross-psi-xor-client",
    "pid/private-id-client/latest/private-id-client",
    "pid/private-id-server/latest/cross-psi-server",
    "pid/private-id-server/latest/cross-psi-xor-server",
    "pid/private-id-server/latest/private-id-server",
    "private_attribution/compute/latest/compute",
    "private_attribution/decoupled_aggregation/latest/decoupled_aggregation",
    "private_attribution/shard-aggregator/latest/shard-aggregator",
    "private_lift/lift/latest/lift",
]

ONEDOCKER_REPOSITORY_PATH = "ONEDOCKER_REPOSITORY_PATH"
