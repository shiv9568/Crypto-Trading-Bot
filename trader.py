import logging
from typing import Literal, Optional, Any

from binance.client import Client 
from binance.exceptions import BinanceAPIException, BinanceRequestException

logger = logging.getLogger(__name__)


OrderSide = Literal['BUY', 'SELL']
OrderType = Literal['MARKET', 'LIMIT', 'STOP_LIMIT']
TimeInForce = Literal['GTC', 'IOC', 'FOK']


TESTNET_URL = 'https://testnet.binancefuture.com'

class BasicBot:
    """
    Simplified Trading Bot for Binance Futures Testnet (USDT-M).
    Uses the standard Client but targets the Futures Testnet URL.
    """
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """Initializes the Binance Client for Futures."""
        
        logger.info(f"Initializing BasicBot. Testnet mode: {testnet}")
        self.testnet = testnet
        
        try:
           
            # This is the most robust way to target Futures without the specific module import
            self.client = Client(
                api_key, 
                api_secret, 
                tld='com',
              
                base_url=TESTNET_URL
            )
            
            
            self.client.futures_exchange_info()
            logger.info(f"Binance Client initialized and connected to Testnet URL: {TESTNET_URL}")
        except Exception as e:
            
            
            logger.error(f"Failed to initialize Binance Client. Check API keys and network: {e}")
            raise 

    def get_market_price(self, symbol: str) -> Optional[float]:
        """Fetches the current market price for a symbol using futures method."""
        try:
            
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            logger.info(f"Market price for {symbol}: {price}")
            return price
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Error fetching market price for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None


    def place_order(
        self, 
        symbol: str, 
        side: OrderSide, 
        order_type: OrderType, 
        quantity: float, 
        price: Optional[float] = None, 
        time_in_force: Optional[TimeInForce] = 'GTC',
        stop_price: Optional[float] = None
    ) -> Optional[dict]:
        """
        Places a new order on Binance Futures Testnet using the futures-specific method.
        """
        
        params: dict[str, Any] = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
        }

        if order_type == 'LIMIT' and price is not None:
            params['price'] = price 
            params['timeInForce'] = time_in_force
        
        if order_type == 'STOP_LIMIT' and price and stop_price:
            params['price'] = price
            params['stopPrice'] = stop_price
            params['timeInForce'] = time_in_force

        logger.info(f"Attempting to place {order_type} order. Request parameters: {params}")

        try:
            
            response = self.client.futures_create_order(**params)
            
            logger.info(f"Order placed successfully. Response: {response}")
            return response

        except BinanceAPIException as e:
            logger.error(f"Binance API Error placing order (Code {e.code}): {e.message}. Request: {params}")
            print(f"FAILED (API Error): Code {e.code} | {e.message}")
            return None
            
        except Exception as e:
            logger.error(f"An unexpected error occurred while placing order: {e}. Request: {params}")
            print(f"FAILED (Unknown Error): {e}")
            return None

    

    def place_market_order(self, symbol: str, side: OrderSide, quantity: float):
        """Places a MARKET order."""
        return self.place_order(symbol, side, 'MARKET', quantity)

    def place_limit_order(self, symbol: str, side: OrderSide, quantity: float, price: float):
        """Places a LIMIT order."""
        return self.place_order(symbol, side, 'LIMIT', quantity, price=price)

    def place_stop_limit_order(self, symbol: str, side: OrderSide, quantity: float, price: float, stop_price: float):
        """Places a STOP_LIMIT order (Bonus)."""
        return self.place_order(
            symbol, side, 'STOP_LIMIT', quantity, 
            price=price, 
            stop_price=stop_price
        )