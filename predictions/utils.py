import pmdarima as pm
import pandas as pd
from .models import SalesData

def get_sales_data():
    # Query sales data from the database
    data = SalesData.objects.all().order_by('date')
    df = pd.DataFrame(list(data.values('date', 'sales')))
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df['sales']

def fit_auto_arima_model():
    # Get sales data as a Pandas Series
    sales_data = get_sales_data()
    # Fit the Auto ARIMA model
    model = pm.auto_arima(sales_data, seasonal=True, m=12, stepwise=True, trace=True)
    # Output the model summary
    print(model.summary())
    return model
