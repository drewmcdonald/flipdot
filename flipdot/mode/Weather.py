import os
from typing import ClassVar

import pendulum
import requests
from pydantic import AwareDatetime, BaseModel, PrivateAttr

from flipdot.DotMatrix import DotMatrix
from flipdot.mode.BaseDisplayMode import BaseDisplayMode, DisplayModeOptions
from flipdot.text import string_to_dots

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


class WeatherOptions(DisplayModeOptions):
    font: str = "cg_pixel_4x5"
    """The font to use for the text."""
    lat: float = 38.9034
    """The latitude of the weather location."""
    lon: float = -76.9882
    """The longitude of the weather location."""


class Weather(BaseDisplayMode):
    """A display mode that shows the current weather."""

    mode_name: ClassVar[str] = "weather"
    Options: ClassVar[type[DisplayModeOptions]] = WeatherOptions

    tick_interval = 1

    _last_dt: pendulum.DateTime | None = PrivateAttr(default=None)

    opts: WeatherOptions = WeatherOptions()

    def get_current_weather(self) -> CurrentWeatherData:
        url = (
            f"{BASE_URL}lat={self.opts.lat}&lon={self.opts.lon}"
            f"&appid={API_KEY}&{api_settings}&{api_units}"
        )
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"Failed to get weather data: {response.text}")

        return CurrentWeatherData(**response.json()['current'])

    def should_render(self) -> bool:
        if not self._last_dt:
            return True
        return (pendulum.now() - self._last_dt).minutes >= 10

    def get_frame(self, frame_idx: int) -> DotMatrix:
        weather = self.get_current_weather()
        self._last_dt = pendulum.now()

        data = f"{weather.temp:.1f}"
        return self.layout.center_middle(string_to_dots(data, self.opts.font))
