import os
from typing import ClassVar

import pendulum
import requests
from pydantic import AwareDatetime, BaseModel, PrivateAttr

from flipdot.display_mode.BaseDisplayMode import BaseDisplayMode
from flipdot.text import string_to_dots
from flipdot.types import DotMatrix

BASE_URL = "https://api.openweathermap.org/data/3.0/onecall?"
API_KEY = os.getenv("OPENWEATHER_API_KEY")

api_settings = 'exclude=alerts,daily,hourly,minutely'
api_units = 'units=imperial'


class CurrentWeatherData(BaseModel):
    class Config:
        extra = "ignore"

    dt: AwareDatetime
    sunrise: AwareDatetime
    sunset: AwareDatetime
    temp: float
    feels_like: float
    pressure: int
    humidity: int


class Weather(BaseDisplayMode):
    """A display mode that shows the current weather."""

    mode_name: ClassVar[str] = "weather"

    tick_interval = 1

    _last_dt: pendulum.DateTime | None = PrivateAttr(default=None)

    class Options(BaseDisplayMode.Options):
        font: str = "cg_pixel_4x5"
        """The font to use for the text."""
        lat: float = 37.7749
        """The latitude of the weather location."""
        lon: float = -122.4194
        """The longitude of the weather location."""

    opts: Options

    def get_current_weather(self) -> CurrentWeatherData:
        url = (
            f"{BASE_URL}lat={self.opts.lat}&lon={self.opts.lon}"
            "&appid={API_KEY}&{api_settings}&{api_units}"
        )
        response = requests.get(url)
        return CurrentWeatherData(**response.json()['current'])

    def should_render(self) -> bool:
        if not self._last_dt:
            return True
        return (pendulum.now() - self._last_dt).minutes >= 10

    def get_frame(self, frame_idx: int) -> DotMatrix:
        weather = self.get_current_weather()
        self._last_dt = pendulum.now()

        data = f"{weather.temp:.1f}F"
        return self.layout.center_middle(string_to_dots(data, self.opts.font))
