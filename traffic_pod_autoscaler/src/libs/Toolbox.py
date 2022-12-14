from datetime import datetime, timezone, timedelta


class Toolbox(object):

    def get_date_now_utc(self):
        _now_UTC = datetime.now(timezone.utc)
        return _now_UTC

    def get_date_utc_from_string(self, _str):
        _date_UTC = datetime.fromisoformat(_str)
        return _date_UTC

    def get_date_timedelta_minutes(self, _minutes):
        _timedelta = timedelta(minutes=_minutes)
        return _timedelta

    def get_date_timedelta_seconds(self, _seconds):
        _timedelta = timedelta(seconds=_seconds)
        return _timedelta

    def get_date_age(self, _date):
        _now_UTC = self.get_date_now_utc()
        _diff = _now_UTC - _date
        return _diff


_toolbox = Toolbox()
