"""
Weather API Client - Program 2
SkillsUSA State 2026
"""

import argparse
import html
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timezone

# User agent string for API requests
USER_AGENT = "SkillsUSA WeatherForecast/1.0"


def fetch_json(url):
    """
    Fetch and parse JSON data from a URL with error handling.
    
    Returns:
        dict: Parsed JSON data from the response.
        .
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json,application/json,text/plain;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise urllib.error.HTTPError(url, response.status, response.reason, response.headers, None)
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error for {url}: {e.code}")
        raise
    except urllib.error.URLError as e:
        print(f"Network Error: {e.reason}")
        raise


def get_zip_info(zip_code):
    """
    Retrieve location information for a given US ZIP code.
    
    Args:
        zip_code (str): The ZIP code to look up. Must be a valid US ZIP code.
    
    Returns:
        dict: Dictionary containing:
            - zip: The ZIP code
            - city: City name
            - state: State abbreviation
            - latitude: Latitude coordinate
            - longitude: Longitude coordinate
            - country: Country abbreviation
            
    Raises:
        ValueError: If the ZIP code cannot be found or no places are returned.
        Exception: If the API request fails.
    """
    url = f"https://api.zippopotam.us/us/{urllib.parse.quote(str(zip_code))}"
    try:
        data = fetch_json(url)
    except Exception:
        raise ValueError(f"Invalid ZIP code: {zip_code}")

    if not data.get("places"):
        raise ValueError(f"No location found for ZIP: {zip_code}")

    place = data["places"][0]
    return {
        "zip": data.get("post code", zip_code),
        "city": place.get("place name", "Unknown"),
        "state": place.get("state abbreviation", place.get("state", "Unknown")),
        "latitude": float(place.get("latitude", 0)),
        "longitude": float(place.get("longitude", 0)),
        "country": data.get("country abbreviation", data.get("country", "US")),
    }


def get_weather_points(lat, lon):
    """Gets weather API endpoints"""
    url = f"https://api.weather.gov/points/{lat},{lon}"
    return fetch_json(url)


def get_forecast(url):
    """Gets forecast data"""
    return fetch_json(url)


def build_html_report(location, points_data, forecast_data, hourly_data, output_path):
    """Generates HTML weather report"""
    location_html = f"{html.escape(location['city'])}, {html.escape(location['state'])} ({html.escape(location['country'])})"
    point_properties = points_data.get("properties", {})
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    def render_period(period):
        """Renders a single forecast period as an HTML card."""

        icon_url = html.escape(period.get("icon", ""))
        name = html.escape(period.get("name", ""))
        temp = html.escape(str(period.get("temperature", "")))
        unit = html.escape(str(period.get("temperatureUnit", "")))
        short = html.escape(period.get("shortForecast", ""))
        detailed = html.escape(period.get("detailedForecast", ""))
        return f"""
        <div class="forecast-card">
            <div class="forecast-title">{name}</div>
            {f'<img class="forecast-icon" src="{icon_url}" alt="{short}" />' if icon_url else ''}
            <div class="forecast-temp">{temp}°{unit}</div>
            <div class="forecast-short">{short}</div>
            <div class="forecast-detail">{detailed}</div>
        </div>
        """

    daily_periods = forecast_data.get("properties", {}).get("periods", [])
    daily_sections = "".join(render_period(p) for p in daily_periods)

    hourly_periods = hourly_data.get("properties", {}).get("periods", [])[:18]
    hourly_sections = "".join(render_period(p) for p in hourly_periods)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather Report for {html.escape(location['zip'])}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f0f8ff; }}
        header {{ background: #0066cc; color: white; padding: 20px; text-align: center; }}
        .container {{ max-width: 1200px; margin: 20px auto; padding: 0 20px; }}
        .summary, .section {{ background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 20px; }}
        .section h2 {{ color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }}
        .row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }}
        .forecast-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; background: #f9f9f9; }}
        .forecast-icon {{ width: 80px; height: auto; display: block; margin: 0 auto 10px; }}
        .forecast-title {{ font-weight: bold; margin-bottom: 8px; }}
        .forecast-temp {{ font-size: 1.3em; color: #0066cc; margin: 8px 0; }}
        .forecast-short {{ font-weight: 500; margin-bottom: 8px; }}
        .forecast-detail {{ font-size: 0.9em; line-height: 1.4; }}
        table {{ width: 100%; border-collapse: collapse; }}
        td, th {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f0f0f0; }}
        .footer {{ text-align: center; color: #666; padding: 20px; }}
    </style>
</head>
<body>
    <header>
        <h1>Weather Forecast</h1>
        <p>{location_html}</p>
        <p>{html.escape(location['zip'])} • Lat {location['latitude']:.4f}, Lon {location['longitude']:.4f}</p>
    </header>
    <div class="container">
        <section class="summary">
            <h2>Location Information</h2>
            <table>
                <tr><th>ZIP Code</th><td>{html.escape(location['zip'])}</td></tr>
                <tr><th>City</th><td>{html.escape(location['city'])}</td></tr>
                <tr><th>State</th><td>{html.escape(location['state'])}</td></tr>
                <tr><th>Latitude</th><td>{location['latitude']:.4f}</td></tr>
                <tr><th>Longitude</th><td>{location['longitude']:.4f}</td></tr>
                <tr><th>Generated</th><td>{generated}</td></tr>
            </table>
        </section>

        <section class="section">
            <h2>7-Day Forecast</h2>
            <div class="row">{daily_sections}</div>
        </section>

        <section class="section">
            <h2>Hourly Forecast (Next 18 Hours)</h2>
            <div class="row">{hourly_sections}</div>
        </section>

        <section class="section">
            <h2>API Information</h2>
            <p>Weather data from api.weather.gov</p>
            <p>Location data from zippopotam.us</p>
        </section>
    </div>
    <div class="footer">
        <p>Generated by SkillsUSA Weather Client</p>
    </div>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Weather forecast by ZIP code")
    parser.add_argument("zip", help="US ZIP code")
    parser.add_argument("--output", "-o", default="weather_report.html", help="Output file")
    parser.add_argument("--open", action="store_true", help="Open in browser")
    return parser.parse_args()


def main():
    """Main program"""
    args = parse_args()

    try:
        location = get_zip_info(args.zip)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Location:")
    print(f"  City:  {location['city']}")
    print(f"  State: {location['state']}")
    print(f"  Lat:   {location['latitude']:.4f}")
    print(f"  Lon:   {location['longitude']:.4f}")
    print()

    try:
        print("Getting weather data...")
        points_data = get_weather_points(location["latitude"], location["longitude"])
        properties = points_data.get("properties", {})
        forecast_url = properties.get("forecast")
        hourly_url = properties.get("forecastHourly")

        if not forecast_url or not hourly_url:
            raise ValueError("Weather API unavailable")

        forecast_data = get_forecast(forecast_url)
        hourly_data = get_forecast(hourly_url)
        print("Weather data retrieved successfully")
    except Exception as e:
        print(f"Error getting weather: {e}")
        sys.exit(1)

    try:
        output_path = args.output
        build_html_report(location, points_data, forecast_data, hourly_data, output_path)
        print(f"Report saved to: {output_path}")

        if args.open:
            webbrowser.open_new_tab(output_path)
            print("Opened in browser")
    except Exception as e:
        print(f"Error creating report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()