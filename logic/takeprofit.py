import numpy
import talib
from logic import MarketTrend
from logic import Indicator, validate_datapoint
from logic.candle import Candle


class TakeProfit(Indicator):

    def __init__(self, atr_period_length=7):
        super(TakeProfit, self).__init__()
        self.period = atr_period_length
        self._high = []
        self._low = []
        self._close = []
        self.position_type = MarketTrend.ENTER_LONG
        self.current_takeprofit_price = 0.0
        self.state = MarketTrend.NO_STOP

    def GetState(self):
        return self.state

    def seen_enough_data(self):
        return self.period <= len(self._high)

    def AmountOfDataStillMissing(self):
        return max(0, self.period - len(self._high))

    def Tickerupdate(self, datapoint):
        if not validate_datapoint(datapoint):
            return

        # Check if it is time to do a stop loss trade
        if (self.current_takeprofit_price > 0.0):
            if (self.position_type == MarketTrend.ENTER_LONG):
                if (datapoint["value"] > self.current_takeprofit_price):
                    # Should sell Long position
                    self.state = MarketTrend.STOP_LONG
                    self.current_takeprofit_price = 0.0
            elif (self.position_type == MarketTrend.ENTER_SHORT):
                if (datapoint["value"] < self.current_takeprofit_price):
                    # Should buy back short position
                    self.state = MarketTrend.STOP_SHORT
                    self.current_takeprofit_price = 0.0

    def update(self, datapoint):

        if not isinstance(datapoint, Candle):
            self.Tickerupdate(datapoint)
            return

        self._high.append(datapoint.high)
        self._low.append(datapoint.low)
        self._close.append(datapoint.close)

        if (len(self._high) > self.period):
            self._close.pop(0)
            self._low.pop(0)
            self._high.pop(0)

    def SetTakeProfit(self, price, position_type=MarketTrend.ENTER_LONG):
        if (position_type != MarketTrend.ENTER_LONG and
                position_type != MarketTrend.ENTER_SHORT):
            return
        if (price <= 0.0):
            return
        self.position_type = position_type
        self.current_takeprofit_price = price
        self.state = MarketTrend.NO_STOP

    def GetPrice(self, position_type=MarketTrend.ENTER_LONG):

        if (not self.seen_enough_data()):
            return numpy.nan

        high = numpy.array(self._high, dtype=float)
        low = numpy.array(self._low, dtype=float)
        close = numpy.array(self._close, dtype=float)
        ATR = talib.ATR(high, low, close, timeperiod=self.period - 1)[-1]
        takeprofit_price = self._close[-1]

        if (position_type == MarketTrend.ENTER_LONG):
            takeprofit_price += 1.0 * ATR
        elif (position_type == MarketTrend.ENTER_SHORT):
            takeprofit_price -= 1.0 * ATR
        else:
            takeprofit_price = numpy.nan

        return takeprofit_price

    def CancelTakeProfit(self):
        self.state = MarketTrend.NO_STOP
        self.current_takeprofit_price = 0.0

    def IsSet(self):
        return self.current_takeprofit_price != 0.0
