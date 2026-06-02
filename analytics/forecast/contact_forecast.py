class ContactForecast:

    @staticmethod
    def moving_average(history, periods=3):
        if len(history) < periods:
            return 0

        return sum(history[-periods:]) / periods

    @staticmethod
    def forecast_next_day(history):
        return ContactForecast.moving_average(history)

    @staticmethod
    def forecast_next_week(history):
        daily_forecast = ContactForecast.forecast_next_day(history)

        return [daily_forecast] * 7