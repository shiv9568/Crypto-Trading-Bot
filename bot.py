import os
import argparse
import sys
from dotenv import load_dotenv
import logging
from typing import Optional, Literal, Union

from trader import BasicBot, OrderSide, OrderType
from logging_config import setup_logging

load_dotenv()
LOG_FILE = setup_logging()
logger = logging.getLogger(__name__)

def validate_input(
    symbol: str, 
    side: str, 
    order_type: str, 
    quantity: str, 
    price: Optional[str], 
    stop_price: Optional[str] = None
) -> Optional[tuple[str, OrderSide, OrderType, float, Optional[float], Optional[float]]]:
    
    side_upper = side.upper()
    order_type_upper = order_type.upper()

    try:
        q = float(quantity)
        if q <= 0:
            raise ValueError()
    except ValueError:
        logger.error(f"Invalid quantity: {quantity}. Must be a positive number.")
        return None

    p: Optional[float] = None
    if order_type_upper in ['LIMIT', 'STOP_LIMIT']:
        if price is None:
            logger.error(f"{order_type_upper} order requires a --price.")
            return None
        try:
            p = float(price)
            if p <= 0:
                raise ValueError()
        except ValueError:
            logger.error(f"Invalid price: {price}. Must be a positive number.")
            return None

    sp: Optional[float] = None
    if order_type_upper == 'STOP_LIMIT':
        if stop_price is None:
            logger.error("STOP_LIMIT order requires a --stop-price.")
            return None
        try:
            sp = float(stop_price)
            if sp <= 0:
                raise ValueError()
            if p is not None and (sp > p and side_upper == 'SELL'):
                logger.warning("Stop Price > Limit Price for a SELL order (may trigger immediately).")
            elif p is not None and (sp < p and side_upper == 'BUY'):
                logger.warning("Stop Price < Limit Price for a BUY order (may trigger immediately).")
        except ValueError:
            logger.error(f"Invalid stop-price: {stop_price}. Must be a positive number.")
            return None
            
    return (
        symbol.upper().replace("/", ""), 
        side_upper, 
        order_type_upper,
        q, 
        p, 
        sp
    )


def main():
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')

    if not api_key or not api_secret:
        logger.critical("API Key or Secret not found in .env file. Exiting.")
        sys.exit("ERROR: Please set BINANCE_API_KEY and BINANCE_API_SECRET in your .env file.")
    
    try:
        bot = BasicBot(api_key=api_key, api_secret=api_secret, testnet=True)
    except Exception:
        logger.critical("Bot initialization failed. Exiting.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="A Simplified Trading Bot for Binance Futures Testnet.",
        epilog=f"\n*** Log files for submission are saved to '{LOG_FILE}'. ***"
    )
    
    parser.add_argument(
        'symbol', 
        type=str, 
        help="Trading pair (e.g., BTCUSDT)"
    )
    parser.add_argument(
        'side', 
        type=str, 
        choices=['BUY', 'SELL'], 
        help="Order side (BUY or SELL)"
    )
    parser.add_argument(
        'order_type', 
        type=str, 
        choices=['MARKET', 'LIMIT', 'STOP_LIMIT'], 
        help="Order type (MARKET, LIMIT, or STOP_LIMIT - bonus)"
    )
    parser.add_argument(
        'quantity', 
        type=str, 
        help="Quantity to trade (e.g., 0.001)"
    )
    parser.add_argument(
        '--price', 
        type=str, 
        default=None, 
        help="Limit price (required for LIMIT and STOP_LIMIT orders)"
    )
    parser.add_argument(
        '--stop-price', 
        type=str, 
        default=None, 
        help="Stop price (required for STOP_LIMIT orders - bonus)"
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    validated = validate_input(
        args.symbol, args.side, args.order_type, args.quantity, args.price, args.stop_price
    )

    if validated is None:
        logger.error("Order processing halted due to invalid input.")
        sys.exit(1)

    symbol, side, order_type, quantity, price, stop_price = validated
    
    print(f"\n--- Attempting to place a {order_type} {side} order for {quantity} {symbol} ---")
    
    order_result: Optional[dict] = None
    
    if order_type == 'MARKET':
        order_result = bot.place_market_order(symbol, side, quantity)
        
    elif order_type == 'LIMIT':
        order_result = bot.place_limit_order(symbol, side, quantity, price=price)
        
    elif order_type == 'STOP_LIMIT':
        order_result = bot.place_stop_limit_order(
            symbol, side, quantity, price=price, stop_price=stop_price
        )

    print("\n--- Execution Status ---")
    if order_result:
        status = order_result.get('status', 'N/A')
        print(f"STATUS: {status}")
        print(f"SYMBOL: {order_result.get('symbol', 'N/A')}")
        print(f"ORDER ID: {order_result.get('orderId', 'N/A')}")
        
        if status in ['NEW', 'PENDING_NEW']:
            print(f"TYPE: {order_result.get('type', 'N/A')}")
            print(f"PRICE: {order_result.get('price', 'N/A')}")
        elif status in ['FILLED', 'PARTIALLY_FILLED']:
            print(f"AVG FILL PRICE: {order_result.get('avgPrice', 'N/A')}")
        
        logger.info(f"Final Order Status Output: {order_result}")
    else:
        print("STATUS: FAILED (Check log file for detailed error message)")
    
    print("-" * 30)
    print(f"Details saved in the log file: {LOG_FILE}")


if __name__ == '__main__':
    main()