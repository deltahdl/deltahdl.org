"""Mock utilities for boto3/botocore testing."""
from typing import Any, Callable
from unittest.mock import MagicMock

from botocore.exceptions import ClientError


def create_client_error(
    error_code: str,
    operation_name: str = 'TestOperation'
) -> ClientError:
    """Create a ClientError for testing error handling.

    Args:
        error_code: AWS error code (e.g., 'ResourceNotFoundException').
        operation_name: Name of the AWS operation that failed.

    Returns:
        ClientError exception with the specified error code.
    """
    return ClientError(
        {
            'Error': {
                'Code': error_code,
                'Message': f'Test error: {error_code}'
            },
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 400,
                'HTTPHeaders': {},
                'RetryAttempts': 0,
                'HostId': ''
            }
        },
        operation_name
    )


def create_boto_client_mock(**service_mocks: Any) -> Callable:
    """Create a boto3 client mock with configurable service mocks.

    Args:
        **service_mocks: Mapping of service names to mock objects.

    Returns:
        Function suitable for use as boto3.client side_effect.
    """
    def mock_client(service_name: str) -> Any:
        return service_mocks.get(service_name, MagicMock())

    return mock_client
