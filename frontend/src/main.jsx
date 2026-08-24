import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import ReactMarkdown from 'react-markdown';

import {
    Sun,
    Cloud,
    CloudSun,
    CloudRain,
    CloudDrizzle,
    CloudLightning,
    CloudFog,
    Snowflake,
    MapPin,
    Send,
    Mic,
    ShieldAlert,
    Wind,
    Droplets,
    Search,
    Languages,
    Volume2,
    RefreshCw,
    Database
} from 'lucide-react';

import './style.css';


const API =
    import.meta.env.VITE_API_URL ||
    'http://localhost:8000/api/v1';

const DEFAULT_LOCATION = 'New Delhi';
const DEFAULT_QUERY = 'What is the weather in New Delhi?';


/* ------------------------------------------------------------
   SOURCE
   ------------------------------------------------------------ */

function Source({ source }) {
    return (
        <div className="source">
            <Database size={14} />

            {source?.provider || 'WeatherGPT'}

            {' · '}

            {source?.data_mode === 'demo_fallback'
                ? 'DEMO FALLBACK'
                : 'LIVE'}

            {source?.retrieved_at &&
                ` · ${new Date(
                    source.retrieved_at
                ).toLocaleTimeString()}`
            }
        </div>
    );
}


/* ------------------------------------------------------------
   WEATHER CODE → ICON + DESCRIPTION
   Open-Meteo / WMO codes
   ------------------------------------------------------------ */

function getWeatherInfo(code) {
    if (code === 0) {
        return { text: 'Clear sky', icon: Sun };
    }

    if (code === 1) {
        return { text: 'Mainly clear', icon: Sun };
    }

    if (code === 2) {
        return { text: 'Partly cloudy', icon: CloudSun };
    }

    if (code === 3) {
        return { text: 'Overcast', icon: Cloud };
    }

    if (code === 45 || code === 48) {
        return { text: 'Fog', icon: CloudFog };
    }

    if (code >= 51 && code <= 57) {
        return { text: 'Drizzle', icon: CloudDrizzle };
    }

    if (code >= 61 && code <= 67) {
        return { text: 'Rain', icon: CloudRain };
    }

    if (code >= 71 && code <= 77) {
        return { text: 'Snow', icon: Snowflake };
    }

    if (code >= 80 && code <= 82) {
        return { text: 'Rain showers', icon: CloudRain };
    }

    if (code >= 85 && code <= 86) {
        return { text: 'Snow showers', icon: Snowflake };
    }

    if (code >= 95 && code <= 99) {
        return { text: 'Thunderstorm', icon: CloudLightning };
    }

    return { text: 'Unknown', icon: Cloud };
}


/* ------------------------------------------------------------
   CURRENT WEATHER TEXT → ICON
   OpenWeather condition
   ------------------------------------------------------------ */

function getCurrentWeatherInfo(condition = '') {
    const text = condition.toLowerCase();

    if (text.includes('thunder')) {
        return { icon: CloudLightning };
    }

    if (text.includes('rain') || text.includes('shower')) {
        return { icon: CloudRain };
    }

    if (text.includes('drizzle')) {
        return { icon: CloudDrizzle };
    }

    if (text.includes('snow') || text.includes('sleet')) {
        return { icon: Snowflake };
    }

    if (text.includes('fog') || text.includes('mist')) {
        return { icon: CloudFog };
    }

    if (text.includes('clear') || text.includes('sun')) {
        return { icon: Sun };
    }

    if (text.includes('cloud') || text.includes('overcast')) {
        return { icon: CloudSun };
    }

    return { icon: Cloud };
}


/* ============================================================
   APP
   ============================================================ */

