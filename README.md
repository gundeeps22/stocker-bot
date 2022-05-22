# stocker-bot
This bot stalks the investments made by Berskhire Hathaway

## Setup

Before running the code please follow the steps below. This assumes that `pip`, `python > 3.6` have been installed.

1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`


## Organization

### `src/data_retrieval`
This folder contains a set of business functions to retrieve data from the `Edgar` system.

**Important Business Functions**:
- `retrieve_investment_data` - given a cik number, this returns the stock data associated with the provided cik number.

