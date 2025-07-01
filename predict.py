from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import pandas as pd
from prophet import Prophet
from utils import get_engine

app = FastAPI()

# 📌 요청 스키마
class ForecastRequest(BaseModel):
    periods: int = 30   # 예측할 일수
    freq: Optional[str] = "D"  # 예: 일간(D), 월간(M)

@app.post("/forecast")
def forecast(request: ForecastRequest):
    # 1) DB 연결
    engine = get_engine()

    # 2) 데이터 불러오기
    query = """
    SELECT Date AS ds, Qty AS y
    FROM your_sales_table
    ORDER BY Date
    """
    df = pd.read_sql(query, engine)

    # 3) 전처리
    df['ds'] = pd.to_datetime(df['ds'])
    df['y'] = df['y'].fillna(0)


    # 4) Prophet 모델 학습
    model = Prophet()
    model.fit(df)

    # 5) 미래 데이터프레임 생성 + 예측
    future = model.make_future_dataframe(periods=request.periods, freq=request.freq)
    forecast = model.predict(future)

    # 6) 예측값 JSON 응답
    result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(request.periods)

    return result.to_dict(orient="records")
