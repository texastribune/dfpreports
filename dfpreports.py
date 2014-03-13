"""
references:
https://github.com/googleads/googleads-python-lib/blob/master/examples/adspygoogle/dfp/v201311/order_service/get_orders_by_statement.py
"""
import datetime
import logging
import os

from googleads import dfp, oauth2
from csvkit.unicsv import UnicodeCSVDictWriter
from project_runpy import env, ColorizingStreamHandler
import pytz


HOME = os.path.expanduser('~')


logger = logging.getLogger(__name__)
# logger.addHandler(logging.StreamHandler())
logger.addHandler(ColorizingStreamHandler())


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

    @property
    def admin_url(self):
        # XXX global: `network`
        return ('https://www.google.com/dfp/{}#delivery/OrderDetail/orderId={}'
            .format(network, self.id)
        )

    # utilities
    def to_datetime(self, data):
        try:
            tz = pytz.timezone('timeZoneID')
        except pytz.UnknownTimeZoneError as e:
            logger.warn(e)
            tz = None
        timetuple = (data['date']['year'], data['date']['month'], data['date']['day'], data['hour'], data['minute'], data['second'])
        timetuple = map(int, timetuple)
        return datetime.datetime(*timetuple, tzinfo=tz)


def make_report(orders):
    fieldnames = orders[0].__dict__.keys()
    with open('report.csv', 'wb') as f:
        writer = UnicodeCSVDictWriter(f, fieldnames=fieldnames)
        writer.writerow(dict(zip(fieldnames, fieldnames)))
        for order in orders:
            data = order.__dict__.copy()
            data['totalBudget'] = data['totalBudget']['microAmount']
            writer.writerow(data)


if __name__ == '__main__':
    # auth example:
    #   https://github.com/googleads/googleads-python-lib/blob/master/examples/dfp/authentication/create_dfp_client_without_yaml.py
    oauth2_client = oauth2.GoogleRefreshTokenClient(
        client_id=env.get('CLIENT_ID'),
        client_secret=env.get('CLIENT_SECRET'),
        refresh_token=env.get('REFRESH_TOKEN'),
    )
    client = dfp.DfpClient(oauth2_client, env.get('APPLICATION_NAME'))
    networks = client.GetService('NetworkService').getAllNetworks()
    network = networks[0]['networkCode']
    client = dfp.DfpClient(oauth2_client, env.get('APPLICATION_NAME'), network)


    # https://github.com/googleads/googleads-python-lib/blob/master/examples/dfp/v201403/order_service/get_orders_by_statement.py
    inventory_service = client.GetService('OrderService', version='v201403')

    start = datetime.date.today() - datetime.timedelta(days=90)
    end = datetime.date.today()
    values = [
        {
            'key': 'start',
            'value': {
                'xsi_type': 'TextValue',
                'value': start.strftime('%Y-%m-%dT%H:%M:%S'),
            }
        },
        {
            'key': 'end',
            'value': {
                'xsi_type': 'TextValue',
                'value': end.strftime('%Y-%m-%dT%H:%M:%S'),
            }
        },
    ]
    query = 'WHERE endDateTime >= :start AND endDateTime < :end'
    statement = dfp.FilterStatement(query, values)
    response = inventory_service.getOrdersByStatement(statement.ToStatement())
    results = response['results']
    orders = [Order(x) for x in results]
