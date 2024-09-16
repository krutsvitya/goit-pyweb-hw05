import aiohttp
import asyncio
import sys
from datetime import datetime, timedelta


class Fetcher:

    API_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'

    def __init__(self, days: int):
        if not (1 <= days <= 10):
            raise ValueError("Кількість днів повинна бути між 1 і 10")
        self.days = days

    async def fetch_rates(self, date: str):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.API_URL.format(date=date)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Не вдалося отримати дані на {date}. Статус: {response.status}")
            except Exception as e:
                print(f"Помилка при отриманні даних: {e}")

    async def get_rates_for_last_days(self):
        tasks = []
        today = datetime.now()

        for i in range(self.days):
            day = today - timedelta(days=i + 1)
            formatted_date = day.strftime('%d.%m.%Y')
            tasks.append(self.fetch_rates(formatted_date))

        results = await asyncio.gather(*tasks)
        return results


class Formatter:

    @staticmethod
    def format_data(data, currencies):
        formatted_data = []
        for day_data in data:
            if day_data is None:
                continue

            date = day_data['date']
            exchange_rates = day_data.get('exchangeRate', [])

            daily_rates = {date: {}}
            for rate in exchange_rates:
                if rate['currency'] in currencies:
                    daily_rates[date][rate['currency']] = {
                        'sale': rate.get('saleRate', rate['saleRateNB']),
                        'purchase': rate.get('purchaseRate', rate['purchaseRateNB']),
                    }
            if daily_rates[date]:
                formatted_data.append(daily_rates)

        return formatted_data


class Main:

    def __init__(self, days: int):
        self.days = days

    async def run(self):
        fetcher = Fetcher(self.days)
        formatter = Formatter()

        raw_data = await fetcher.get_rates_for_last_days()
        formatted_data = formatter.format_data(raw_data, ['EUR', 'USD'])
        print(formatted_data)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    days = int(sys.argv[1])

    if days < 1 or days > 10:
        sys.exit(1)

    asyncio.run(Main(days).run())
