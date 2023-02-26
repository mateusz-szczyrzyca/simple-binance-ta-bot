## What's this

***This is fully private project and it's not completed yet - do not use it for trading ***.

This is a very simple binance trading bot which uses pandas-ta set of technical indicators from 
pandas-ta lib.

Bot automatically builds up it's on OHLCV data for models in SQLite database while it's working.

You can easily plug your strategy (instruction will be provided when it's ready)

## OHLCV data for free

You can download archive OHLCV data from Binance for free using this 
bot either for technical indicators usage by bot or just for your own needs.

I'm not sure if it's applicable to already delisted coins, but definitely 
works for coins that are currently listed on Binance.

Set `BOT_PYTHON_DATABASE_UPDATE_START_RECORD` to define epoch start point time 
in the past.

For example, default timestamp value `1640995200000` which is `1st January 2022 00:00:00` and
bot will try to start fetch ohlcv data from this date up to today. Data granulation is 
`1 minute` and bot fetches `720 minutes (12h)` per single request and then wait `BOT_PYTHON_DATABASE_UPDATE_DELAY_SECS` time 
before the next request (Binance has API limits hence you should not try to download as fast as possible as they may block you)

Records which already exist in db just simply won't be added based on db schema and this is 
handled by SQLite itself this there is no additional logic for that.

&nbsp;

If you just want to use OHLCV for your own needs and tests, then you can use `read_sql_query()` 
function from pandas as follow:

```python
df = pd.DataFrame()
con = sqlite3.connect('btcusdt.db')
df = pd.read_sql_query("SELECT * from main.ohlcv_data ORDER BY open_time ASC", con)
```

And in `df` dataframe you now have fetched OHLCV data for you own experiments, see instruction 
here: https://github.com/twopirllc/pandas-ta