function App() {

    const [place, setPlace] = useState(DEFAULT_LOCATION);

    const [query, setQuery] = useState(
        DEFAULT_QUERY
    );

    const [current, setCurrent] = useState(null);

    const [forecast, setForecast] = useState(null);

    const [busy, setBusy] = useState(false);

    const [chat, setChat] = useState([
        {
            who: 'bot',
            text:
                'Namaste! Ask about current weather, a forecast, rain alerts, or climate trends. I only report verified provider data.'
        }
    ]);


    /* ------------------------------------------------------------
       LOAD WEATHER
       ------------------------------------------------------------ */

    const load = async (location = place) => {
        if (!location.trim()) return;

        setBusy(true);

        try {
            const [currentResponse, forecastResponse] =
                await Promise.all([
                    fetch(
                        `${API}/weather/current?location=${encodeURIComponent(
                            location
                        )}`
                    ),
                    fetch(
                        `${API}/weather/forecast?location=${encodeURIComponent(
                            location
                        )}`
                    )
                ]);

            if (!currentResponse.ok) {
                throw new Error('Location not found');
            }

            if (!forecastResponse.ok) {
                throw new Error('Forecast unavailable');
            }

            const currentData =
                await currentResponse.json();

            const forecastData =
                await forecastResponse.json();

            if (currentData.error) {
                throw new Error(currentData.error);
            }

            if (forecastData.error) {
                throw new Error(forecastData.error);
            }

            setCurrent(currentData);
            setForecast(forecastData);

        } catch (error) {
            setChat(messages => [
                ...messages,
                {
                    who: 'bot',
                    text:
                        `Unable to retrieve data: ${error.message}. Check the API connection or try another location.`
                }
            ]);
        } finally {
            setBusy(false);
        }
    };


    /* ------------------------------------------------------------
       INITIAL LOAD
       ------------------------------------------------------------ */

    useEffect(() => {
        load('New Delhi');
    }, []);


    /* ------------------------------------------------------------
       CHAT
       ------------------------------------------------------------ */

    const send = async () => {
        if (!query.trim() || busy) return;

        const question = query;

        setChat(messages => [
            ...messages,
            {
                who: 'me',
                text: question
            }
        ]);

        setQuery('');
        setBusy(true);

        try {
            const response = await fetch(
                `${API}/chat`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: question,
                        location: place
                    })
                }
            );

            if (!response.ok) {
                throw new Error('Could not answer');
            }

            const data = await response.json();

            setChat(messages => [
                ...messages,
                {
                    who: 'bot',
                    text: data.answer,
                    source: data.source
                }
            ]);

        } catch (error) {
            setChat(messages => [
                ...messages,
                {
                    who: 'bot',
                    text: error.message
                }
            ]);
        } finally {
            setBusy(false);
        }
    };


    /* ------------------------------------------------------------
       CURRENT WEATHER
       ------------------------------------------------------------ */

    const locationName =
        current?.location?.name || place;

    const currentWeather =
        current?.weather?.current || {};

    const temperature =
        currentWeather.temperature_2m;

    const humidity =
        currentWeather.relative_humidity_2m;

    const wind =
        currentWeather.wind_speed_10m;

    const feelsLike =
        currentWeather.apparent_temperature;

    const condition =
        currentWeather.condition || 'Unknown';


    const currentInfo = currentWeather.weather_code != null
        ? getWeatherInfo(currentWeather.weather_code)
        : getCurrentWeatherInfo(condition);

    const CurrentIcon = currentInfo.icon;


    /* ------------------------------------------------------------
       FORECAST
       ------------------------------------------------------------ */

    const daily =
        forecast?.forecast?.daily || {};

    const forecastDays =
        daily.time || [];


    /* ------------------------------------------------------------
       ALERTS
       ------------------------------------------------------------ */

    const alerts =
        forecast?.alerts || [];


    /* ============================================================
       RENDER
       ============================================================ */

    return (
        <main>

            {/* NAVIGATION */}

            <nav>

                <div className="brand">

                    <span>
                        <CloudSun />
                    </span>

                    <div>
                        WeatherGPT

                        <small>
                            INDIA · DISASTER INTELLIGENCE
                        </small>
                    </div>

                </div>


                <div className="navright">

                    <button className="ghost">
                        <Languages size={16} />
                        EN / हिन्दी
                    </button>

                    <button className="ghost">
                        <Volume2 size={16} />
                        Voice
                    </button>

                    <div className="live">
                        <i />
                        LIVE DATA
                    </div>

                </div>

            </nav>


            {/* HERO */}

            <section className="hero">

                <div>

                    <p className="eyebrow">
                        SIH 2026 · PROBLEM 26068
                    </p>

                    <h1>
                        Weather intelligence
                        <br />
                        <em>
                            when every minute matters.
                        </em>
                    </h1>

                    <p className="sub">
                        Conversational forecasts, hazard-aware
                        advisories, and transparent live sources
                        for operational teams across India.
                    </p>

                </div>


                <div className="search">

                    <Search size={19} />

                    <input
                        value={place}
                        onFocus={() => {
                            if (place === DEFAULT_LOCATION) {
                                setPlace('');
                            }
                        }}
                        onChange={event =>
                            setPlace(event.target.value)
                        }
                        onKeyDown={event => {
                            if (event.key === 'Enter') {
                                load();
                            }
                        }}
                        placeholder="Search a city or district"
                    />

                    <button
                        onClick={() => load()}
                        disabled={busy}
                    >
                        <RefreshCw
                            size={17}
                            className={
                                busy ? 'spin' : ''
                            }
                        />

                        Update
                    </button>

                </div>

            </section>


            {/* CURRENT WEATHER + MAP */}

            <section className="grid overview">

                <article className="current card">

                    <div className="cardtop">

                        <span>
                            NOW · {locationName}
                        </span>

                        <MapPin size={17} />

                    </div>


                    <div className="temp">

                        <CurrentIcon size={62} />

                        <strong>
                            {temperature ?? '—'}
                            <sup>°C</sup>
                        </strong>

                    </div>


                    <p>
                        {condition !== 'Unknown'
                            ? condition.charAt(0).toUpperCase() + condition.slice(1)
                            : currentInfo.text}
                        {' · '}
                        Feels like {feelsLike ?? '—'}°
                    </p>


                    <div className="metrics">

                        <span>
                            <Droplets />
                            Humidity

                            <b>
                                {humidity ?? '—'}%
                            </b>
                        </span>


                        <span>
                            <Wind />
                            Wind

                            <b>
                                {wind ?? '—'} m/s
                            </b>
                        </span>

                    </div>


                    <Source source={current?.source} />

                </article>


                <article className="map card">

                    <div className="cardtop">

                        <span>
                            OPERATIONAL MAP
                        </span>

                        <span className="mapkey">
                            Weather overlay
                        </span>

                    </div>


                    <div className="mapvisual">

                        <div className="mapdots">
                            •
                            <br />
                            　　•
                            <br />
                                　　　　•
                            <br />
                            　•
                        </div>


                        <div className="pin">

                            ●

                            <small>
                                {locationName}
                            </small>

                        </div>


                        <div className="rings" />

                    </div>


                    <p className="caption">
                        Location intelligence · Provider-ready map layer
                    </p>

                </article>

            </section>


            {/* FORECAST + ALERTS */}

            <section className="grid lower">

                <article className="forecast card">

                    <div className="sectiontitle">

                        <div>

                            <p className="eyebrow">
                                OUTLOOK
                            </p>

                            <h2>
                                7-day forecast
                            </h2>

                        </div>

                        <span>
                            Provider forecast
                        </span>

                    </div>


                    <div className="days">

                        {forecastDays.map((date, index) => {

                            const info =
                                getWeatherInfo(
                                    daily.weather_code?.[index]
                                );

                            const ForecastIcon =
                                info.icon;

                            const max =
                                daily.temperature_2m_max?.[
                                    index
                                ];

                            const min =
                                daily.temperature_2m_min?.[
                                    index
                                ];

                            const rain =
                                daily
                                    .precipitation_probability_max?.[
                                    index
                                ];

                            const dayName =
                                index === 0
                                    ? 'Today'
                                    : new Date(
                                        `${date}T00:00`
                                    ).toLocaleDateString(
                                        undefined,
                                        {
                                            weekday: 'short'
                                        }
                                    );

                            return (
                                <div
                                    className="day"
                                    key={date}
                                >

                                    <b>
                                        {dayName}
                                    </b>

                                    <ForecastIcon />

                                    <span>
                                        {info.text}
                                    </span>

                                    <strong>
                                        {max ?? '—'}°

                                        {' '}

                                        <small>
                                            {min ?? '—'}°
                                        </small>
                                    </strong>

                                    <i>
                                        {rain ?? 0}% rain
                                    </i>

                                </div>
                            );

                        })}

                    </div>


                    {!forecastDays.length && (
                        <p
                            style={{
                                color: '#8daab0',
                                fontSize: '12px'
                            }}
                        >
                            No forecast data available.
                        </p>
                    )}


                    <Source source={forecast?.source} />

                </article>


                <article className="alerts card">

                    <div className="sectiontitle">

                        <div>

                            <p className="eyebrow">
                                RISK MONITOR
                            </p>

                            <h2>
                                Advisories
                            </h2>

                        </div>

                        <ShieldAlert />

                    </div>


                    {alerts.length > 0 ? (

                        alerts.map((alert, index) => (

                            <div
                                className={`alert ${
                                    alert.severity || 'info'
                                }`}
                                key={index}
                            >

                                <ShieldAlert size={18} />

                                <div>

                                    <b>
                                        {alert.title}
                                    </b>

                                    <p>
                                        {alert.body}
                                    </p>

                                </div>

                            </div>

                        ))

                    ) : (

                        <div className="alert info">

                            <ShieldAlert size={18} />

                            <div>

                                <b>
                                    No active advisories
                                </b>

                                <p>
                                    No weather alerts are currently
                                    available from the configured provider.
                                </p>

                            </div>

                        </div>

                    )}


                    <p className="official">
                        Operational decisions must be verified
                        against official IMD bulletins.
                    </p>

                </article>

            </section>


            {/* CHAT */}

            <section className="chat card">

                <div className="chathead">

                    <div>

                        <p className="eyebrow">
                            WEATHER ASSISTANT
                        </p>

                        <h2>
                            Ask WeatherGPT
                        </h2>

                    </div>

                    <span>
                        <i />
                        Tool-backed responses
                    </span>

                </div>


                <div className="messages">

                    {chat.map(
                        (message, index) => (

                            <div
                                className={message.who}
                                key={index}
                            >

                                <ReactMarkdown>
                                    {message.text}
                                </ReactMarkdown>

                                {message.source && (
                                    <Source source={message.source} />
                                )}

                            </div>

                        )
                    )}

                </div>


                <div className="composer">

                    <button
                        aria-label="voice"
                        type="button"
                    >
                        <Mic />
                    </button>


                    <input
                        value={query}
                        onFocus={() => {
                            if (query === DEFAULT_QUERY) {
                                setQuery('');
                            }
                        }}
                        onChange={event =>
                            setQuery(event.target.value)
                        }
                        onKeyDown={event => {
                            if (event.key === 'Enter') {
                                send();
                            }
                        }}
                        placeholder="Ask about weather, floods, alerts, climate…"
                    />


                    <button
                        className="send"
                        onClick={send}
                        disabled={busy}
                    >
                        <Send size={18} />
                        Ask
                    </button>

                </div>


                <div className="chips">

                    {[
                        'Will it rain tomorrow?',
                        'Any severe weather alerts?',
                        'Show climate trend'
                    ].map(text => (

                        <button
                            key={text}
                            onClick={() => setQuery(text)}
                        >
                            {text}
                        </button>

                    ))}

                </div>

            </section>


            {/* FOOTER */}

            <footer>
                WEATHERGPT · Data is transparently attributed ·
                OpenWeather adapter active · Open-Meteo forecast ·
                IMD integration ready
            </footer>

        </main>
    );
}


createRoot(
    document.getElementById('root')
).render(
    <App />
);
