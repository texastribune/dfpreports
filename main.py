"""
references:
https://github.com/googleads/googleads-python-lib/blob/master/examples/adspygoogle/dfp/v201311/order_service/get_orders_by_statement.py
"""
import datetime
import logging
import os

from adspygoogle.dfp.DfpClient import DfpClient
import pytz


HOME = os.path.expanduser('~')


class Order(object):
    """
    advertiserId: str(int) ex: '12345'
    creatorId: str(int) ex: '12345'
    currencyCode: str ex: 'USD'
    endDateTime: datetime
    externalOrderId: str(int) ex: '0'
    id: str(int) ex: '12345'
    isArchived: bool
    lastModifiedByApp: str ex: 'Goog_DFPUI'
    lastModifiedDateTime: datetime
    name: str ex: '1 for All Campaign'
    notes: str
    poNumber
    startDateTime: datetime
    status:
    totalBudget:
        currencyCode: 'USD'
        microAmount: '0'
    totalClicksDelivered: int
    totalImpressionsDelivered: int
    traffickerId: str(int)
    unlimitedEndDateTime: bool

    """
    def __init__(self, order_data):
        self._original_data = order_data  # hang onto the original data
        self.__dict__ = order_data.copy()

        # begin type conversions

        # bool
        self.isArchived = self.isArchived == 'true'
        self.unlimitedEndDateTime = self.unlimitedEndDateTime == 'true'

        # int
        self.totalClicksDelivered = int(order_data['totalClicksDelivered'])
        self.totalImpressionsDelivered = int(order_data['totalImpressionsDelivered'])

        # datetimes
        if 'endDateTime' in order_data:
            self.endDateTime = self.to_datetime(order_data['endDateTime'])
        self.lastModifiedDateTime = self.to_datetime(order_data['lastModifiedDateTime'])
        self.startDateTime = self.to_datetime(order_data['startDateTime'])

    def __repr__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.name.encode('utf8')

    # utilities
    def to_datetime(self, data):
        try:
            tz = pytz.timezone('timeZoneID')
        except pytz.UnknownTimeZoneError as e:
            logger = logging.getLogger(__name__)
            logger.warn(e)
            tz = None
        timetuple = (data['date']['year'], data['date']['month'], data['date']['day'], data['hour'], data['minute'], data['second'])
        timetuple = map(int, timetuple)
        return datetime.datetime(*timetuple, tzinfo=tz)


if __name__ == '__main__':
    client = DfpClient(path=HOME)

    # https://developers.google.com/doubleclick-publishers/docs/reference/v201311/OrderService#getOrdersByStatement
    inventory_service = client.GetService('OrderService', version='v201311')

    today = datetime.date.today()
    then = datetime.date.today() + datetime.timedelta(days=7)
    values = [
        {
            'key': 'today',
            'value': {
                'xsi_type': 'TextValue',
                'value': today.strftime('%Y-%m-%dT%H:%M:%S')
            }
        },
        {
            'key': 'then',
            'value': {
                'xsi_type': 'TextValue',
                'value': then.strftime('%Y-%m-%dT%H:%M:%S')
            }
        },
    ]
    filter_statement = {
        'query': ('WHERE endDateTime >= :today AND endDateTime < :then LIMIT 500'),
        'values': values,
    }
    results = inventory_service.GetOrdersByStatement(filter_statement)[0]['results']
    orders = [Order(x) for x in results]
