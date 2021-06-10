from dateutil.relativedelta import relativedelta


class Formatters:

    @staticmethod
    def split_account_number(account_number='', chunk_size=4):
        chunks = len(account_number)
        array = [account_number[i:i+chunk_size]
                 for i in range(0, chunks, chunk_size)]
        return '-'.join(array)

    @staticmethod
    def mandate_spread_by_month(months=1, date=None):
        if months <= 0:
            raise Exception('months must be more than 0')
        if date is None:
            raise Exception('date is required!')

        __dates__ = [

            [date + relativedelta(months=+__calendar__)
             for __calendar__ in range(1, months+1)]
        ]
        return __dates__
