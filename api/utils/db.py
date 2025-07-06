import os

from datetime import datetime
from decimal import Decimal
from uuid import uuid4
import logging
from typing import Optional, List, Dict

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


def add_transaction(
    symbol: str,
    num_of_shares: int,
    amount: float,
    operation: str = 'BUY',
    currency: str = 'EUR'
) -> bool:
    # Validate operation
    if operation not in ('BUY', 'SELL'):
        logger.warning("Invalid operation: %s", operation)
        return False, None

    # Validate currency
    if currency not in ('USD', 'EUR'):
        logger.warning("Invalid currency: %s", currency)
        return False, None

    try:
        # Initialize DynamoDB (credentials loaded from environment or ~/.aws/credentials)
        dynamodb = boto3.resource('dynamodb',
                                  aws_access_key_id=AWS_ACCESS_KEY_ID, 
                                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY, 
                                  region_name='eu-north-1')
        table = dynamodb.Table('transactions_table')

        # Generate item
        date = datetime.today().strftime('%Y-%m-%d')
        item_id = f"{symbol}_{date.replace('-', '')}_{str(uuid4())[:8]}"

        item = {
            'id': item_id,
            'Symbol': symbol,
            'Operation': operation,
            'Num_of_Shares': num_of_shares,
            'Amount': Decimal(str(amount)),
            'Currency': currency,
            'Date': date
        }

        # Write to DynamoDB
        table.put_item(Item=item)
        # logger.info(item)
        logger.info("Transaction added: %s", item_id)
        return True, item

    except Exception as e:
        logger.error("Failed to add transaction: %s", str(e))
        return False, None


def get_finance_transactions(symbol: Optional[str] = None) -> List[Dict]:
    """
    Fetches transactions from the DynamoDB table.
    
    If `symbol` is provided, queries the 'SymbolIndex' GSI for matching transactions.
    If not provided, scans the entire table (use cautiously for large datasets).

    Parameters:
        symbol (str, optional): Stock symbol to filter by.

    Returns:
        List[Dict]: List of transaction items.
    """
    dynamodb = boto3.resource('dynamodb',
                          aws_access_key_id=AWS_ACCESS_KEY_ID, 
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY, 
                          region_name='eu-north-1')
    table = dynamodb.Table('transactions_table')

    try:
        items = []

        if symbol:
            # Query using GSI
            symbol = symbol.upper()
            logger.info(f"Querying transactions for symbol: {symbol}")
            response = table.query(
                IndexName='SymbolIndex',
                KeyConditionExpression=Key("Symbol").eq(symbol)
            )
            items.extend(response['Items'])

            # Handle pagination (if needed)
            while 'LastEvaluatedKey' in response:
                response = table.query(
                    IndexName='SymbolIndex',
                    KeyConditionExpression=Key("Symbol").eq(symbol),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                items.extend(response['Items'])
        else:
            # Full table scan (use with caution)
            logger.info("Scanning entire transactions table...")
            response = table.scan()
            items.extend(response['Items'])

            while 'LastEvaluatedKey' in response:
                response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
                items.extend(response['Items'])

        logger.info(f"Retrieved {len(items)} transaction(s).")
        items = [{k: float(v) if isinstance(v, Decimal) else v for k, v in x.items()} for x in items]
        return pd.DataFrame(items)

    except ClientError as e:
        logger.error(f"Error fetching transactions: {e.response['Error']['Message']}")
        return []